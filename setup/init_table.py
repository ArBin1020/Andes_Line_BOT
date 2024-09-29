from sqlalchemy import create_engine, inspect
from const import *
from common import init_handler
from common.security import decrypt
import subprocess
from database import Account, UserData, Measure, Faces, LineUser, Reservation


init_logger = init_handler('init_logger', 'init.log', console_output=True)

# 定義資料庫連線資訊
DATABASE_URL = f"mariadb+mariadbconnector://{DB_USER}:{decrypt(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 建立資料庫引擎
engine = create_engine(DATABASE_URL)


# 檢查並建立缺少的資料表
def check_and_create_tables(engine):
    init_logger.info("Initializing the Database...")
    root_password = input("Enter MariaDB root password: ")
    result = subprocess.run(['bash', 'init_mariadb.sh'], input=root_password, capture_output=True, text=True)
    if result.returncode != 0:
        init_logger.info(f'Error occurred: \n{result.stderr}')
    else:
        init_logger.info("Initialization completed.")

    inspector = inspect(engine)
    tables = [Reservation, LineUser, Measure, Faces, UserData, Account]
    
    for table in tables:
        if inspector.has_table(table.__tablename__):
            table.__table__.drop(engine)
            init_logger.info(f"Table '{table.__tablename__}' already exists. Dropping...")

    for table in tables[::-1]:
        if not inspector.has_table(table.__tablename__):
            init_logger.info(f"Table '{table.__tablename__}' does not exist. Creating...")
            table.__table__.create(engine)
        else:

            table.__table__.create(engine)
            init_logger.info(f"Table '{table.__tablename__}' already exists")

def table_setup():
    # 執行檢查和建立資料表
    check_and_create_tables(engine)

