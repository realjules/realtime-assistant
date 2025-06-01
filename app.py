import os
import asyncio
import json
from datetime import datetime
from openai import AsyncOpenAI
import chainlit as cl
from chainlit.logger import logger

client = AsyncOpenAI()

# =============================================================================
# SASABOT DEMO DATA
# =============================================================================

DEMO_PRODUCTS = [
    {"id": "1", "name": "Samsung Galaxy A54", "price": 35000, "stock": 8, "category": "Electronics"},
    {"id": "2", "name": "Dell Inspiron Laptop", "price": 55000, "stock": 3, "category": "Electronics"},
    {"id": "3", "name": "Sony Wireless Headphones", "price": 4500, "stock": 15, "category": "Accessories"},
    {"id": "4", "name": "iPhone 13", "price": 75000, "stock": 2, "category": "Electronics"},
    {"id": "5", "name": "MacBook Air M1", "price": 120000, "stock": 1, "category": "Electronics"},
    {"id": "6", "name": "Bluetooth Speaker", "price": 2500, "stock": 20, "category": "Accessories"},
    {"id": "7", "name": "Phone Charger Cable", "price": 500, "stock": 50, "category": "Accessories"},
    {"id": "8", "name": "Tablet 10-inch", "price": 18000, "stock": 6, "category": "Electronics"},
]

DEMO_ORDERS = [
    {"id": "ORD001", "customer": "John Kamau", "product": "Samsung Galaxy A54", "amount": 35000, "status": "delivered"},
    {"id": "ORD002", "customer": "Mary Wanjiku", "product": "Dell Inspiron Laptop", "amount": 55000, "status": "shipped"},
    {"id": "ORD003", "customer": "Peter Ochieng", "product": "Sony Wireless Headphones", "amount": 9000, "status": "processing"},
]

# =============================================================================
# SASABOT TEXT-BASED TOOLS
# =============================================================================

async def show_products_handler(category: str = "all"):
    """Show available products"""
    products = DEMO_PRODUCTS
    if category != "all":
        products = [p for p in products if category.lower() in p["category"].lower()]
    
    if not products:
        return f"😕 No products found in category '{category}'. Try 'show products' to see all items."
    
    product_list = ["📦 **AVAILABLE PRODUCTS**\n"]
    for i, product in enumerate(products, 1):
        if product["stock"] > 10:
            availability = "✅ In Stock"
        elif product["stock"] > 5:
            availability = f"📦 {product['stock']} available"
        elif product["stock"] > 0:
            availability = f"⚠️ Only {product['stock']} left!"
        else:
            availability = "❌ Out of Stock"
        
        product_list.append(
            f"**{i}. {product['name']}**\n"
            f"   💰 KSh {product['price']:,.0f}\n"
            f"   📦 {availability}\n"
            f"   🏷️ {product['category']}\n"
        )
    
    footer = "\n💬 **To order:** Say 'buy [product name]' or ask 'how much is [product]?'"
    return "\n".join(product_list) + footer

async def add_product_handler(product_name: str, price: float, stock: int = 1, category: str = "General"):
    """Add new product to inventory"""
    # Check if product already exists
    for product in DEMO_PRODUCTS:
        if product["name"].lower() == product_name.lower():
            return f"❌ Product '{product_name}' already exists. Use 'update product' to modify it."
    
    new_product = {
        "id": str(len(DEMO_PRODUCTS) + 1),
        "name": product_name,
        "price": price,
        "stock": stock,
        "category": category
    }
    DEMO_PRODUCTS.append(new_product)
    
    return f"""✅ **Product Added Successfully!**

📱 **{product_name}**
💰 Price: KSh {price:,.0f}
📦 Stock: {stock} units
🏷️ Category: {category}

Product is now available for customers!"""

async def buy_product_handler(product_name: str, quantity: int = 1):
    """Purchase a product"""
    # Find product
    for product in DEMO_PRODUCTS:
        if product_name.lower() in product["name"].lower():
            if product["stock"] >= quantity:
                total = product["price"] * quantity
                product["stock"] -= quantity
                
                # Generate order ID
                order_id = f"ORD{len(DEMO_ORDERS) + 100:03d}"
                
                return f"""🛒 **Order Confirmed!**

📋 **Order ID:** {order_id}
✅ **Product:** {product['name']} x{quantity}
💰 **Total:** KSh {total:,.0f}

📱 **Payment Options:**
• M-Pesa: Pay via mobile money
• Cash on Delivery: Pay when you receive

🚚 **Delivery:**
• Same day delivery in Nairobi
• 1-2 days other areas
• Delivery fee: KSh 200

**Asante for shopping with Sasabot!**"""
            else:
                return f"❌ Sorry, only {product['stock']} units of {product['name']} available."
    
    return f"❌ Product '{product_name}' not found. Try 'show products' to see available items."

