import os
import httpx
from io import BytesIO
from PIL import Image

# Set up constants
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
DALLE2_ENDPOINT = f'{AZURE_OPENAI_ENDPOINT}/dalle2'
DALLE3_ENDPOINT = f'{AZURE_OPENAI_ENDPOINT}/dalle3'

# Generate DALL-E 2 Image
def generate_dalle2_image(query):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_API_KEY
    }
    payload = {
        'prompt': query,
        'n': 1
    }
    
    response = httpx.post(DALLE2_ENDPOINT, headers=headers, json=payload)
    if response.status_code == 200:
        image_url = response.json().get('data', [{}])[0].get('url', '')
        return image_url
    else:
        return f"Error: {response.status_code} - {response.text}"

# Generate DALL-E 3 Image
def generate_dalle3_image(query):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_API_KEY
    }
    payload = {
        'prompt': query,
        'n': 1
    }
    
    response = httpx.post(DALLE3_ENDPOINT, headers=headers, json=payload)
    if response.status_code == 200:
        image_url = response.json().get('data', [{}])[0].get('url', '')
        return image_url
    else:
        return f"Error: {response.status_code} - {response.text}"

# Retrieve image from URL and convert to bytes
def get_image_bytes(image_url):
    image_content = httpx.get(image_url).content
    return BytesIO(image_content)

# Endpoint for sending messages via Telegram
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{os.getenv("TELEGRAM_API_TOKEN")}/sendMessage'
    response = httpx.post(url, data={'chat_id': chat_id, 'text': text})
    return response.json()

def process_dalle_request(query, command, chat_id):
    if command == 'dalle2':
        image_url = generate_dalle2_image(query)
    elif command == 'image':
        image_url = generate_dalle3_image(query)
    else:
        send_message(chat_id, "Unknown command.")
        return "Unknown command."
    
    if "Error:" in image_url:
        send_message(chat_id, image_url)
        return image_url
    
    image_bytes = get_image_bytes(image_url)
    # Optionally display or further process the image_bytes here if needed
    send_message(chat_id, f"Image generated successfully: {image_url}")
    return image_url
