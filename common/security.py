from cryptography.fernet import Fernet
from authlib.jose import jwt, JoseError
from const import SE_KEY, SECRET_KEY


# 生成密鑰
# key = Fernet.generate_key()
cipher_suite = Fernet(SE_KEY)

# 加密密碼
def encrypt(password):
    encrypted_password = cipher_suite.encrypt(password.encode())
    return encrypted_password

# 解密密碼
def decrypt(encrypted_password):
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode()
    return decrypted_password

# 生成 JWT Token
def generate_token(data: dict):
    header = {'alg': 'HS256'}
    # data = data.update({'exp': datetime.utcnow() + timedelta(seconds=expires_in), 'jti': str(uuid.uuid4())})
    return jwt.encode(header=header, payload=data, key=SECRET_KEY).decode('utf-8')

# 驗證 JWT Token
def verify_token(token):
    if not token:
        return None
    try:
        data = jwt.decode(token, SECRET_KEY)
        return data
    except JoseError:
        return None