from flask import request
from datetime import datetime

from .security import verify_token


def format_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None

def get_token():
    token = request.headers.get('Authorization')
    return verify_token(token)