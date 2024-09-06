import os
import requests

# Azure OpenAI configuration
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')

def get_openai_response(query, retries=3, backoff_factor=1):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_API_KEY,
    }

    MAX_TOKENS = 4096
    MAX_INPUT_TOKENS = MAX_TOKENS - 800

    input_tokens = count_tokens(query)
    if input_tokens > MAX_INPUT_TOKENS:
        query = ' '.join(query.split()[:MAX_INPUT_TOKENS])

    payload = {
        'messages': [
            {
                'role': 'system',
                'content': [
                    {
                        'type': 'text',
                        'text': 'You are an AI assistant that helps people find information.'
                    }
                ]
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': query
                    }
                ]
            }
        ],
        'temperature': 0.7,
        'top_p': 0.95,
        'max_tokens': 800
    }

    url = f'{AZURE_OPENAI_ENDPOINT}/v1/engines/davinci-codex/completions'  # Adjust endpoint if needed

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 429:
                wait_time = backoff_factor * (2 ** attempt)
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            response_data = response.json()
            answer = response_data.get('choices', [{}])[0].get('text', 'No response content')
            return answer
        except requests.RequestException as e:
            if attempt == retries - 1:
                return f"Failed to make the request. Error: {e}"
            wait_time = backoff_factor * (2 ** attempt)
            print(f"Request failed. Waiting for {wait_time} seconds before retrying.")
            time.sleep(wait_time)

    return "Failed to get a response after several attempts."

def count_tokens(text):
    return len(text.split())

def process_dalle_request(query, model_name):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_API_KEY,
    }

    payload = {
        'prompt': query,
        'n': 1
    }

    if model_name == 'dalle2':
        url = f'{AZURE_OPENAI_ENDPOINT}/v1/images/generations'  # Adjust endpoint if needed
    elif model_name == 'image':
        url = f'{AZURE_OPENAI_ENDPOINT}/v1/images/generations'  # Adjust endpoint if needed
    else:
        return "Unsupported model name."

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    response_data = response.json()
    image_url = response_data.get('data', [{}])[0].get('url', '')
    return image_url

def send_message(chat_id, text):
    TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
    TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage'
    response = requests.post(TELEGRAM_API_URL, data={'chat_id': chat_id, 'text': text})
    return response.json()
