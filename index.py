from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB connection setup
client = MongoClient(os.getenv('MONGO_DB_URL'))
db = client['your_database']
collection = db['your_collection']

@app.route('/')
def index():
    return '@Dhanrakshak'

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
                # Save image URL to MongoDB
                collection.insert_one({'chat_id': chat_id, 'image_url': image_url, 'command': 'dalle2'})
                send_message(chat_id, f"Image URL: {image_url}")
            else:
                send_message(chat_id, "Please provide a query after the /dalle2 command.")
        elif text.startswith('/image'):
            query = text[len('/image '):].strip()
            if query:
                image_url = process_dalle_request(query, 'image', chat_id)
                # Save image URL to MongoDB
                collection.insert_one({'chat_id': chat_id, 'image_url': image_url, 'command': 'image'})
                send_message(chat_id, f"Image URL: {image_url}")
            else:
                send_message(chat_id, "Please provide a query after the /image command.")
        elif text == '/start':
            send_message(chat_id, "I am working")
    except Exception as e:
        send_message(chat_id, f"Error processing message: {e}")

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