async def daily_report_handler():
    """Generate daily business report"""
    total_inventory = sum(p["price"] * p["stock"] for p in DEMO_PRODUCTS)
    low_stock_items = [p for p in DEMO_PRODUCTS if p["stock"] < 5]
    out_of_stock = [p for p in DEMO_PRODUCTS if p["stock"] == 0]
    
    # Simulate daily sales data
    daily_revenue = 85000
    daily_orders = 4
    daily_customers = 4
    
    report = f"""📊 **DAILY BUSINESS REPORT**
📅 {datetime.now().strftime('%B %d, %Y')}

💰 **Financial Performance:**
• Daily Revenue: KSh {daily_revenue:,.0f}
• Orders Processed: {daily_orders} orders
• Unique Customers: {daily_customers} customers
• Average Order Value: KSh {daily_revenue//daily_orders:,.0f}

📦 **Inventory Overview:**
• Total Products: {len(DEMO_PRODUCTS)} items
• Total Inventory Value: KSh {total_inventory:,.0f}
• Low Stock Items: {len(low_stock_items)} items
• Out of Stock: {len(out_of_stock)} items"""

    if low_stock_items:
        report += "\n\n⚠️ **Low Stock Alerts:**"
        for item in low_stock_items:
            report += f"\n• {item['name']}: {item['stock']} units remaining"
    
    if out_of_stock:
        report += "\n\n❌ **Out of Stock:**"
        for item in out_of_stock:
            report += f"\n• {item['name']}: Needs immediate restock"
    
    if not low_stock_items and not out_of_stock:
        report += "\n\n✅ **All products have sufficient stock!**"
    
    report += "\n\n💡 **Recommendation:** " + (
        "Focus on restocking low inventory items." if low_stock_items or out_of_stock 
        else "Great inventory management! Consider expanding popular categories."
    )
    
    return report

async def search_products_handler(search_term: str):
    """Search for products"""
    if not search_term.strip():
        return "🔍 What are you looking for? Try: 'search phones' or 'find laptops'"
    
    search_lower = search_term.lower()
    matching_products = []
    
    for product in DEMO_PRODUCTS:
        if (search_lower in product["name"].lower() or 
            search_lower in product.get("category", "").lower()):
            matching_products.append(product)
    
    if not matching_products:
        return f"""🔍 **No products found for '{search_term}'**

💡 **Try searching for:**
• Phones, Laptops, Headphones
• Electronics, Accessories
• Or browse all products with 'show products'"""
    
    result = [f"🔍 **Search Results for '{search_term}'** ({len(matching_products)} found)\n"]
    
    for i, product in enumerate(matching_products, 1):
        availability = "✅ Available" if product["stock"] > 5 else f"⚠️ Only {product['stock']} left"
        result.append(
            f"**{i}. {product['name']}**\n"
            f"   💰 KSh {product['price']:,.0f}\n"
            f"   📦 {availability}\n"
        )
    
    result.append("💬 Say 'buy [product name]' to purchase or ask for more details!")
    return "\n".join(result)

async def track_order_handler(order_id: str = ""):
    """Track order status"""
    if order_id:
        # Look for specific order
        for order in DEMO_ORDERS:
            if order_id.upper() in order["id"]:
                status_emoji = {
                    "pending": "⏳", "confirmed": "✅", "processing": "📦", 
                    "shipped": "🚚", "delivered": "✅", "cancelled": "❌"
                }
                
                return f"""📋 **ORDER TRACKING - {order['id']}**

👤 **Customer:** {order['customer']}
📱 **Product:** {order['product']}
💰 **Amount:** KSh {order['amount']:,.0f}
📊 **Status:** {status_emoji.get(order['status'], '📋')} {order['status'].title()}

🚚 **Delivery Updates:**
{
    "✅ Order delivered successfully!" if order['status'] == 'delivered' else
    "🚚 Your order is on the way! Expected delivery: Today" if order['status'] == 'shipped' else
    "📦 Order is being prepared for shipment" if order['status'] == 'processing' else
    "⏳ Order received, processing will begin shortly"
}

📞 **Need help?** Contact customer support anytime!"""
        
        return f"❌ Order '{order_id}' not found. Check your order ID and try again."
    
    # Show recent orders if no ID provided
    if DEMO_ORDERS:
        recent_orders = "📋 **Recent Orders:**\n\n"
        for order in DEMO_ORDERS[-3:]:  # Show last 3 orders
            status_emoji = {"pending": "⏳", "processing": "📦", "shipped": "🚚", "delivered": "✅"}
            recent_orders += f"• **{order['id']}** - {order['product']} - {status_emoji.get(order['status'], '📋')} {order['status'].title()}\n"
        
        recent_orders += "\n💬 Say 'track [order ID]' for detailed tracking info!"
        return recent_orders
    
    return "📋 No orders found. Place your first order to start tracking!"

