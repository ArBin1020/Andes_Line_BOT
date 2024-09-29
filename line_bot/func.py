from database import *
import json
from linebot.v3.messaging import ApiClient, MessagingApi
from linebot.v3.messaging.models.flex_message import FlexMessage
from linebot.v3.messaging.models.flex_container import FlexContainer
from linebot.v3.webhooks import PostbackEvent
from datetime import datetime

class LineBotSQL:
    check_user_membership_sql = """
        SELECT is_member FROM {table}
        WHERE line_user_id = %(line_user_id)s
    """.format(table=LineUser.__tablename__)

    add_user_sql = """
        INSERT INTO {table} (line_user_id, is_member)
        VALUES (%(line_user_id)s, %(is_member)s)
    """.format(table=LineUser.__tablename__)

    update_user_connection_sql = """
        UPDATE {table}
        SET is_member = %(is_member)s, patient_id = %(patient_id)s
        WHERE line_user_id = %(line_user_id)s
    """.format(table=LineUser.__tablename__)

    get_national_id_sql = """
        SELECT national_id FROM {table}
        WHERE national_id = %(national_id)s
    """.format(table=UserData.__tablename__)

    update_tmp_reservation_info_sql = """
        UPDATE {table}
        SET tmp_reservation_info = %(tmp_reservation_info)s
        WHERE line_user_id = %(line_user_id)s
    """.format(table=LineUser.__tablename__)

    get_id_and_name_sql = """
        SELECT national_id, name FROM {table}
        JOIN {table2}
        ON {table}.national_id = {table2}.patient_id
        WHERE line_user_id = %(line_user_id)s
    """.format(table=UserData.__tablename__, table2=LineUser.__tablename__)

    fetch_tmp_reservation_info_sql = """
        SELECT tmp_reservation_info FROM {table}
        WHERE line_user_id = %(line_user_id)s
    """.format(table=LineUser.__tablename__)
    
    confirm_reservation_sql = """
        INSERT INTO {table} (patient_id, doctor_name, reservation_type, reservation_date, reservation_number)
        VALUES (%(patient_id)s, %(doctor_name)s, %(reservation_type)s, %(reservation_date)s, %(reservation_number)s)
    """.format(table=Reservation.__tablename__)

    examine_reservation_sql =  """
        SELECT * FROM {reservation_table} r
        JOIN {line_user_table} l ON r.patient_id = l.patient_id
        WHERE l.line_user_id = %(line_user_id)s AND r.is_cancelled = 0 
    """.format(reservation_table=Reservation.__tablename__, line_user_table=LineUser.__tablename__)

    cancel_reservation_sql = """
        UPDATE {table}
        SET is_cancelled = 1
        WHERE id = %(reservation_id)s
    """.format(table=Reservation.__tablename__)

    count_reservation_sql = """
        SELECT COUNT(*) FROM {table}
        WHERE reservation_date = %(reservation_date)s
    """.format(table=Reservation.__tablename__)
class Helper:
    local_table = {'A':1,'B':0,'C':9,'D':8,'E':7,'F':6,'G':5,'H':4,'I':9,
                    'J':3,'K':2,'L':2,'M':1,'N':0,'O':8,'P':9,'Q':8,'R':7,
                    'S':6,'T':5,'U':4,'V':3,'W':1,'X':3,'Y':2,'Z':0}
    @staticmethod
    def validate_national_id(id_number):
        sex = int(id_number[1])
        if len(id_number)!=10 or sex!=1 and sex!=2:
            return False
        check_num = Helper.local_table[id_number[0]]
        for i in range(1, 9):
            check_num = check_num + int(id_number[i])*(9-i)
        check_num = check_num + int(id_number[9])

        if check_num%10 == 0:
            return True
        else:
            return False
    
    @staticmethod
    def insert_new_user(event):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.add_user_sql
            args = {'line_user_id': event.source.user_id, 'is_member': False}
            cursor.execute(sql, args)

    @staticmethod
    def get_user_status(event):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.check_user_membership_sql
            args = {'line_user_id': event.source.user_id}
            cursor.execute(sql, args)
            examine_result = cursor.fetchone()
        return examine_result
    
    @staticmethod
    def register(api, event):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.get_national_id_sql
            args = {'national_id': event.message.text}
            cursor.execute(sql, args)
            patient_id = cursor.fetchone()

        if not patient_id or not Helper.validate_national_id(event.message.text):
            return "身分證字號錯誤或查無此人，請重新輸入\n" \
                   "若為第一次使用，請輸入病患家屬的身分證字號，以進行連動"

        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.update_user_connection_sql
            args = {'line_user_id': event.source.user_id, 'is_member': True, 'patient_id': patient_id['national_id']}
            cursor.execute(sql, args)
        return "連動成功"

    def update_confirm_json(data, doctor_name, reservation_type, reservation_time, name, patient_id):
        def replace_text(contents, replacements):
            for item in contents:
                if 'contents' in item:
                    replace_text(item['contents'], replacements)
                elif 'text' in item and item['text'] in replacements:
                    item['text'] = replacements[item['text']]

        replacements = {
            '暫存1': doctor_name,
            '暫存2': reservation_type,
            '暫存3': reservation_time,
            '暫存4': name,
            '暫存5': patient_id
        }
        
        if 'body' in data and 'contents' in data['body']:
            replace_text(data['body']['contents'], replacements)
        
        return data
        
    def count_reservation_number(date):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.count_reservation_sql
            args = {'reservation_date': date}
            cursor.execute(sql, args)
            res = cursor.fetchone()
        return res['COUNT(*)'] + 1

    def examine_reservation(event, date):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.examine_reservation_sql
            sql = sql + "AND r.reservation_date = %(reservation_date)s"
            args = {'line_user_id': event.source.user_id, 'reservation_date': date}
            cursor.execute(sql, args)
            res = cursor.fetchone()
        return res
    
