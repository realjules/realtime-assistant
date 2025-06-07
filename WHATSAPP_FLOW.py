"""
Comprehensive WhatsApp Flow Fix - Addresses all identified issues
"""

import os
import requests
import json
import asyncio
import time
from flask import Flask, Blueprint, request
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import AsyncOpenAI
from collections import defaultdict

# Load environment variables
load_dotenv()

# WhatsApp Configuration
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN") or os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN") or os.getenv("VERIFY_TOKEN")
WHATSAPP_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID") or os.getenv("WHATSAPP_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Updated phone mappings based on actual interaction data
PHONE_TO_BUSINESS = {
    "+254762222000": {"business_id": "mama_jane_electronics", "role": "vendor", "name": "Jane"},
    # Default all phones to customers for Mama Jane Electronics for now
    # Real implementation would have proper business registration
}

# Session storage with improved structure
whatsapp_sessions = {}

# Message deduplication and rate limiting
message_cache = defaultdict(dict)
user_last_message_time = defaultdict(float)
RATE_LIMIT_SECONDS = 2
DUPLICATE_WINDOW_SECONDS = 30

app = Flask(__name__)
webhook_bp = Blueprint('webhook', __name__)

def normalize_phone(phone: str) -> str:
    """Normalize phone number to consistent format"""
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("07") or phone.startswith("01"):
        phone = "+254" + phone[1:]
    elif phone.startswith("254"):
        phone = "+" + phone
    elif phone.startswith("250"):
        phone = "+" + phone
    elif not phone.startswith("+"):
        phone = "+" + phone
    return phone

def is_duplicate_or_rate_limited(phone: str, message: str) -> tuple[bool, str]:
    """
    Check if message is duplicate or rate limited
    Returns (should_skip, reason)
    """
    current_time = time.time()
    phone = normalize_phone(phone)
    
    # Rate limiting check
    if phone in user_last_message_time:
        time_since_last = current_time - user_last_message_time[phone]
        if time_since_last < RATE_LIMIT_SECONDS:
            return True, f"rate_limited ({time_since_last:.1f}s ago)"
    
    # Clean old messages from cache
    if phone in message_cache:
        message_cache[phone] = {
            msg: timestamp for msg, timestamp in message_cache[phone].items()
            if current_time - timestamp < DUPLICATE_WINDOW_SECONDS
        }
    
    # Duplicate message check
    if message in message_cache[phone]:
        time_diff = current_time - message_cache[phone][message]
        if time_diff < DUPLICATE_WINDOW_SECONDS:
            return True, f"duplicate ({time_diff:.1f}s ago)"
    
    # Store this message and update timestamps
    message_cache[phone][message] = current_time
    user_last_message_time[phone] = current_time
    
    return False, "allowed"

def get_business_context(phone: str):
    """Get business context for phone number"""
    phone = normalize_phone(phone)
    
    # Check explicit mappings first
    if phone in PHONE_TO_BUSINESS:
        return PHONE_TO_BUSINESS[phone]
    
    # Default all unknown numbers to customers of Mama Jane Electronics
    return {
        "business_id": "mama_jane_electronics",
        "role": "customer", 
        "name": "Customer"
    }

def load_business_data(business_id: str = "mama_jane_electronics"):
    """Load business data from existing JSON files"""
    try:
        data_dir = "data"
        business_info = {}
        products = []
        
        # Load businesses
        businesses_file = os.path.join(data_dir, "businesses.json")
        if os.path.exists(businesses_file):
            with open(businesses_file, 'r') as f:
                businesses = json.load(f)
                business_info = businesses.get(business_id, {})
        
        # Load products  
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

