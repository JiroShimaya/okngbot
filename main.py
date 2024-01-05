from flask import Flask, request, abort

from linebot import (
  LineBotApi, WebhookHandler
)
from linebot.exceptions import (
  InvalidSignatureError
)
from linebot.models import (
  MessageEvent, TextMessage, TextSendMessage,
  TemplateSendMessage,ButtonsTemplate,MessageAction
)

from faq import Faq

app = Flask(__name__)

#返信するボタンテンプレートのリストを返す。
#候補の文字列リストが入力
def make_button_template(candidates):
  messages = []
  #candidateは１度に４つまでなので、数が多い場合は分けて、リストにして返す。
  max_loop = len(candidates)//4
  if len(candidates)%4>0: max_loop+=1
  max_loop = min(5, max_loop) #一度にメッセージを連続で送れるのは5個まで
  for i in range(max_loop):
    actions = []
    for c in candidates[i*4:i*4+4]:
      msg = MessageAction( label = c, text = c )
      actions.append(msg)
    message_template = TemplateSendMessage(
      alt_text="にゃーん",
      template=ButtonsTemplate(
        text="近いものを選んでください",
        #title="タイトルですよ",
        actions=actions
      )
    )
    messages.append(message_template)
  return messages

class LineManager:
  def __init__(self, config):
    self.line_bot_api = LineBotApi(config["channel_access_token"])
    self.handler = WebhookHandler(config["channel_secret"])
    self.faq = Faq(config)
    
    @self.handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
      print(event)
      # reply_tokenが特定の値だった場合に処理終了
      #if event.reply_token == "00000000000000000000000000000000":
      #  return      #入力文字列からcandidatesを取得し、得られたcandidateの個数に応じて返答を分岐する。
      #self.line_bot_api.reply_message(
      #  event.reply_token,
      #  TextSendMessage(text=event.message.text))
      #return
      given_msg = event.message.text
      #print("===1==========")
      return_msg = self.faq.get_answer(given_msg)
      #return_msg = given_msg
      if type(return_msg) is str:
        #print("===2-1==========")
        answer = TextSendMessage(text=return_msg)
      elif type(return_msg) is list:
        #print("===2-2==========")
        answer = make_button_template(return_msg)
      #print("===3==========")
      self.line_bot_api.reply_message(
        event.reply_token,
        answer
      )
      #print("===4==========")
      
    
  def callback(self):
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
      #print(body)
      self.handler.handle(body, signature)
    except InvalidSignatureError:
      print("Invalid signature. Please check your channel access token/channel secret.")
      abort(400)

    return 'OK'

#変更①。line_bot_apiをチャンネルごとに宣言する。チャンネルアクセストークン、チャンネルシークレットは別途jsonファイルから取得
if __name__ == "__main__":

  import json, os
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("--config_path", type=str, default="./config.json")
  parser.add_argument("--port", type=int, default=5001)
  args = parser.parse_args()

  CONF_PATH = args.config_path
  PORT = int(args.port)

  with open(CONF_PATH) as f:
    auth_token = json.load(f)
  LineManagers = {}
  for k, v in auth_token.items():
    LineManagers[k] = LineManager(v)


  for k, manager in LineManagers.items():
      endpoint = f"{k}_callback"  # 各マネージャーに対してユニークなエンドポイント名を生成
      app.add_url_rule(f"/{k}/callback", endpoint, manager.callback, methods=['POST'])  

      #外部からの接続を受け付けられるようにした上で、port番号を指定して、立ち上げ
  #    app.run()
  app.run(host="0.0.0.0", port=PORT)