import requests
from flask import Flask
import os
import requests
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_ID = os.getenv("Whatsapp_ID")
OPENAI_API_KEY = os.getenv("API_KEY_OPENAI")
FLOW_ID = os.getenv("FLOW_ID")
FLOW_TOKEN = os.getenv("FLOW_TOKEN")

app = Flask(__name__)


# Route for verifying webhook (GET)
@app.route("/webhook", methods=["GET"])
def verify():

    mode = requests.args.get("hub.mode")
    token = requests.args.get("hub.verify_token")
    challenge = requests.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403

# Route to handle incoming messages (POST)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = requests.get_json()
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        messages = value.get('messages')

        if messages:
            phone_number = messages[0]['from']  
            user_message = messages[0]['text']['body'] 

            # Trigger the WhatsApp Flow for any incoming message
            send_flow(phone_number)

    except Exception as e:
        print("Error processing message:", e)

    return "OK", 200

# Function to send a WhatsApp Flow
def send_flow(recipient_number):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {
                "type": "text",
                "text": "Welcome to Sasabot"
            },
            "body": {
                "text": "Let's get you started. Tap below to begin onboarding."
            },
            
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_id": {FLOW_ID},
                    "flow_token": FLOW_TOKEN,
                    "flow_cta": "Start Onboarding",
                    "mode": "live"  
                }
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Flow sent:", response.status_code, response.text)

# Run the Flask app
if __name__ == "__main__":
    app.run(port=5000, debug=True)
