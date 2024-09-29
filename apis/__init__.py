# import apis.api
import apis.api
from .model import ns
from common.handler import init_handler, CustomAPIError

from flask_restx import Api
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
import traceback

# Line import 
from linebot.v3.exceptions import InvalidSignatureError
from const import linebot_handler, access_token
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage, FlexMessage, Configuration
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent
from line_bot.func import CommandSelector


app = Flask(__name__)
# 設置日誌記錄
app.logger = init_handler('werkzeug', 'flask.log', console_output=True)

@app.errorhandler(Exception)
def handle_generic_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    elif isinstance(e, CustomAPIError):
        code = e.status_code
    
    if code == 500:
        app.logger.error(f'Status code: {code}, Error: {repr(e)}')
        app.logger.debug(traceback.format_exc())
    else:
        app.logger.info(f'Status code: {code}, Error: {repr(e)}')
    return jsonify(error=repr(e)), code

# Line callback
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        linebot_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        CustomAPIError(400, "Invalid signature. Please check your channel access token/channel secret.")

    return 'OK'


@linebot_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(Configuration(access_token=access_token)) as api_client:
        line_bot_api = MessagingApi(api_client)
        selector = CommandSelector(line_bot_api)
        msg = selector.execute_command(event)
        # line_bot_api.reply_message_with_http_info(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=msg)]))
        if isinstance(msg, FlexMessage):
            reply_message = msg 
        else:
            reply_message = TextMessage(text=msg)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )

@linebot_handler.add(PostbackEvent)
def handle_postback(event):
    with ApiClient(Configuration(access_token=access_token)) as api_client:
        line_bot_api = MessagingApi(api_client)
        selector = CommandSelector(line_bot_api)
        msg = selector.execute_command(event)
        if isinstance(msg, FlexMessage):
            reply_message = msg 
        else:
            reply_message = TextMessage(text=msg)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )

api = Api(app, version='1.0', title='My API',
          description='A simple demonstration API',
          doc='/api/doc')


api.add_namespace(ns, path='/v1')