async def help_handler(user_type: str, topic: str = ""):
    """Provide contextual help"""
    if user_type == "vendor":
        return """🆘 **VENDOR HELP GUIDE**

**📦 Product Management:**
• 'show products' - View your inventory
• 'add product [name] [price]' - Add new items
• 'show electronics' - Filter by category
• 'search [term]' - Find specific products

**📊 Business Reports:**
• 'daily report' - Today's performance summary
• 'weekly report' - 7-day business overview
• 'inventory status' - Stock levels and alerts

**💡 Natural Language Examples:**
• "Add iPhone for 75000 with 5 units"
• "Show me all electronics under 50k"
• "What products are running low?"
• "How did my business perform today?"

**Need specific help?** Ask about: products, inventory, reports, or sales"""

    elif user_type == "customer":
        return """🆘 **CUSTOMER HELP GUIDE**

**🛍️ Shopping Commands:**
• 'show products' - Browse all items
• 'show electronics' - Browse by category
• 'search [item]' - Find specific products
• 'buy [product]' - Purchase items
• 'track order' - Check order status

**💰 Price & Info:**
• 'how much is [product]?' - Check prices
• 'what phones do you have?' - Category browsing
• 'products under 30k' - Price filtering

**💡 Natural Language Examples:**
• "I'm looking for a good laptop under 60k"
• "Show me all phones available"
• "Buy Samsung Galaxy phone"
• "Track my recent order"

**🎯 Payment:** M-Pesa and Cash on Delivery available
**🚚 Delivery:** Same day in Nairobi, 1-2 days elsewhere"""

    else:
        return """🆘 **SASABOT HELP**

**🎯 Getting Started:**
• Say 'vendor' - Manage your business
• Say 'customer' - Shop for products

**🏪 For Business Owners:**
• Complete inventory management
• Sales reports and analytics
• Business insights and recommendations
• Natural language commands

**🛒 For Customers:**
• Easy product browsing
• Simple ordering process
• Order tracking
• M-Pesa payment integration

**🌟 Key Features:**
• No rigid commands - just talk naturally!
• Kenyan business context (KSh, M-Pesa, local terms)
• Real-time inventory management
• Comprehensive business reports

**📱 Real Implementation:**
This demo shows exactly how Sasabot works on WhatsApp for real Kenyan businesses!

**Choose your role to get started:**
• 'vendor' - Business management
• 'customer' - Shopping experience"""

# =============================================================================
# INTENT RECOGNITION & ROUTING
# =============================================================================

