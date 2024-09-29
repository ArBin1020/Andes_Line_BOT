from common import init_handler
import subprocess
import time


init_logger = init_handler('init_logger', 'init.log', console_output=True)

def check_wifi_connection():
    try:
        # ping 命令檢查網絡連接
        subprocess.check_output(['ping', '-c', '1', '8.8.8.8'])
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect_wifi():
    try:
        # 重新啟動網絡服務
        subprocess.call(['sudo', 'systemctl', 'restart', 'dhcpcd'])
        init_logger.info("重新連接 WiFi 中...")
    except Exception as e:
        init_logger.error(f"重新連接 WiFi 時發生未知錯誤: {e}")

def wifi_setup():
    while True:
        if not check_wifi_connection():
            init_logger.info("WiFi 未連接，嘗試重新連接...")
            reconnect_wifi()
        else:
            init_logger.info("WiFi 已連接")
            break
        # 每隔 60 秒檢查一次
        time.sleep(60)