class Command:
    query_mapping = {
        "內科部與內科系統相關問題": "query_Internal.json",
        "外科部與外科系統相關問題": "query_Surgery.json",
        "婦兒科系相關問題": "query_Obstetrics.json",
        "癌症中心或癌症相關問題": "query_Cancer.json",
    }
    
    doctor_mapping = {
        "內科部與內科系統": "dcotor_Internal.json",
        "外科部與外科系統": "dcotor_Surgery.json",
        "婦兒科系": "dcotor_Obstetrics.json",
        "癌症中心或癌症相關": "dcotor_Cancer.json"
    }

    time_mapping = {}


    @staticmethod
    def faq(api, event):
        return "1. 第一次使用請輸入病患家屬的身分證字號，以進行連動\n" \
               "2. 若已經連動成功，請點選下方「預約」功能\n" \
               "3. 若有任何問題，您可以透過使用「AI問答」按鈕來進行提問"

    def create_reservation(api, event):
        with open('line_bot/reply_info/reservation.json') as f:
            data = json.load(f)
        message = FlexMessage(alt_text="預約資訊", contents=FlexContainer.from_dict(data))
        return message
    
    def display_doctor_selection(api, event):
        msg = event.message.text[5:]
        # find the corresponding json file
        file_name = Command.doctor_mapping[msg]
        with open('line_bot/reply_info/'+file_name) as f:
            data = json.load(f)
        message = FlexMessage(alt_text="醫師選擇", contents=FlexContainer.from_dict(data))
        return message

    def choose_reservation_time(api, event):
        
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.get_id_and_name_sql
            args = {'line_user_id': event.source.user_id}
            cursor.execute(sql, args)
            res = cursor.fetchone()

        doctor_name = event.postback.data.split(" ")[1]
        reservation_type = event.postback.data.split(" ")[2]
        reservation_time = datetime.fromisoformat(event.postback.params['date']).strftime("%Y年%m月%d日")
        name = res['name']
        patient_id = res['national_id']
        
        reservation_info = json.dumps({
            'doctor_name': doctor_name,
            'reservation_type': reservation_type,
            'reservation_time': reservation_time,
            'name': name,
            'patient_id': patient_id
        })

        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.update_tmp_reservation_info_sql
            args = {'line_user_id': event.source.user_id, 'tmp_reservation_info': reservation_info}
            cursor.execute(sql, args)
        with open('line_bot/reply_info/time_select.json') as f:
            data = json.load(f)
        message = FlexMessage(alt_text="選擇預約時間", contents=FlexContainer.from_dict(data))
        return message
    
    def confirm_reservation_time(api, event):
        time = event.postback.data.split(" ")[1]
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.fetch_tmp_reservation_info_sql
            args = {'line_user_id': event.source.user_id}
            cursor.execute(sql, args)
            reservation_info = cursor.fetchone()
        reservation_info = json.loads(reservation_info['tmp_reservation_info'])
        reservation_info['reservation_time'] = reservation_info['reservation_time'].split(" ")[0] + " " + time
        reservation_info = json.dumps(reservation_info)
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.update_tmp_reservation_info_sql
            args = {'line_user_id': event.source.user_id, 'tmp_reservation_info': reservation_info}
            cursor.execute(sql, args)
        reservation_info = json.loads(reservation_info)
        with open('line_bot/reply_info/confirm.json') as f:
            data = json.load(f)
        data = Helper.update_confirm_json(data, reservation_info['doctor_name'], reservation_info['reservation_type'], reservation_info['reservation_time'], reservation_info['name'], reservation_info['patient_id'])
        message = FlexMessage(alt_text="確認資訊", contents=FlexContainer.from_dict(data))
        return message

    def finalize_reservation(api, event):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.fetch_tmp_reservation_info_sql
            args = {'line_user_id': event.source.user_id}
            cursor.execute(sql, args)
            reservation_info = cursor.fetchone()
        reservation_info = json.loads(reservation_info['tmp_reservation_info'])
        check_is_already_reserved = Helper.examine_reservation(event, reservation_info['reservation_time'])
        reservation_number = Helper.count_reservation_number(reservation_info['reservation_time'])
        if check_is_already_reserved:
            return "您已經預約過了，請勿重複預約"
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.confirm_reservation_sql
            args = {
                'patient_id': reservation_info['patient_id'],
                'doctor_name': reservation_info['doctor_name'],
                'reservation_type': reservation_info['reservation_type'],
                'reservation_date': reservation_info['reservation_time'],
                'reservation_number': reservation_number
            }
            cursor.execute(sql, args)
        return f"預約成功，您預約的時間為{reservation_info['reservation_time']}，預約號碼為{reservation_number}號"
    
    def cancel_reservation(api, event):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.get_active_reservation_sql
            args = {'line_user_id': event.source.user_id}
            cursor.execute(sql, args)
            reservation = cursor.fetchone()
        
        if reservation:
            with CursorFromConnectionPool() as cursor:
                sql = LineBotSQL.cancel_reservation_sql
                args = {'reservation_id': reservation['id']}
                cursor.execute(sql, args)
            return "預約取消成功"
        else:
            return "沒有找到任何尚未取消的預約資料"

    def check_reservation_count(api, event):...

    def check_reservation(api, event):
        with CursorFromConnectionPool() as cursor:
            sql = LineBotSQL.examine_reservation_sql
            args = {'line_user_id': event.source.user_id}
            cursor.execute(sql, args)
            res = cursor.fetchall()

        if not res:
            return "您尚未有任何預約"
        message = "您的預約如下：\n"
        message += "====================\n"
        for item in res:
            message += f"預約時間：{item['reservation_date']}\n預約號碼：{item['id']}\n預約醫師：{item['doctor_name']}\n預約科別：{item['reservation_type']}\n"
            message += "====================\n"
        return message

    def search_info(api, event):
        msg = event.message.text[5:]
        file_name = Command.query_mapping[msg]
        with open('line_bot/reply_info/' + file_name) as f:
            data = json.load(f)
        message = FlexMessage(alt_text="常見問題", contents=FlexContainer.from_dict(data))
        return message

