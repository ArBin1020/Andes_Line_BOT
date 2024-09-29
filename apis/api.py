from .model import ns, login_input_model, register_input_model, face_register_parser, face_detect_parser, face_detect_response, \
                    info_input_model
from .module import UserAccountModule, UserInfoModule, detect_face, register_face
from common.func import get_token
from common.handler import CustomAPIError

from functools import wraps
from flask_restx import Resource


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token()
        if not token:
            raise CustomAPIError(401, 'Unauthorized access.')
        ns.payload['uid'] = token['uid']
        return f(*args, **kwargs)
    return decorated_function


@ns.route('/login')
class Login(Resource):
    @ns.expect(login_input_model)
    # @ns.marshal_with(output_model)
    def post(self):
        payload = ns.payload
        data = UserAccountModule(payload['username'], payload['password']).login()
        return {"result": 0, "data": data}

@ns.route('/register')
class Register(Resource):
    @ns.expect(register_input_model)
    def post(self):
        payload = ns.payload
        UserAccountModule(payload['username'], payload['password']).register()
        return {"result": 0, "message": "Account created successfully."}
    
@ns.route('/detect_face')
class DetectFace(Resource):
    @ns.expect(face_detect_parser)
    @ns.marshal_with(face_detect_response)
    def post(self):
        data = face_detect_parser.parse_args()
        return {"result": 0, "data": detect_face(**data)}
    
@ns.route('/register_face')
class RegisterFace(Resource):
    @ns.expect(face_register_parser)
    def post(self):
        data = face_register_parser.parse_args()
        register_face(**data)
        return {"result": 0, "message": "Face registered successfully."}

@ns.route('/user_info')
class UserInfo(Resource):
    @login_required
    @ns.expect(info_input_model)
    def post(self):
        payload = ns.payload
        UserInfoModule.save_user_info(payload)
        return {"result": 0, "message": "User info saved successfully."}