async def parse_user_intent(message: str, user_type: str):
    """Parse user intent from message"""
    msg_lower = message.lower().strip()
    
    # Help requests
    if any(word in msg_lower for word in ["help", "assistance", "commands", "what can you do"]):
        return {"action": "help", "params": {"topic": ""}}
    
    # Role switching
    if any(word in msg_lower for word in ["switch", "change role", "become customer", "become vendor"]):
        if "customer" in msg_lower:
            return {"action": "switch_role", "params": {"target_role": "customer"}}
        elif "vendor" in msg_lower:
            return {"action": "switch_role", "params": {"target_role": "vendor"}}
    
    if user_type == "vendor":
        # Vendor-specific intents
        if any(word in msg_lower for word in ["add", "create", "new product"]):
            return {"action": "add_product", "params": {"message": message}}
        
        elif any(word in msg_lower for word in ["show", "list", "view", "products", "inventory"]):
            category = "all"
            if "electronics" in msg_lower:
                category = "electronics"
            elif "accessories" in msg_lower:
                category = "accessories"
            return {"action": "show_products", "params": {"category": category}}
        
        elif any(word in msg_lower for word in ["report", "sales", "revenue", "performance", "daily", "business"]):
            return {"action": "daily_report", "params": {}}
        
        elif any(word in msg_lower for word in ["search", "find"]):
            # Extract search term
            for word in ["search", "find"]:
                if word in msg_lower:
                    search_term = msg_lower.split(word, 1)[1].strip()
                    return {"action": "search_products", "params": {"search_term": search_term}}
    
    elif user_type == "customer":
        # Customer-specific intents
        if any(word in msg_lower for word in ["show", "browse", "products", "catalog", "available"]):
            category = "all"
            if "electronics" in msg_lower:
                category = "electronics"
            elif "accessories" in msg_lower:
                category = "accessories"
            return {"action": "show_products", "params": {"category": category}}
        
        elif any(word in msg_lower for word in ["search", "find", "looking for"]):
            # Extract search term
            for word in ["search", "find", "looking for"]:
                if word in msg_lower:
                    search_term = msg_lower.split(word, 1)[1].strip()
                    return {"action": "search_products", "params": {"search_term": search_term}}
        
        elif any(word in msg_lower for word in ["buy", "purchase", "order", "want to buy"]):
            # Extract product name
            for word in ["buy", "purchase", "order", "want to buy"]:
                if word in msg_lower:
                    product_name = msg_lower.split(word, 1)[1].strip()
                    return {"action": "buy_product", "params": {"product_name": product_name}}
        
        elif any(word in msg_lower for word in ["track", "order status", "my order"]):
            # Extract order ID if provided
            words = msg_lower.split()
            order_id = ""
            for word in words:
                if word.startswith("ord") and len(word) > 3:
                    order_id = word
                    break
            return {"action": "track_order", "params": {"order_id": order_id}}
        
        elif any(word in msg_lower for word in ["how much", "price", "cost"]):
            return {"action": "show_products", "params": {"category": "all"}}
    
    # Default - general conversation
    return {"action": "general_conversation", "params": {"message": message}}

async def execute_action(action: str, params: dict, user_type: str):
    """Execute the parsed action"""
    try:
        if action == "help":
            return await help_handler(user_type, params.get("topic", ""))
        
        elif action == "switch_role":
            target_role = params.get("target_role")
            cl.user_session.set("user_type", target_role)
            if target_role == "vendor":
                return "🏪 **Switched to VENDOR mode**\n\nYou can now manage your business. Try:\n• 'show my products'\n• 'add product laptop 50000'\n• 'daily report'"
            else:
                return "🛒 **Switched to CUSTOMER mode**\n\nYou can now shop for products. Try:\n• 'show products'\n• 'buy phone'\n• 'search laptops'"
        
        elif action == "show_products":
            return await show_products_handler(params.get("category", "all"))
        
        elif action == "add_product":
            # Parse product details from message
            message = params.get("message", "")
            words = message.split()
            
            # Simple parsing - can be enhanced
            product_name = ""
            price = 0
            stock = 1
            
            # Look for price (numbers)
            for word in words:
                if word.replace(',', '').replace('.', '').isdigit():
                    price = float(word.replace(',', ''))
                    break
            
            # Get product name (words before price)
            name_words = []
            for word in words:
                if word.replace(',', '').replace('.', '').isdigit():
                    break
                if word.lower() not in ["add", "product", "new"]:
                    name_words.append(word)
            
            product_name = " ".join(name_words)
            
            if not product_name or price <= 0:
                return "🤔 Please specify product name and price.\n\nExample: 'Add product iPhone 75000'\nOr: 'Add laptop for 55000 with 3 units'"
            
            return await add_product_handler(product_name, price, stock)
        
        elif action == "buy_product":
            product_name = params.get("product_name", "").strip()
            if not product_name:
                return "🛒 Which product would you like to buy?\n\nTry: 'Buy Samsung phone' or browse products first with 'show products'"
            return await buy_product_handler(product_name)
        
        elif action == "daily_report":
            return await daily_report_handler()
        
        elif action == "search_products":
            return await search_products_handler(params.get("search_term", ""))
        
        elif action == "track_order":
            return await track_order_handler(params.get("order_id", ""))
        
        else:
            # General conversation fallback
            if user_type == "vendor":
                return "🏪 I'm here to help manage your business!\n\nTry:\n• 'show my products'\n• 'add product [name] [price]'\n• 'daily report'\n• 'help' for more options"
            elif user_type == "customer":
                return "🛒 I'm here to help you shop!\n\nTry:\n• 'show products'\n• 'search for [item]'\n• 'buy [product]'\n• 'help' for more options"
            else:
                return "🤖 Please choose your role first:\n• Say 'vendor' for business management\n• Say 'customer' for shopping"
    
    except Exception as e:
        logger.error(f"Error executing action {action}: {e}")
        return "😔 Sorry, I encountered an error. Please try again or type 'help' for assistance."

# =============================================================================
# CHAINLIT APP
# =============================================================================

