"""
Fixed WhatsApp Flow Integration
Uses existing Sasabot components with minimal changes
"""

import os
import requests
import asyncio
from flask import Flask, Blueprint, request
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing components
from utils.simple_db import db
from realtime.assistant import SasabotAssistant

# WhatsApp Configuration from your .env
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN") or os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN") or os.getenv("VERIFY_TOKEN")
WHATSAPP_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID") or os.getenv("WHATSAPP_ID")

# Initialize your existing assistant
assistant = SasabotAssistant()

# Store WhatsApp sessions (using your phone number as key)
whatsapp_sessions = {}

# Phone to business mapping (simple approach)
PHONE_TO_BUSINESS = {
    "+254712345678": {"business_id": "mama_jane_electronics", "role": "vendor", "name": "Jane"},
    # Add more mappings as needed
}

app = Flask(__name__)
webhook_bp = Blueprint('webhook', __name__)

def normalize_phone(phone: str) -> str:
    """Normalize phone number to +254 format"""
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("07") or phone.startswith("01"):
        phone = "+254" + phone[1:]
    elif phone.startswith("254"):
        phone = "+" + phone
    elif not phone.startswith("+"):
        phone = "+" + phone
    return phone

def get_business_context(phone: str):
    """Get business context for phone number"""
    phone = normalize_phone(phone)
    mapping = PHONE_TO_BUSINESS.get(phone, {
        "business_id": "mama_jane_electronics",  # Default business
        "role": "customer", 
        "name": "Customer"
    })
    return mapping

def create_mock_session(phone: str):
    """Create mock Chainlit session for WhatsApp user"""
    context = get_business_context(phone)
    
    session = {
        "user_type": context["role"],
        "business_id": context["business_id"], 
        "message_count": 0,
        "conversation_history": [],
        "start_time": datetime.now(),
        "phone": phone
    }
    
    whatsapp_sessions[phone] = session
    return session

def get_session(phone: str):
    """Get or create session for phone number"""
    phone = normalize_phone(phone)
    if phone not in whatsapp_sessions:
        return create_mock_session(phone)
    return whatsapp_sessions[phone]

class MockChainlitSession:
    """Mock Chainlit user session for WhatsApp"""
    def __init__(self, session_data):
        self.data = session_data
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value

async def process_whatsapp_message(phone: str, message: str) -> str:
    """Process message using your existing assistant"""
    try:
        # Get WhatsApp session
        session = get_session(phone)
        
        # Create mock Chainlit context
        mock_session = MockChainlitSession(session)
        
        # Temporarily monkey-patch chainlit for your assistant
        import sys
        import types
        
        # Create mock chainlit module
        mock_cl = types.ModuleType('chainlit')
        mock_cl.user_session = mock_session
        
        # Store original and replace
        original_cl = sys.modules.get('chainlit')
        sys.modules['chainlit'] = mock_cl
        
        try:
            # Use your existing assistant
            response = await assistant.process_message(message)
            
            # Update session
            session["message_count"] = session.get("message_count", 0) + 1
            
            # Add to conversation history
            if "conversation_history" not in session:
                session["conversation_history"] = []
            
            session["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_message": message,
                "ai_response": response
            })
            
            # Keep last 10 exchanges
            if len(session["conversation_history"]) > 10:
                session["conversation_history"] = session["conversation_history"][-10:]
            
            # Save session
            whatsapp_sessions[phone] = session
            
            return response
            
        finally:
            # Restore original chainlit
            if original_cl:
                sys.modules['chainlit'] = original_cl
            elif 'chainlit' in sys.modules:
                del sys.modules['chainlit']
                
    except Exception as e:
        print(f"Error processing message: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def format_for_whatsapp(text: str) -> str:
    """Format response for WhatsApp (4000 char limit)"""
    # Replace markdown with simple formatting
    formatted = text.replace("**", "*")  # Bold
    formatted = formatted.replace("##", "")  # Headers
    formatted = formatted.replace("###", "")
    
    # Truncate if too long
    if len(formatted) > 4000:
        formatted = formatted[:3900] + "\n\n... (message truncated)"
    
    return formatted

def save_customer_interaction(customer_id: str, message: str, timestamp: datetime):
    """Save interaction to your existing database"""
    try:
        # Use your existing database to save interactions
        # You can extend simple_db.py or just save to a simple file
        interactions_file = "data/whatsapp_interactions.json"
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Load existing interactions
        interactions = []
        if os.path.exists(interactions_file):
            import json
            try:
                with open(interactions_file, 'r') as f:
                    interactions = json.load(f)
            except:
                interactions = []
        
        # Add new interaction
        interactions.append({
            "phone": normalize_phone(customer_id),
            "message": message,
            "timestamp": timestamp.isoformat(),
            "platform": "whatsapp"
        })
        
        # Keep only last 1000
        if len(interactions) > 1000:
            interactions = interactions[-1000:]
        
        # Save back
        import json
        with open(interactions_file, 'w') as f:
            json.dump(interactions, f, indent=2)
            
    except Exception as e:
        print(f"Error saving interaction: {e}")

def send_message(customer_id: str, text: str):
    """Send message to WhatsApp"""
    try:
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
        print(f"Message sent: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"Error sending message: {e}")

@webhook_bp.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token') 
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("✅ Webhook verified!")
            return challenge, 200
        else:
            print("❌ Webhook verification failed")
            return 'Verification failed', 403

    if request.method == 'POST':
        try:
            data = request.json
            print(f"📨 Webhook data: {data}")
            
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
                                    timestamp = datetime.now(timezone.utc)
                                    
                                    print(f"📱 Message from {customer_phone}: {message_body}")
                                    
                                    # Save interaction
                                    save_customer_interaction(customer_phone, message_body, timestamp)
                                    
                                    # Process with your assistant (run async in thread)
                                    def run_async():
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        return loop.run_until_complete(
                                            process_whatsapp_message(customer_phone, message_body)
                                        )
                                    
                                    response_text = run_async()
                                    
                                    # Format for WhatsApp
                                    formatted_response = format_for_whatsapp(response_text)
                                    
                                    # Send response
                                    send_message(customer_phone, formatted_response)
                                    
                                    print(f"✅ Processed message from {customer_phone}")
            
            return "OK", 200
            
        except Exception as e:
            print(f"❌ Error processing webhook: {e}")
            return "Error", 500

# Register blueprint
app.register_blueprint(webhook_bp)

@app.route('/health')
def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Sasabot WhatsApp", 
        "timestamp": datetime.now().isoformat()
    }

@app.route('/test')
def test():
    """Test endpoint"""
    return {
        "message": "WhatsApp webhook is running!",
        "webhook_url": "/webhook",
        "verify_token": VERIFY_TOKEN[:5] + "..." if VERIFY_TOKEN else "NOT SET"
    }

if __name__ == "__main__":
    print("🚀 Starting Sasabot WhatsApp Integration...")
    print(f"📱 WhatsApp ID: {WHATSAPP_ID}")
    print(f"🔐 Verify Token: {VERIFY_TOKEN}")
    print(f"🔗 Webhook: /webhook")
    print(f"❤️ Health: /health") 
    print("="*50)
    
    # Check environment
    if not all([ACCESS_TOKEN, VERIFY_TOKEN, WHATSAPP_ID]):
        print("❌ Missing environment variables!")
        print("Please check your .env file")
    else:
        print("✅ Environment variables loaded")
    
    app.run(host='0.0.0.0', port=8080, debug=True)