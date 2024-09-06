import os
import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
from openai import get_openai_response, process_dalle_request, send_message

app = Flask(__name__)

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client.get_database()  # Use default database or specify one
collection = db.get_collection('messages')  # Specify your collection

# Telegram API configuration
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    chat_id = data.get('message', {}).get('chat', {}).get('id')
    text = data.get('message', {}).get('text', '')

    if not chat_id or not text:
        send_message(chat_id, "Received invalid data in webhook")
        return jsonify(success=False), 400

    try:
        if text.startswith('/ask'):
            query = text[len('/ask '):].strip()
            if query:
                answer = get_openai_response(query)
                send_message(chat_id, answer)
            else:
                send_message(chat_id, "Please provide a query after the /ask command.")
        elif text.startswith('/dalle2'):
            query = text[len('/dalle2 '):].strip()
            if query:
                image_url = process_dalle_request(query, 'dalle2', chat_id)
                send_message(chat_id, f"Image URL: {image_url}")
            else:
                send_message(chat_id, "Please provide a query after the /dalle2 command.")
        elif text.startswith('/image'):
            query = text[len('/image '):].strip()
            if query:
                image_url = process_dalle_request(query, 'image', chat_id)
                send_message(chat_id, f"Image URL: {image_url}")
            else:
                send_message(chat_id, "Please provide a query after the /image command.")
        elif text == '/start':
            send_message(chat_id, "I am working")

        # Store the message in MongoDB
        collection.insert_one({
            'chat_id': chat_id,
            'text': text,
            'processed_at': datetime.datetime.utcnow()
        })

    except Exception as e:
        send_message(chat_id, f"Error processing message: {e}")

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
