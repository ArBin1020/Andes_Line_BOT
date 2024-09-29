from flask_restx import Namespace, fields, reqparse
from werkzeug.datastructures import FileStorage

ns = Namespace('example', description='Example operations')

# 定義輸入模型
account_basic = ns.model('AccountBasic', {
    'username': fields.String(required=True, example='admin'),
    'password': fields.String(required=True, example='admin')
})

login_input_model = ns.inherit('LoginInputModel', account_basic, {
})

register_input_model = ns.inherit('RegisterInputModel', account_basic, {
})


face_register_parser = reqparse.RequestParser()
face_register_parser.add_argument('image', type=FileStorage, location='files', required=True, help='Image file')
face_register_parser.add_argument('name', type=str, required=True, help='Name of the person')

face_detect_parser = reqparse.RequestParser()
face_detect_parser.add_argument('image', type=FileStorage, location='files', required=True, help='Image file')
face_detect_response = ns.model("FaceDetectResponse", {
    'result': fields.Raw(description='The face detection result')
    }
)

info_input_model = ns.model('InfoInputModel', {
    'name': fields.String(required=True, example='John Doe'),
    'height': fields.Float(required=True, example=180.3),
    'weight': fields.Float(required=True, example=70.2),
    'gender': fields.Boolean(required=True, example=True),
    'national_id': fields.String(required=True, example='A123456789'),
    'birthday': fields.String(required=True, example='1990-01-01')
})