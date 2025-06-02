import os
import asyncio
import json
from datetime import datetime
from openai import AsyncOpenAI
import chainlit as cl
from chainlit.logger import logger

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =============================================================================
# DYNAMIC DATA STORAGE
# =============================================================================

class DynamicDataStore:
    """Dynamic data storage that can be modified during runtime"""
    
    def __init__(self):
        self.businesses = {}
        self.products = {}
        self.orders = {}
        self.customers = {}
        self.initialize_demo_data()
    
    def initialize_demo_data(self):
        """Initialize with some demo data"""
        self.businesses = {
            "mama_jane_electronics": {
                "name": "Mama Jane's Electronics",
                "owner": "Jane Wanjiku",
                "location": "Nairobi, Kenya",
                "created_at": datetime.now().isoformat()
            }
        }
        
        self.products = {
            "1": {"id": "1", "name": "Samsung Galaxy A54", "price": 35000, "stock": 8, "category": "Electronics", "business_id": "mama_jane_electronics"},
            "2": {"id": "2", "name": "Dell Inspiron Laptop", "price": 55000, "stock": 3, "category": "Electronics", "business_id": "mama_jane_electronics"},
            "3": {"id": "3", "name": "Sony Wireless Headphones", "price": 4500, "stock": 15, "category": "Accessories", "business_id": "mama_jane_electronics"},
        }
    
    def add_product(self, business_id: str, name: str, price: float, stock: int = 1, category: str = "General"):
        """Dynamically add a new product"""
        product_id = str(len(self.products) + 1)
        self.products[product_id] = {
            "id": product_id,
            "name": name,
            "price": price,
            "stock": stock,
            "category": category,
            "business_id": business_id,
            "created_at": datetime.now().isoformat()
        }
        return product_id
    
    def update_product(self, product_id: str, **updates):
        """Update product details"""
        if product_id in self.products:
            self.products[product_id].update(updates)
            return True
        return False
    
    def get_products(self, business_id: str = None, category: str = None, max_price: float = None):
        """Get products with dynamic filtering"""
        products = list(self.products.values())
        
        if business_id:
            products = [p for p in products if p.get("business_id") == business_id]
        
        if category:
            products = [p for p in products if category.lower() in p.get("category", "").lower()]
        
        if max_price:
            products = [p for p in products if p.get("price", 0) <= max_price]
        
        return products
    
    def place_order(self, customer_name: str, product_id: str, quantity: int = 1):
        """Place a new order"""
        if product_id not in self.products:
            return None, "Product not found"
        
        product = self.products[product_id]
        if product["stock"] < quantity:
            return None, f"Only {product['stock']} units available"
        
        # Update stock
        self.products[product_id]["stock"] -= quantity
        
        # Create order
        order_id = f"ORD{len(self.orders) + 1000}"
        order = {
            "id": order_id,
            "customer_name": customer_name,
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "total": product["price"] * quantity,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        self.orders[order_id] = order
        return order_id, "Order placed successfully"

# Global data store
data_store = DynamicDataStore()

# =============================================================================
# AI-POWERED INTENT RECOGNITION
# =============================================================================

async def analyze_user_intent(message: str, user_type: str, conversation_history: list = []):
    """Use GPT to understand user intent and extract parameters"""
    
    # Build context from conversation history
    context = ""
    if conversation_history:
        recent_messages = conversation_history[-3:]  # Last 3 exchanges
        context = "\n".join([f"User: {h['user_message']}\nAssistant: {h['ai_response']}" for h in recent_messages])
    
    system_prompt = f"""You are an intelligent intent recognition system for Sasabot, a Kenyan business automation platform.

Current user type: {user_type}
Conversation context: {context}

Analyze the user's message and return a JSON response with:
1. "intent" - the primary intent (vendor intents: add_product, show_products, update_product, delete_product, generate_report, check_stock, update_stock; customer intents: browse_products, search_products, buy_product, track_order, add_to_cart, view_cart; general: help, switch_role, general_conversation)
2. "confidence" - confidence score 0-1
3. "parameters" - extracted parameters as key-value pairs
4. "reasoning" - brief explanation of your analysis

For Kenyan context, understand:
- Currency references (KSh, shillings)
- Local products and brands
- Natural language variations
- Swahili and English mixed usage

Examples:
- "Add iPhone for 75k" -> intent: add_product, parameters: {{"product_name": "iPhone", "price": 75000}}
- "Show me phones under 50k" -> intent: search_products, parameters: {{"search_term": "phones", "max_price": 50000}}
- "How are sales today?" -> intent: generate_report, parameters: {{"period": "daily"}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this message: '{message}'"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"Error in AI intent analysis: {e}")
        # Fallback to simple keyword matching
        return {
            "intent": "general_conversation",
            "confidence": 0.5,
            "parameters": {},
            "reasoning": "Fallback to general conversation due to analysis error"
        }

# =============================================================================
# AI-POWERED RESPONSE GENERATION
# =============================================================================

async def generate_dynamic_response(intent: str, parameters: dict, user_type: str, context: dict = {}):
    """Generate contextual responses using GPT"""
    
    system_prompt = f"""You are Sasabot, an intelligent AI assistant for Kenyan businesses and customers.

Current context:
- User type: {user_type}
- Intent: {intent}
- Parameters: {json.dumps(parameters)}
- Additional context: {json.dumps(context)}

Guidelines:
1. Use Kenyan context (KSh currency, local greetings like "Karibu", "Asante")
2. Be conversational and helpful
3. Include relevant emojis
4. Format prices as "KSh X,XXX"
5. Provide actionable next steps
6. Be encouraging and supportive

For business owners: Focus on growth, efficiency, and insights
For customers: Focus on great shopping experience and support

Generate a natural, helpful response that addresses the user's intent."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate response for intent '{intent}' with parameters {parameters}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating dynamic response: {e}")
        return "I understand what you're looking for. Let me help you with that!"

# =============================================================================
# DYNAMIC ACTION HANDLERS
# =============================================================================

async def handle_vendor_action(intent: str, parameters: dict, user_type: str):
    """Handle vendor actions dynamically"""
    
    if intent == "add_product":
        product_name = parameters.get("product_name", "")
        price = parameters.get("price", 0)
        stock = parameters.get("stock", 1)
        category = parameters.get("category", "General")
        
        if not product_name or price <= 0:
            response = await generate_dynamic_response(
                "error", 
                {"message": "Missing product name or invalid price"}, 
                user_type
            )
            return response
        
        business_id = cl.user_session.get("business_id", "mama_jane_electronics")
        product_id = data_store.add_product(business_id, product_name, price, stock, category)
        
        context = {
            "product_added": True,
            "product_name": product_name,
            "price": price,
            "stock": stock,
            "product_id": product_id
        }
        
        return await generate_dynamic_response("add_product_success", parameters, user_type, context)
    
    elif intent == "show_products":
        business_id = cl.user_session.get("business_id", "mama_jane_electronics")
        products = data_store.get_products(business_id=business_id)
        
        if not products:
            return await generate_dynamic_response("no_products", {}, user_type)
        
        # Create dynamic product listing
        product_list = []
        total_value = 0
        low_stock_count = 0
        
        for i, product in enumerate(products, 1):
            stock_status = "✅ In Stock" if product["stock"] > 5 else f"⚠️ Only {product['stock']} left"
            if product["stock"] == 0:
                stock_status = "❌ Out of Stock"
                
            if product["stock"] < 5:
                low_stock_count += 1
                
            product_list.append(f"**{i}. {product['name']}**\n   💰 KSh {product['price']:,.0f} | 📦 {stock_status}")
            total_value += product['price'] * product['stock']
        
        context = {
            "products": products,
            "product_list": "\n\n".join(product_list),
            "total_value": total_value,
            "low_stock_count": low_stock_count,
            "total_products": len(products)
        }
        
        return await generate_dynamic_response("show_products", {}, user_type, context)
    
    elif intent == "generate_report":
        period = parameters.get("period", "daily")
        business_id = cl.user_session.get("business_id", "mama_jane_electronics")
        
        # Calculate dynamic metrics
        products = data_store.get_products(business_id=business_id)
        orders = [o for o in data_store.orders.values() if any(p["business_id"] == business_id for p in products if p["id"] == o["product_id"])]
        
        total_revenue = sum(order["total"] for order in orders)
        total_orders = len(orders)
        total_products = len(products)
        inventory_value = sum(p["price"] * p["stock"] for p in products)
        
        context = {
            "period": period,
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_products": total_products,
            "inventory_value": inventory_value,
            "avg_order_value": total_revenue / max(total_orders, 1)
        }
        
        return await generate_dynamic_response("business_report", parameters, user_type, context)
    
    # Add more vendor actions as needed
    return await generate_dynamic_response(intent, parameters, user_type)

async def handle_customer_action(intent: str, parameters: dict, user_type: str):
    """Handle customer actions dynamically"""
    
    if intent == "browse_products" or intent == "search_products":
        category = parameters.get("category")
        max_price = parameters.get("max_price")
        search_term = parameters.get("search_term", "")
        
        products = data_store.get_products(category=category, max_price=max_price)
        
        # Filter by search term if provided
        if search_term:
            products = [p for p in products if search_term.lower() in p["name"].lower()]
        
        if not products:
            return await generate_dynamic_response("no_products_found", parameters, user_type)
        
        # Create dynamic product listing for customers
        product_list = []
        for i, product in enumerate(products, 1):
            availability = "✅ Available" if product["stock"] > 5 else f"⚠️ Only {product['stock']} left"
            if product["stock"] == 0:
                availability = "❌ Out of Stock"
                
            product_list.append(f"**{i}. {product['name']}**\n   💰 KSh {product['price']:,.0f}\n   📦 {availability}")
        
        context = {
            "products": products,
            "product_list": "\n\n".join(product_list),
            "total_found": len(products),
            "search_term": search_term,
            "category": category,
            "max_price": max_price
        }
        
        return await generate_dynamic_response("product_listing", parameters, user_type, context)
    
    elif intent == "buy_product":
        product_name = parameters.get("product_name", "").strip()
        quantity = parameters.get("quantity", 1)
        
        if not product_name:
            return await generate_dynamic_response("missing_product_name", {}, user_type)
        
        # Find product by name
        matching_products = [p for p in data_store.products.values() if product_name.lower() in p["name"].lower()]
        
        if not matching_products:
            context = {"product_name": product_name}
            return await generate_dynamic_response("product_not_found", parameters, user_type, context)
        
        product = matching_products[0]  # Take first match
        customer_name = cl.user_session.get("customer_name", "Customer")
        
        order_id, message = data_store.place_order(customer_name, product["id"], quantity)
        
        if order_id:
            context = {
                "order_placed": True,
                "order_id": order_id,
                "product_name": product["name"],
                "quantity": quantity,
                "total": product["price"] * quantity
            }
            return await generate_dynamic_response("order_success", parameters, user_type, context)
        else:
            context = {"error_message": message}
            return await generate_dynamic_response("order_failed", parameters, user_type, context)
    
    # Add more customer actions as needed
    return await generate_dynamic_response(intent, parameters, user_type)

# =============================================================================
# MAIN CHAT HANDLERS
# =============================================================================

@cl.on_chat_start
async def start():
    """Initialize Dynamic Sasabot"""
    try:
        cl.user_session.set("user_type", "unknown")
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("message_count", 0)
        
        welcome_msg = """🤖 **Karibu to Sasabot!**

I'm an AI-powered assistant that adapts to your needs in real-time.

**🧠 What makes me:**
• I understand natural language using AI
• I learn from our conversation
• I adapt responses based on context
• I can handle new scenarios intelligently

**🎯 Choose your role:**
👨‍💼 **"vendor"** or **"business owner"** - AI-powered business management
👥 **"customer"** or **"shopper"** - Intelligent shopping assistant

**Just start talking naturally - I'll understand! 🚀**"""

        await cl.Message(content=welcome_msg).send()
        logger.info("Dynamic Sasabot initialized")
        
    except Exception as e:
        logger.error(f"Error starting Dynamic Sasabot: {e}")
        await cl.ErrorMessage(content="😔 Error starting Sasabot. Please try again.").send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle messages with AI-powered understanding"""
    try:
        user_type = cl.user_session.get("user_type", "unknown")
        conversation_history = cl.user_session.get("conversation_history", [])
        message_count = cl.user_session.get("message_count", 0) + 1
        cl.user_session.set("message_count", message_count)
        
        msg_content = message.content.strip()
        
        # Handle role selection for new users
        if user_type == "unknown":
            if any(word in msg_content.lower() for word in ["vendor", "business", "owner", "manage"]):
                cl.user_session.set("user_type", "vendor")
                cl.user_session.set("business_id", "mama_jane_electronics")
                
                response = await generate_dynamic_response(
                    "role_activated", 
                    {"role": "vendor"}, 
                    "vendor"
                )
                await cl.Message(content=response).send()
                return
                
            elif any(word in msg_content.lower() for word in ["customer", "shop", "buy", "browse"]):
                cl.user_session.set("user_type", "customer")
                cl.user_session.set("customer_name", "Valued Customer")
                
                response = await generate_dynamic_response(
                    "role_activated", 
                    {"role": "customer"}, 
                    "customer"
                )
                await cl.Message(content=response).send()
                return
            else:
                response = await generate_dynamic_response(
                    "role_selection_needed", 
                    {}, 
                    "unknown"
                )
                await cl.Message(content=response).send()
                return
        
        # AI-powered intent analysis
        intent_analysis = await analyze_user_intent(msg_content, user_type, conversation_history)
        
        logger.info(f"AI Analysis: {intent_analysis}")
        
        intent = intent_analysis["intent"]
        parameters = intent_analysis["parameters"]
        confidence = intent_analysis["confidence"]
        
        # Handle the intent dynamically
        if user_type == "vendor":
            response = await handle_vendor_action(intent, parameters, user_type)
        elif user_type == "customer":
            response = await handle_customer_action(intent, parameters, user_type)
        else:
            response = await generate_dynamic_response(intent, parameters, user_type)
        
        await cl.Message(content=response).send()
        
        # Update conversation history
        conversation_history.append({
            "user_message": msg_content,
            "ai_response": response,
            "intent": intent,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 exchanges
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        cl.user_session.set("conversation_history", conversation_history)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await cl.ErrorMessage(content="😔 I encountered an error. Please try rephrasing your message.").send()

@cl.on_chat_end
@cl.on_stop
async def on_end():
    """Cleanup"""
    try:
        message_count = cl.user_session.get("message_count", 0)
        user_type = cl.user_session.get("user_type", "unknown")
        logger.info(f"Dynamic session ended - User: {user_type}, Messages: {message_count}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    logger.info("Starting Dynamic AI-Powered Sasabot...")