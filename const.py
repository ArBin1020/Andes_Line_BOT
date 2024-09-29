
from linebot.v3 import WebhookHandler

# =========================
# Symmetric Encryption Key
# =========================
SE_KEY = 'SE_KEY'
SECRET_KEY = 'SECRET_KEY'

# =========================
# Database Configuration
# =========================
DB_USER = "DB_USER"
DB_HOST = "DB_HOST"
DB_PORT = 3306
DB_PASSWORD = 'DB_PORT'
DB_NAME = "DB_NAME"

# =========================
# MQTT Configuration
# =========================
MQTT_broker = "MQTT_broker"
MQTT_PORT = 1883

# =========================
# Flask Configuration
# =========================
FLASK_PORT = 5032

# =========================
# Logging Configuration
# =========================
LOG_DIR = "logs/"



# =========================
# Line Configuration
# =========================
headers = {'Authorization':'Bearer headers','Content-Type':'application/json'}
access_token = 'access_token'
linebot_handler = WebhookHandler('linebot_handler')
