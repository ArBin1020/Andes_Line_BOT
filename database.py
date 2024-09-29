from mariadb import PoolError
from mariadb import ConnectionPool
import time
from const import *
from common import decrypt
import threading
from sqlalchemy import (Column, Integer, String, TIMESTAMP, func,
                        Text, Boolean, ForeignKey, DECIMAL)
from sqlalchemy.orm import declarative_base
from common import init_handler


db_logger = init_handler("database", "database.log", console_output=True)

Base = declarative_base()

class Database:
    __connection_pool = None

    @staticmethod
    def init():
        Database.__connection_pool = ConnectionPool(
            pool_name="conn_pool",
            pool_size=10,
            user=DB_USER,
            password=decrypt(DB_PASSWORD),
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
    
    @staticmethod
    def get_connection():
        if Database.__connection_pool is None:
            Database.init()
        
        connection = None
        while connection is None:
            try:
                connection = Database.__connection_pool.get_connection()
            except PoolError:
                print("No connection available, waiting...")
                time.sleep(0.1)  # 等待0.1秒後再嘗試
        return connection
    
    @staticmethod
    def close_all_connections():
        if Database.__connection_pool is not None:
            Database.__connection_pool.close()


class CursorFromConnectionPool:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = Database.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)
        return self.cursor
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:
            db_logger.error(f"Error({exception_type}): {exception_value}")
            self.conn.rollback()
        else:
            self.cursor.close()
            self.conn.commit()
        self.conn.close()


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    verified = Column(Boolean, server_default='0')


class UserData(Base):
    __tablename__ = 'userdata'
    uid = Column(Integer, ForeignKey('account.id'), primary_key=True)
    name = Column(String(255), nullable=True, server_default=None)
    height = Column(DECIMAL(5, 2), server_default='0')
    weight = Column(DECIMAL(5, 2), server_default='0')
    gender = Column(Boolean, nullable=True, server_default=None)
    national_id = Column(String(20), nullable=False, unique=True)
    birthday = Column(TIMESTAMP, nullable=True, server_default=None)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Measure(Base):
    __tablename__ = 'measure'
    uid = Column(Integer, ForeignKey('account.id'), primary_key=True)
    pulse = Column(Integer, server_default='0')
    temperature = Column(DECIMAL(3, 1), server_default='0')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Faces(Base):
    __tablename__ = "faces"

    face_id = Column(String(100), primary_key=True)
    face_encodings = Column(Text, nullable=False)

class LineUser(Base):
    __tablename__ = "line_user"
    line_user_id = Column(String(100), primary_key=True)
    patient_id = Column(String(20), ForeignKey('userdata.national_id'))
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_member = Column(Boolean, server_default='0')
    tmp_reservation_info = Column(Text, nullable=True)

class Reservation(Base):
    __tablename__ = "reservation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(20), ForeignKey('userdata.national_id'))
    doctor_name = Column(String(255), nullable=False)
    reservation_type = Column(String(20), nullable=False)
    reservation_date = Column(String(20), nullable=False)
    reservation_number = Column(Integer, nullable=True)
    is_cancelled = Column(Boolean, server_default='0')

if __name__ == "__main__":

    def test_connection():
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM account")
            print(cursor.fetchall())
    
    with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM account")
        print(cursor.fetchall())
    
    threads = []
    for i in range(100):
        thread = threading.Thread(target=test_connection)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()