def format_response_for_whatsapp(response: str) -> str:
    """Format AI response appropriately for WhatsApp"""
    # Remove excessive markdown formatting
    response = response.replace('**', '')
    response = response.replace('*', '')
    response = response.replace('###', '')
    response = response.replace('##', '')
    response = response.replace('#', '')
    
    # Remove bullet points and replace with simple dashes
    response = response.replace('•', '-')
    response = response.replace('◦', '-')
    
    # Limit length (WhatsApp best practice)
    if len(response) > 500:
        # Find a good breaking point
        sentences = response.split('. ')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence + ". ") < 450:
                truncated += sentence + ". "
            else:
                break
        
        if truncated:
            response = truncated.strip()
            if not response.endswith('.'):
                response += "."
            response += "\n\nWould you like more details?"
        else:
            # If no good breaking point, hard truncate
            response = response[:450] + "...\n\nMessage truncated. Please ask for specific details."
    
    # Clean up multiple newlines
    while '\n\n\n' in response:
        response = response.replace('\n\n\n', '\n\n')
    
    return response.strip()

def get_conversation_context(phone: str) -> dict:
    """Get conversation context and state"""
    phone = normalize_phone(phone)
    
    if phone not in whatsapp_sessions:
        whatsapp_sessions[phone] = {
            "conversation_history": [],
            "first_interaction": datetime.now().isoformat(),
            "message_count": 0,
            "last_context": "greeting",
            "needs_introduction": True
        }
    
    session = whatsapp_sessions[phone]
    session["message_count"] = session.get("message_count", 0) + 1
    
    # Check if it's been a while since last interaction (new conversation)
    if session["conversation_history"]:
        last_msg_time = session["conversation_history"][-1].get("timestamp", "")
        try:
            last_time = datetime.fromisoformat(last_msg_time.replace('Z', '+00:00'))
            if (datetime.now(timezone.utc) - last_time).total_seconds() > 1800:  # 30 minutes
                session["needs_introduction"] = True
        except:
            pass
    
    return session

async def process_message_with_openai(message: str, phone: str) -> str:
    """Process message using OpenAI with improved context and formatting"""
    try:
        # Get contexts
        business_context = get_business_context(phone)
        conversation_context = get_conversation_context(phone)
        business_data = load_business_data(business_context["business_id"])
        
        # Determine if this is a greeting or new conversation
        message_lower = message.lower().strip()
        greeting_words = ["hello", "hi", "hey", "good morning", "good afternoon", "hola", "karibu"]
        is_greeting = any(word in message_lower for word in greeting_words)
        
        # Build appropriate system prompt based on context
        if conversation_context["needs_introduction"] or is_greeting:
            conversation_guidance = """
IMPORTANT: This is a new conversation or greeting. Please:
1. Greet warmly and introduce yourself as "Sasabot, an AI assistant for Mama Jane Electronics"
2. Ask how you can help them today
3. DO NOT immediately list all products or be pushy
4. Be conversational and helpful
"""
            conversation_context["needs_introduction"] = False
        else:
            conversation_guidance = """
CONTEXT: Continuing existing conversation. Be natural and respond to what they're asking.
"""
        
        # Enhanced system prompt
        system_prompt = f"""You are Sasabot, a friendly AI assistant for Mama Jane Electronics in Kenya.

{conversation_guidance}

PERSONALITY:
- Warm, helpful, and conversational (never pushy or overly sales-focused)
- Use "Karibu" naturally but sparingly
- Ask questions to understand customer needs
- Be honest about what's available
- Keep responses concise and natural for WhatsApp chat

BUSINESS INFO:
- Business: {business_data['business'].get('name', 'Mama Jane Electronics')}
- Location: {business_data['business'].get('location', 'Nairobi, Kenya')}
- Phone: {business_data['business'].get('phone', '+254762222000')}

AVAILABLE PRODUCTS: {len(business_data['products'])} items
{json.dumps(business_data['products'][:3], indent=2) if business_data['products'] else "No products currently loaded"}

CONVERSATION RULES:
1. Keep responses under 200 words for WhatsApp
2. Be helpful, not pushy about sales
3. Ask clarifying questions when customers want products
4. Only suggest specific products when customers show interest
5. Be honest about pricing and availability
6. Use simple, clear language

USER TYPE: {business_context['role']}
MESSAGE COUNT: {conversation_context['message_count']}"""

        # Build messages for OpenAI API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 3 exchanges)
        recent_history = conversation_context["conversation_history"][-3:]
        for exchange in recent_history:
            messages.append({"role": "user", "content": exchange.get("user_message", "")})
            messages.append({"role": "assistant", "content": exchange.get("ai_response", "")})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=400,  # Limit response length
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Format response for WhatsApp
        formatted_response = format_response_for_whatsapp(ai_response)
        
        # Save to conversation history
        conversation_context["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "ai_response": formatted_response
        })
        
        # Keep only last 10 exchanges
        if len(conversation_context["conversation_history"]) > 10:
            conversation_context["conversation_history"] = conversation_context["conversation_history"][-10:]
        
        whatsapp_sessions[normalize_phone(phone)] = conversation_context
        
        return formatted_response
        
    except Exception as e:
        print(f"Error processing message: {e}")
        return "Sorry, I'm having trouble right now. Please try again in a moment."

