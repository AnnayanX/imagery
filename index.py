from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

# Import functions from openai.py
from openai import send_message, get_openai_response

# Access environment variables set in Vercel
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
OPENAI_ENDPOINT = os.getenv('OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')  # Chat ID for sending error messages

TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}'

@app.route('/')
def index():
    return '@Dhanrakshak'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # Extract chat_id and message text
    chat_id = data.get('message', {}).get('chat', {}).get('id')
    text = data.get('message', {}).get('text', '')

    if not chat_id or not text:
        send_message(CHAT_ID, "Received invalid data in webhook")
        return jsonify(success=False), 400

    try:
        # Check if the message starts with the '/ask' command
        if text.startswith('/ask'):
            query = text[len('/ask '):].strip()
            if query:
                answer = get_openai_response(query)
                send_message(chat_id, answer)
            else:
                send_message(chat_id, "Please provide a query after the /ask command.")
        elif text == '/start':
            send_message(chat_id, "I am working")
    except Exception as e:
        send_message(CHAT_ID, f"Error processing message: {e}")

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
