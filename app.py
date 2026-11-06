import os
import math
import re
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 從環境變數讀取密鑰（安全做法，部署時會在網站後台設定）
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# 兩點距離計算核心邏輯
def calculate_distance(user_message):
    numbers = re.findall(r'-?\d+\.?\d*', user_message)
    if len(numbers) != 4:
        return "格式錯誤！請輸入兩點座標數字。\n例如輸入：(1,2) (4,6) 或 1,2,4,6"
    
    x1, y1, x2, y2 = map(float, numbers)
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return f"📍 座標 1：({x1}, {y1})\n📍 座標 2：({x2}, {y2})\n\n📏 兩點間的距離為：{round(distance, 4)}"

# 接收 LINE Webhook 訊號的網址路徑
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# 當收到文字訊息時觸發此副程式
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    # 呼叫計算公式
    result_text = calculate_distance(user_text)
    
    # 回傳訊息給使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=result_text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
