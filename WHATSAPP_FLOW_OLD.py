import os
import requests
from flask import Blueprint, request
from services.whatsapp_handler import handle_intelligent_response, send_message
from utils.db import save_customer_interaction
from datetime import datetime, timezone
from config.config import VERIFY_TOKEN

MONGO_URI = os.getenv("MONGO_URI")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_ID = os.getenv("Whatsapp_ID")
OPENAI_API_KEY = os.getenv("API_KEY_OPENAI")
FLOW_ID = os.getenv("FLOW_ID")
FLOW_TOKEN = os.getenv("FLOW_TOKEN")

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Verification failed', 403

    if request.method == 'POST':
        try:
            data = request.json
            messages = data.get('entry', [])[0].get('changes', [])[0].get('value', {}).get('messages', [])

            if messages:
                message_body = messages[0].get('text', {}).get('body', '')
                customer_id = messages[0]['from']

                timestamp = datetime.now(timezone.utc)
                save_customer_interaction(customer_id, message_body, timestamp)
                response_text = handle_intelligent_response(message_body, customer_id)
                send_message(customer_id, response_text)

                return "OK", 200
            return "No messages", 400
        except Exception as e:
            print(f"Webhook error: {e}")
            return "Error", 500
        


def send_message(customer_id: str, text: str) -> None:
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": customer_id,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Text sent: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending text: {e}")