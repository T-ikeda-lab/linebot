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
import openai

# HTTPリクエストを送信するライブラリ
import requests

# エラーログの取得
import logging
logging.basicConfig(filename='error.log', level=logging.DEBUG)

## .env ファイル読み込み
from dotenv import load_dotenv
load_dotenv()

## 環境変数を変数に割り当て
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
openai.api_key = os.getenv("OPENAI_API_KEY")

## Flask アプリのインスタンス化
app = Flask(__name__)

## LINE のアクセストークン読み込み
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
# api_client = ApiClient(configuration)  # MessagingApiのインスタンス化
# line_bot_api = MessagingApi(api_client)

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

# OpenAIの設定
def call_open_chat_api(user_message):
		
	response = openai.ChatCompletion.create(
		model='gpt-3.5-turbo',
		message=[
			{'role': 'system', 'content': 'You are helpful assustant.'},
			{'role': 'user', 'content': user_message}
		]
	)

	return response.choices[0].message['content']

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
	except Exception as e:
		# 予期せぬエラーをログ出力
		logging.exception("An error occurd during webhook handling:")
		abort(500)

	return 'OK'	

## Chatボット
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
	## APIインスタンス化
	with ApiClient(configuration) as api_client:
		line_bot_api = MessagingApi(api_client)

	# 受信メッセージの中身を取得
	user_message = event.message.text

	try:
		# OpenAIの返信結果
		result = call_open_chat_api(user_message)

		# LINEに返信を送信
		line_bot_api.reply_message_with_http_info(
   		ReplyMessageRequest(
        		replyToken=event.reply_token,
        		messages=[TextMessage(text=result)]
       		)
    	)
	except Exception as e:
		logging.exception("An error occured during message handling:")
		# エラー発生時にユーザーに通知
		line_bot_api.reply_message_with_http_info(
			ReplyMessageRequest(
				replyToken=event.reply_token,
				messages=[TextMessage(text="エラーが発生しました。")]
			)
		)
	# OpenAI APIへのリクエストの設定
#	headers = {
#			'Content-Type':'application/json',
#			'Authorization': f'Bearer {openai.api_key}'
#		}
#	body = {
#			'model':'gpt-3.5-turbo',
#			'messages':[
#			{'role':'user', 'content':user_message}
#			]
#		}
#
	# OpenAI APIにリクエストを送信
#	response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=body)
#	
	# OpenAI APIエラーハンドリング
#	if response.ok:
#		response_json = response.json()
#		text = response_json['choices'][0]['message']['content'].strip()
#	else:
#		text = "申し訳ありません。エラーが発生しました。"
#		app.logger.error(f"OpenAI API error: {response.status_code} {response.text}")


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
