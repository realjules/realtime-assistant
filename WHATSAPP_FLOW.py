"""
Simplified WhatsApp Flow - Fixes Chainlit context error
Uses OpenAI directly instead of trying to mock Chainlit
"""

import os
import requests
import json
from flask import Flask, Blueprint, request
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# WhatsApp Configuration
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN") or os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN") or os.getenv("VERIFY_TOKEN")
WHATSAPP_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID") or os.getenv("WHATSAPP_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Phone mappings
PHONE_TO_BUSINESS = {
    "+254762222000": {"business_id": "mama_jane_electronics", "role": "vendor", "name": "Jane"},
    # Add more mappings as needed
}

# Session storage
whatsapp_sessions = {}

app = Flask(__name__)
webhook_bp = Blueprint('webhook', __name__)

def normalize_phone(phone: str) -> str:
    """Normalize phone number"""
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("07") or phone.startswith("01"):
        phone = "+254" + phone[1:]
    elif phone.startswith("254"):
        phone = "+" + phone
    elif not phone.startswith("+"):
        phone = "+" + phone
    return phone

def get_business_context(phone: str):
    """Get business context for phone"""
    phone = normalize_phone(phone)
    return PHONE_TO_BUSINESS.get(phone, {
        "business_id": "mama_jane_electronics",
        "role": "customer", 
        "name": "Customer"
    })

def load_business_data(business_id: str = "mama_jane_electronics"):
    """Load business data from your existing JSON files"""
    try:
        # Load from your existing data files
        data_dir = "data"
        
        business_info = {}
        products = []
        
        # Try to load businesses
        businesses_file = os.path.join(data_dir, "businesses.json")
        if os.path.exists(businesses_file):
            with open(businesses_file, 'r') as f:
                businesses = json.load(f)
                business_info = businesses.get(business_id, {})
        
        # Try to load products
        products_file = os.path.join(data_dir, "products.json")
        if os.path.exists(products_file):
            with open(products_file, 'r') as f:
                all_products = json.load(f)
                products = [p for p in all_products if p.get("business_id") == business_id]
        
        return {
            "business": business_info,
            "products": products
        }
    except Exception as e:
        print(f"Error loading business data: {e}")
        return {"business": {}, "products": []}