def save_interaction(phone: str, message: str):
    """Save customer interaction to JSON file"""
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
        
        # Keep only last 1000 interactions
        if len(interactions) > 1000:
            interactions = interactions[-1000:]
        
        with open(interactions_file, 'w') as f:
            json.dump(interactions, f, indent=2)
            
    except Exception as e:
        print(f"Error saving interaction: {e}")

def send_message(customer_id: str, text: str):
    """Send message to WhatsApp with proper error handling"""
    try:
        # Ensure message isn't too long for WhatsApp
        if len(text) > 4096:
            text = text[:4000] + "\n\n... (message truncated)"
        
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
        print(f"📤 Message sent to {customer_id}: {response.status_code}")
        
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
            print(f"📨 Webhook received: {len(str(data))} chars")
            
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
                                    
                                    # Check for duplicates and rate limiting
                                    should_skip, reason = is_duplicate_or_rate_limited(customer_phone, message_body)
                                    
                                    if should_skip:
                                        print(f"🚫 Skipping message from {customer_phone}: {reason}")
                                        continue
                                    
                                    print(f"📱 Processing: {customer_phone} -> {message_body}")
                                    
                                    # Save interaction
                                    save_interaction(customer_phone, message_body)
                                    
                                    # Process with OpenAI in a new event loop
                                    try:
                                        # Create and run new event loop for async processing
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        
                                        response_text = loop.run_until_complete(
                                            process_message_with_openai(message_body, customer_phone)
                                        )
                                        
                                        loop.close()
                                        
                                        print(f"🤖 AI Response ready ({len(response_text)} chars)")
                                        
                                        # Send response
                                        success = send_message(customer_phone, response_text)
                                        
                                        if success:
                                            print(f"✅ Response sent to {customer_phone}")
                                        else:
                                            print(f"❌ Failed to send to {customer_phone}")
                                            
                                    except Exception as e:
                                        print(f"❌ Error processing message: {e}")
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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Sasabot WhatsApp",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(whatsapp_sessions),
        "message_cache_size": sum(len(cache) for cache in message_cache.values())
    }

@app.route('/sessions')
def sessions():
    """View current sessions (for debugging)"""
    return {
        "sessions": {phone: {
            "message_count": session.get("message_count", 0),
            "last_message": session.get("conversation_history", [{}])[-1].get("timestamp", "never") if session.get("conversation_history") else "never",
            "needs_intro": session.get("needs_introduction", True)
        } for phone, session in whatsapp_sessions.items()},
        "total_sessions": len(whatsapp_sessions)
    }

if __name__ == "__main__":
    print("🚀 Starting Enhanced Sasabot WhatsApp...")
    print(f"📱 WhatsApp ID: {WHATSAPP_ID}")
    print(f"🔐 Verify Token: {VERIFY_TOKEN}")
    print(f"🤖 OpenAI: {'✅' if OPENAI_API_KEY else '❌'}")
    print("="*50)
    
    app.run(host='0.0.0.0', port=8080, debug=True)