@cl.on_chat_start
async def start():
    """Initialize Sasabot Text Demo"""
    try:
        # Initialize user session
        cl.user_session.set("user_type", "unknown")
        cl.user_session.set("message_count", 0)
        
        # Send welcome message
        welcome_msg = """🤖 **Karibu to Sasabot!**

I'm an AI assistant built specifically for Kenyan businesses and their customers.

**🎯 Choose your experience:**

👨‍💼 **BUSINESS OWNERS** - Say **"vendor"** or **"business owner"**
• Manage your inventory and products
• Generate sales reports and analytics
• Get business insights and recommendations
• Track performance and revenue

👥 **CUSTOMERS** - Say **"customer"** or **"shopper"**
• Browse and search for products
• Place orders with M-Pesa payments
• Track deliveries and order status
• Get personalized shopping assistance

**🇰🇪 Built for Kenya:**
• M-Pesa payment integration
• KSh currency and local context
• Swahili + English support
• SME-focused features

**📱 Real Implementation:**
*This demo shows exactly how Sasabot works on WhatsApp for real businesses!*

**💬 Just say "vendor" or "customer" to get started!**"""

        await cl.Message(content=welcome_msg).send()
        logger.info("Sasabot text demo initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Sasabot: {e}")
        await cl.ErrorMessage(
            content="😔 Sorry, there was an error starting Sasabot. Please refresh and try again."
        ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming text messages"""
    try:
        user_type = cl.user_session.get("user_type", "unknown")
        message_count = cl.user_session.get("message_count", 0) + 1
        cl.user_session.set("message_count", message_count)
        
        msg_lower = message.content.lower()
        
        # Handle role selection for new users
        if user_type == "unknown":
            if any(word in msg_lower for word in ["vendor", "business", "owner", "manage", "sell"]):
                cl.user_session.set("user_type", "vendor")
                response = """🏪 **VENDOR MODE ACTIVATED!**

Welcome to your AI business dashboard! You can now:

📦 **Manage Products:**
• 'show my products' - View inventory
• 'add product [name] [price]' - Add items
• 'search [product]' - Find specific items

📊 **Business Analytics:**
• 'daily report' - Performance summary
• 'inventory status' - Stock levels
• 'sales overview' - Revenue insights

💡 **Natural Language:**
Just talk normally! Say things like:
• "Add iPhone for 75000"
• "Show me all electronics"
• "How is business today?"

**What would you like to do first?**"""
                await cl.Message(content=response).send()
                return
                
            elif any(word in msg_lower for word in ["customer", "shop", "buy", "browse", "purchase"]):
                cl.user_session.set("user_type", "customer")
                response = """🛒 **CUSTOMER MODE ACTIVATED!**

Welcome to Sasabot Marketplace! You can now:

🛍️ **Browse & Shop:**
• 'show products' - View all items
• 'search [item]' - Find specific products
• 'show electronics' - Browse by category
• 'buy [product]' - Purchase items

💰 **Pricing & Orders:**
• 'how much is [product]?' - Check prices
• 'track my order' - Order status
• 'products under 30k' - Price filtering

💡 **Natural Shopping:**
Just ask naturally! Say things like:
• "Show me phones under 50k"
• "I want to buy a laptop"
• "What headphones do you have?"

**What are you looking for today?**"""
                await cl.Message(content=response).send()
                return
            
            else:
                response = """🤔 **Let me help you choose your role:**

**Say one of these:**
👨‍💼 **"vendor"** or **"business owner"** - Manage your business
👥 **"customer"** or **"shopper"** - Browse and buy products

**Or describe what you want to do:**
• "I want to manage my inventory"
• "I'm looking to buy a phone"
• "Show me the business dashboard"
• "I want to shop for electronics"

**What brings you to Sasabot today?**"""
                await cl.Message(content=response).send()
                return
        
        # Parse user intent and execute action
        intent_result = await parse_user_intent(message.content, user_type)
        response = await execute_action(
            intent_result["action"], 
            intent_result["params"], 
            user_type
        )
        
        await cl.Message(content=response).send()
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await cl.ErrorMessage(
            content="😔 Sorry, I encountered an error. Please try again or type 'help' for assistance."
        ).send()

@cl.on_chat_end
@cl.on_stop
async def on_end():
    """Clean up when conversation ends"""
    try:
        message_count = cl.user_session.get("message_count", 0)
        user_type = cl.user_session.get("user_type", "unknown")
        logger.info(f"Text session ended - User type: {user_type}, Messages: {message_count}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    logger.info("Starting Sasabot text-only demo...")