from database import CursorFromConnectionPool, Account, UserData, Measure
from common.security import generate_token
from common.handler import CustomAPIError
from common.func import format_date
from functools import wraps
from .util import FaceDetector


def assert_all_keys_present(required_keys: list[str]):
    """
    A decorator that asserts all required keys are present in the function's kwargs.
    Args:
        required_keys (list[str]): A list of required keys.
    """
    def _wrapper(func):
        @wraps(func)
        def _inner(*args, **kwargs):
            for key in required_keys:
                if key not in kwargs:
                    raise ValueError(f"Missing required key: {key}")
                
            return func(*args, **kwargs)
        return _inner
    return _wrapper


class UserInfoModule(object):
    save_monitor_info_sql = """
        INSERT INTO {measure_table} ()
        VALUES (%()s)
    """.format(measure_table=Measure.__tablename__)

    save_user_info_sql = """
        INSERT INTO {userdata_table} (uid, name, height, weight, gender, idcard, birthday)
        VALUES (%(uid)s, %(name)s, %(height)s, %(weight)s, %(gender)s, %(idcard)s, %(birthday)s)
    """.format(userdata_table=UserData.__tablename__)

    get_account_sql = """
        SELECT * FROM {account_table}
        WHERE id = %(uid)s
    """.format(account_table=Account.__tablename__)

    @staticmethod
    def save_monitor_info(payload):
        with CursorFromConnectionPool() as cursor:
            sql = UserInfoModule.save_monitor_info_sql
            args = payload
            cursor.execute(sql, args)

    @staticmethod
    def save_user_info(payload):
        with CursorFromConnectionPool() as cursor:
            sql = UserInfoModule.get_account_sql
            args = {'uid': payload['uid']}
            cursor.execute(sql, args)
            if not cursor.fetchone():
                CustomAPIError(401, 'User is not found.')

            sql = UserInfoModule.save_user_info_sql
            formatted_date = format_date(payload['birthday'])
            if not formatted_date:
                CustomAPIError(400, 'Invalid date format.')
            payload['birthday'] = formatted_date
            args = payload
            cursor.execute(sql, args)

class UserAccountModule(object):
    get_account_sql = """
        SELECT * FROM {account_table}
        WHERE username = %(username)s
    """.format(account_table=Account.__tablename__)

    insert_account_sql = """
        INSERT INTO {account_table} (username, password)
        VALUES (%(username)s, %(password)s)
        RETURNING id
    """.format(account_table=Account.__tablename__)

    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def login(self):
        with CursorFromConnectionPool() as cursor:
            sql = UserAccountModule.get_account_sql
            args = {'username': self.username}
            cursor.execute(sql, args)
            user = cursor.fetchone()
            if user and user['password'] == self.password:
                return {"token": generate_token({"uid": user['id']})}
            else:
                CustomAPIError(401, 'Invalid username or password.')

    def register(self):
        with CursorFromConnectionPool() as cursor:
            sql = UserAccountModule.get_account_sql
            args = {'username': self.username}
            cursor.execute(sql, args)
            if cursor.fetchone():
                CustomAPIError(400, 'Username already exists.')
            
            sql = UserAccountModule.insert_account_sql
            args = {'username': self.username, 'password': self.password}
            cursor.execute(sql, args)


@assert_all_keys_present(required_keys=["image"])
def detect_face(**kwargs) -> dict[str, bool]:
    """
    A function that detects faces in an image.
    Args:
        image (bytes): The image to detect faces from.

    Returns:
        dict[str, bool]: A dictionary containing the face name and a boolean value indicating if the face is detected.
    """
    detector = FaceDetector()
    return detector.detect_face(kwargs["image"])

@assert_all_keys_present(required_keys=["image", "name"])
def register_face(**kwargs):
    """
    A function that registers a face.
    Args:
        image (bytes): The image of the face.
        name (str): The name of the person.
    """
    detector = FaceDetector()
    detector.register_face(name=kwargs["name"], face_image=kwargs["image"])
