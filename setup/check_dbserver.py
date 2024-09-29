from common import init_handler
import subprocess


init_logger = init_handler('init_logger', 'init.log', console_output=True)

def check_maria_status():
    try:
        output = subprocess.check_output(['systemctl', 'is-active', 'mariadb'])
        if output.strip() == b'active':
            init_logger.info("MariaDB 服務已正常運行")
            return True
        else:
            init_logger.info("MariaDB 服務未運行")
            return False
    except subprocess.CalledProcessError:
        init_logger.error("發生未知錯誤，無法檢查 MariaDB 服務狀態")
        return False

def start_maria_service():
    try:
        subprocess.check_call(['sudo', 'systemctl', 'start', 'mariadb'])
        init_logger.info("MariaDB 服務已啟動")
    except subprocess.CalledProcessError as e:
        init_logger.error(f"發生未知錯誤，無法啟動 MariaDB 服務: {e}")

def db_setup():
    # 檢查 MariaDB 服務狀態
    if not check_maria_status():
        init_logger.info("嘗試啟動 MariaDB 服務...")
        start_maria_service()
        if not check_maria_status():
            init_logger.info("無法啟動 MariaDB 服務，請檢查錯誤日誌")
