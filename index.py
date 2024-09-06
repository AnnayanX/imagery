import os
import httpx
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from io import BytesIO
from PIL import Image
from openai import AzureOpenAI

# Configuration
app = Flask(__name__)

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI')  # Ensure this URI includes the database name
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['mydatabase']  # Replace 'mydatabase' with your actual database name
collection = db.get_collection('messages')

# Telegram API configuration
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
if not TELEGRAM_API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN environment variable is not set")
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}'

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://opendalle.openai.azure.com/')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
if not AZURE_OPENAI_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY environment variable is not set")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_version="2024-02-01",
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

def send_message(chat_id, text):
    url = f'{TELEGRAM_API_URL}/sendMessage'
    response = requests.post(url, data={'chat_id': chat_id, 'text': text})
    return response.json()

def send_image(chat_id, image_url):
    url = f'{TELEGRAM_API_URL}/sendPhoto'
    response = requests.post(url, data={'chat_id': chat_id, 'photo': image_url})
    return response.json()

def get_openai_response(query):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_API_KEY,
    }
    payload = {
        "prompt": query,
        "max_tokens": 150,
        "temperature": 0.7,
        "top_p": 0.95,
    }
    response = httpx.post(f'{AZURE_OPENAI_ENDPOINT}/openai/deployments/davinci-codex/completions', headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['text'].strip()

def generate_dalle_image(prompt):
    # Generate image using DALL-E 3
    result = client.images.generate(
        model="dalle3",  # DALL-E 3 deployment
        prompt=prompt,
        n=1
    )

    # Extract image URL from response
    image_url = result.data[0].url

    return image_url

@app.route('/', methods=['GET'])
def home():
    return render_template_string("<html><body><h1>@Dhanrakshak</h1></body></html>")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # Extract chat_id and message text
    chat_id = data.get('message', {}).get('chat', {}).get('id')
    text = data.get('message', {}).get('text', '')

    if not chat_id or not text:
        return jsonify(success=False, message="Received invalid data in webhook"), 400

    try:
        if text.startswith('/ask'):
            query = text[len('/ask '):].strip()
            if query:
                answer = get_openai_response(query)
                send_message(chat_id, answer)
            else:
                send_message(chat_id, "Please provide a query after the /ask command.")
        elif text.startswith('/dalle2') or text.startswith('/image'):
            query = text[len('/dalle2 '):].strip() if text.startswith('/dalle2') else text[len('/image '):].strip()
            if query:
                image_url = generate_dalle_image(query)
                send_image(chat_id, image_url)
            else:
                send_message(chat_id, "Please provide a query after the /dalle2 or /image command.")
        elif text == '/start':
            send_message(chat_id, "Bot is Working")

        # Store the message in MongoDB
        collection.insert_one({
            'chat_id': chat_id,
            'text': text,
            'processed_at': datetime.datetime.utcnow()
        })

    except Exception as e:
        error_message = f"Error processing message: {e}"
        send_message(chat_id, error_message)
        app.logger.error(error_message, exc_info=True)
        return jsonify(success=False, message="An internal error occurred"), 500

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
