# -*- coding: utf-8 -*-
from flask import Flask, request, abort, jsonify
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
	ApiClient, Configuration, MessagingApi,
	ReplyMessageRequest, PushMessageRequest,
	TextMessage, PostbackAction
)
from linebot.v3.webhooks import (
	FollowEvent, MessageEvent, PostbackEvent, TextMessageContent
)
import os
import json

# HTTPリクエストを送信するライブラリ
import requests

## .env ファイル読み込み
from dotenv import load_dotenv
load_dotenv()

## 環境変数を変数に割り当て
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
OPENAI_APIKEY = os.getenv['OPENAI_APIKEY']

## Flask アプリのインスタンス化
app = Flask(__name__)

## LINE のアクセストークン読み込み
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

## コールバックのおまじない
@app.route("/callback", methods=['POST'])
def callback():
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)

	# handle webhook body
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
		abort(400)

	return 'OK'

## 友達追加時のメッセージ送信
@handler.add(FollowEvent)
def handle_follow(event):
	## APIインスタンス化
	with ApiClient(configuration) as api_client:
		line_bot_api = MessagingApi(api_client)

	## 返信
	line_bot_api.reply_message(ReplyMessageRequest(
		replyToken=event.reply_token,
		messages=[TextMessage(text='Thank You!')]
	))
	
## ChatGPTボット
@app.route('/webhook', methods=['POST'])
def webhook():
	data = request.json
	event = data['events'][0]

	reply_token = event['replyToken']
	user_message = event['message'].get('text', '???')

	# OpenAI APIへのリクエストの設定
	headers = {
		'Content-Type':'application/json',
		'Authorization': f'Bearer{OPENAI_APIKEY}'
	}
	body = {
		'model':'gpt-3.5-turbo',
		'messages':[
			{'role':'user', 'content': user_message}
		]
	}

	# OpenAI APIにリクエストを送信
	response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=body)
	response_json = response.json()
	text = response_json['choice'][0]['message']['content'].strip()

	# Line APIへの返信設定
	line_headers = {
		'Content-Type':'application/json',
		'Authorization': f'Bearer{CHANNEL_ACCESS_TOKEN}'
	}
	line_body = {
		'replyToken': reply_token,
		'messages': [{'type':'text', 'text': text}]
	}

	# LINE APIに返信を送信
	request.post('https://api.line.me/v2/bot/message/reply', headers=line_headers, json=line_body)

	return jsonify({'content':'post ok'}), 200

## オウム返しメッセージ
#@handler.add(MessageEvent, message=TextMessageContent)
#def handle_message(event):
	## APIインスタンス化
#	with ApiClient(configuration) as api_client:
#		line_bot_api = MessagingApi(api_client)

	## 受信メッセージの中身を取得
#	received_message = event.message.text

	## APIを呼んで送信者のプロフィール取得
#	profile = line_bot_api.get_profile(event.source.user_id)
#	display_name = profile.display_name

	## 返信メッセージ編集
#	reply = f'{display_name}さんのメッセージ\n{received_message}'

	## オウム返し
#	line_bot_api.reply_message(ReplyMessageRequest(
#		replyToken=event.reply_token,
#		messages=[TextMessage(text=reply)]
#	))

## 起動確認用ウェブサイトのトップページ
@app.route('/', methods=['GET'])
def toppage():
	return 'Hello world!'

## ボット起動コード
if __name__ == "__main__":
	## ローカルでテストする時のために、`debug=True` にしておく
	app.run(host="0.0.0.0", port=8000, debug=True)
