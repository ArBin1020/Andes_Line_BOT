from const import LOG_DIR
import logging
import os


# Check if the logs directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    filename=f'{LOG_DIR}app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

def init_handler(getLoggerName, filename, console_output=False):
    """
    input parmeter:
        getLoggerName:  logger名稱
        filename:       logger儲存的檔案名稱
        console_output: 是否顯示在終端機上
    """
    logger = logging.getLogger(getLoggerName)
    if not logger.handlers:
        file_handler = logging.FileHandler(f'{LOG_DIR}{filename}')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - PID: %(process)d - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        if console_output:
            logger.addHandler(console_handler)
    return logger

class CustomAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