class CommandSelector:
    mapping = {
        "常見問題": Command.faq,
        "我要預約": Command.create_reservation,
        "預約醫師": Command.display_doctor_selection,
        "預約時間": Command.choose_reservation_time,
        "預約時段選擇": Command.confirm_reservation_time,
        "確認預約": Command.finalize_reservation,
        "取消預約": Command.cancel_reservation,
        "我要查詢": Command.search_info,
        "預約查詢": Command.check_reservation,
        "預約人數查詢": Command.check_reservation_count
    }

    def __init__(self, api):
        self.api = api

    def execute_command(self, event):
        # ========== TODO ==========
        # 取消預約
        # 預約時間判斷是否有醫師值班及休假
        # 確認當前預約報到狀況
        # ==========================
    
        user_status = Helper.get_user_status(event)
        
        # if user is first time to use the bot
        if user_status == None:
            Helper.insert_new_user(event)
            user_status = Helper.get_user_status(event)
        
        if user_status['is_member'] == False:
            if event.message.text.split(" ")[0] == "常見問題":
                return Command.faq(self.api, event)
            return Helper.register(self.api, event)
        
        
        if isinstance(event, PostbackEvent):
            if event.postback.data.split(" ")[0] not in self.mapping:
                return "未知指令"
            return self.mapping[event.postback.data.split(" ")[0]](self.api, event)
        
        else:
            if event.message.text.split(" ")[0] not in self.mapping:
                return "未知指令"
            return self.mapping[event.message.text.split(" ")[0]](self.api, event)