async def process_message_with_openai(message: str, phone: str) -> str:
    """Process message using OpenAI directly (bypassing Chainlit context)"""
    try:
        # Get business context
        context = get_business_context(phone)
        business_data = load_business_data(context["business_id"])
        
        # Get or create session
        phone = normalize_phone(phone)
        if phone not in whatsapp_sessions:
            whatsapp_sessions[phone] = {
                "conversation_history": [],
                "user_role": context["role"],
                "business_id": context["business_id"]
            }
        
        session = whatsapp_sessions[phone]
        
        # Build system prompt
        if context["role"] == "vendor":
            system_prompt = f"""
You are Sasabot, an AI assistant for {context['name']}'s business ({context['business_id']}).

You help vendors manage their business:
- Track inventory and products
- Process orders and sales
- Answer customer questions
- Provide business insights

Business Info: {json.dumps(business_data['business'], indent=2)}
Products: {json.dumps(business_data['products'], indent=2)}

Keep responses concise for WhatsApp (under 300 words).
"""
        else:
            system_prompt = f"""
You are Sasabot, a helpful shopping assistant for Mama Jane Electronics.

You help customers:
- Find products they need
- Get product information and prices
- Place orders
- Track deliveries

Available Products: {json.dumps(business_data['products'], indent=2)}

Keep responses friendly and concise for WhatsApp (under 300 words).
Be helpful in finding the right products for customers.
"""
        
        # Build conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history
        for msg in session["conversation_history"][-5:]:  # Last 5 exchanges
            messages.append({"role": "user", "content": msg["user_message"]})
            messages.append({"role": "assistant", "content": msg["ai_response"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Save to conversation history
        session["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "ai_response": ai_response
        })
        
        # Keep only last 10 exchanges
        if len(session["conversation_history"]) > 10:
            session["conversation_history"] = session["conversation_history"][-10:]
        
        whatsapp_sessions[phone] = session
        
        return ai_response
        
    except Exception as e:
        print(f"Error processing message: {e}")
        return f"Sorry, I encountered an error processing your message. Please try again."

def save_interaction(phone: str, message: str):
    """Save customer interaction"""
    try:
        interactions_file = "data/whatsapp_interactions.json"
        os.makedirs("data", exist_ok=True)
        
        interactions = []
        if os.path.exists(interactions_file):
            try:
                with open(interactions_file, 'r') as f:
                    interactions = json.load(f)
            except:
                interactions = []
        
        interactions.append({
            "phone": normalize_phone(phone),
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "platform": "whatsapp"
        })
        
        # Keep only last 1000
        if len(interactions) > 1000:
            interactions = interactions[-1000:]
        
        with open(interactions_file, 'w') as f:
            json.dump(interactions, f, indent=2)
            
    except Exception as e:
        print(f"Error saving interaction: {e}")

def send_message(customer_id: str, text: str):
    """Send message to WhatsApp"""
    try:
        # Format for WhatsApp (4000 char limit)
        if len(text) > 4000:
            text = text[:3900] + "\n\n... (message truncated)"
        
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
        
        response = requests.post(url, headers=headers, json=payload)
        print(f"📤 Message sent: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Send error: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

@webhook_bp.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token') 
        challenge = request.args.get('hub.challenge')
        
        print(f"🔐 Verification: mode={mode}, token={token}")
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("✅ Webhook verified!")
            return challenge, 200
        else:
            print("❌ Webhook verification failed")
            return 'Verification failed', 403

    if request.method == 'POST':
        try:
            data = request.json
            print(f"📨 Webhook data: {json.dumps(data, indent=2)}")
            
            # Extract messages
            if data and 'entry' in data:
                entry = data['entry'][0]
                if 'changes' in entry:
                    changes = entry['changes'][0]
                    if 'value' in changes:
                        value = changes['value']
                        if 'messages' in value:
                            messages = value['messages']
                            
                            for message in messages:
                                if 'text' in message:
                                    customer_phone = message['from']
                                    message_body = message['text']['body']
                                    
                                    print(f"📱 Processing: {customer_phone} -> {message_body}")
                                    
                                    # Save interaction
                                    save_interaction(customer_phone, message_body)
                                    
                                    # Process with OpenAI (run async)
                                    import asyncio
                                    
                                    def run_async():
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        return loop.run_until_complete(
                                            process_message_with_openai(message_body, customer_phone)
                                        )
                                    
                                    try:
                                        response_text = run_async()
                                        print(f"🤖 AI Response: {response_text}")
                                        
                                        # Send response
                                        success = send_message(customer_phone, response_text)
                                        
                                        if success:
                                            print(f"✅ Response sent to {customer_phone}")
                                        else:
                                            print(f"❌ Failed to send to {customer_phone}")
                                            
                                    except Exception as e:
                                        print(f"❌ Error processing: {e}")
                                        # Send error message
                                        send_message(customer_phone, "Sorry, I'm having trouble right now. Please try again in a moment.")
                                
                                else:
                                    print(f"📎 Non-text message: {message.get('type', 'unknown')}")
            
            return "OK", 200
            
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return "Error", 500

# Register blueprint
app.register_blueprint(webhook_bp)

@app.route('/health')
def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Sasabot WhatsApp",
        "timestamp": datetime.now().isoformat(),
        "sessions_count": len(whatsapp_sessions)
    }

@app.route('/sessions')
def sessions():
    """View current sessions (for debugging)"""
    return {
        "sessions": whatsapp_sessions,
        "count": len(whatsapp_sessions)
    }

if __name__ == "__main__":
    print("🚀 Starting Simplified Sasabot WhatsApp...")
    print(f"📱 WhatsApp ID: {WHATSAPP_ID}")
    print(f"🔐 Verify Token: {VERIFY_TOKEN}")
    print(f"🤖 OpenAI: {'✅' if OPENAI_API_KEY else '❌'}")
    print("="*50)
    
    app.run(host='0.0.0.0', port=8080, debug=True)