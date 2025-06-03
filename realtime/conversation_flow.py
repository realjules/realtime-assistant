"""
Conversation Flow Tools
Handles chat interaction and AI conversation logic
"""

import chainlit as cl
import json
from typing import Dict, List, Optional

# =============================================================================
# WELCOME & GREETING
# =============================================================================

welcome_message_def = {
    "name": "welcome_message",
    "description": "Generate personalized welcome message based on user role",
    "parameters": {
        "type": "object",
        "properties": {
            "user_type": {
                "type": "string",
                "enum": ["vendor", "customer", "unknown"],
                "description": "Type of user"
            },
            "business_name": {
                "type": "string",
                "description": "Business name for vendors",
                "default": ""
            }
        },
        "required": ["user_type"]
    }
}

async def welcome_message_handler(user_type: str, business_name: str = ""):
    """Generate welcome message"""
    if user_type == "vendor":
        business_display = f" - {business_name}" if business_name else ""
        message = f"""🏪 **Karibu to Sasabot Business Dashboard{business_display}!**

I'm your AI business assistant. I can help you:

📦 **INVENTORY MANAGEMENT:**
• Add, update, delete products
• Check stock levels and get alerts
• Manage your product catalog

📊 **BUSINESS REPORTS:**
• Daily, weekly, monthly sales reports  
• Revenue analytics and insights
• Top-selling products analysis

🚨 **SMART ALERTS:**
• Low stock notifications
• Sales performance updates
• Customer activity insights

💰 **FINANCIAL TRACKING:**
• Revenue summaries
• Order processing stats
• Profit margin analysis

**🎯 Quick Start Commands:**
• "Show my products" - View inventory
• "Add product [name] [price]" - Add new item
• "Daily report" - Today's performance
• "How are sales?" - Quick overview

**What would you like to do first?**"""

    elif user_type == "customer":
        message = """🛒 **Karibu to Sasabot Marketplace, I am AI assistant!**

I'm here to make your shopping experience amazing! I can help with:

🛍️ **PRODUCT DISCOVERY:**
• Browse our complete catalog
• Search for specific items
• Filter by price, category, brand
• Get product recommendations

💰 **SMART SHOPPING:**
• Compare prices and features
• Find the best deals
• Check product availability
• Get detailed product information

📱 **EASY ORDERING:**
• Add items to your cart
• Quick one-click purchases
• Track your orders
• Multiple payment options (M-Pesa, Cash)

🎯 **PERSONALIZED SERVICE:**
• Product recommendations based on your needs
• Customer support chat
• Order history and reordering

**🚀 Try these commands:**
• "Show me products" - Browse catalog
• "Search for phones" - Find specific items
• "What's under 30k?" - Price filtering
• "Best deals" - Current promotions

**What are you looking for today?**"""

    else:
        message = """🤖 **Karibu to Sasabot, I am AI assistant!**

I'm an AI assistant built for Kenyan businesses and their customers.

**🎯 Choose your experience:**

👨‍💼 **BUSINESS OWNERS** - Say "vendor" or "business owner"
• Manage your inventory and products
• Generate sales reports and analytics
• Get business insights and alerts
• Track performance and revenue

👥 **CUSTOMERS** - Say "customer" or "shopper"  
• Browse and search products
• Place orders with M-Pesa payments
• Track deliveries and order status
• Get customer support

**🇰🇪 Built for Kenya:**
• M-Pesa payment integration
• Local business workflows
• Swahili + English support
• Affordable for SMEs

**📱 Real Implementation:**
*This demo shows exactly how Sasabot works on WhatsApp for real businesses!*

**Just say "vendor" or "customer" to get started!**"""

    # FIXED: Return only the message string, not a dictionary
    return message


# =============================================================================
# INTENT RECOGNITION
# =============================================================================

parse_user_intent_def = {
    "name": "parse_user_intent",
    "description": "Understand what the user wants to do from their message",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "User's message to parse"
            },
            "user_type": {
                "type": "string",
                "description": "vendor or customer"
            },
            "conversation_context": {
                "type": "string",
                "description": "Previous conversation context",
                "default": ""
            }
        },
        "required": ["message", "user_type"]
    }
}

async def parse_user_intent_handler(message: str, user_type: str, conversation_context: str = ""):
    """Parse user intent from message"""
    message_lower = message.lower()
    
    # Common intents for both user types
    if any(word in message_lower for word in ["help", "assistance", "commands", "what can you do"]):
        return {"intent": "help_request", "confidence": 0.95, "parameters": {}}
    
    if any(word in message_lower for word in ["switch", "change role", "become customer", "become vendor"]):
        if "customer" in message_lower:
            return {"intent": "switch_role", "confidence": 0.9, "parameters": {"target_role": "customer"}}
        elif "vendor" in message_lower:
            return {"intent": "switch_role", "confidence": 0.9, "parameters": {"target_role": "vendor"}}
    
    if user_type == "vendor":
        # Product management intents
        if any(word in message_lower for word in ["add", "create", "new product"]):
            # Extract product details from message
            words = message.split()
            params = {}
            
            # Simple extraction (can be enhanced with NLP)
            if len(words) >= 3:
                params["product_name"] = words[2] if len(words) > 2 else ""
                # Look for price (numbers)
                for word in words:
                    if word.replace(',', '').replace('.', '').isdigit():
                        params["price"] = float(word.replace(',', ''))
                        break
            
            return {"intent": "add_product", "confidence": 0.9, "parameters": params}
        
        elif any(word in message_lower for word in ["show", "list", "view", "my products", "products", "inventory"]):
            return {"intent": "show_products", "confidence": 0.9, "parameters": {}}
        
        elif any(word in message_lower for word in ["update", "modify", "change", "edit product"]):
            return {"intent": "update_product", "confidence": 0.8, "parameters": {}}
        
        elif any(word in message_lower for word in ["delete", "remove", "drop product"]):
            return {"intent": "delete_product", "confidence": 0.8, "parameters": {}}
        
        elif any(word in message_lower for word in ["report", "sales", "revenue", "performance"]):
            period = "daily"
            if "weekly" in message_lower or "week" in message_lower:
                period = "weekly"
            elif "monthly" in message_lower or "month" in message_lower:
                period = "monthly"
            elif "quarterly" in message_lower or "quarter" in message_lower:
                period = "quarterly"
            elif "yearly" in message_lower or "year" in message_lower:
                period = "yearly"
            
            return {"intent": "generate_report", "confidence": 0.9, "parameters": {"period": period}}
        
        elif any(word in message_lower for word in ["stock", "inventory level", "low stock"]):
            return {"intent": "check_stock", "confidence": 0.9, "parameters": {}}
        
        elif any(word in message_lower for word in ["menu", "dashboard", "options"]):
            return {"intent": "show_vendor_menu", "confidence": 0.9, "parameters": {}}
    
    elif user_type == "customer":
        # Shopping intents
        if any(word in message_lower for word in ["show", "browse", "products", "catalog", "available"]):
            params = {}
            
            # Check for category filters
            if "electronics" in message_lower:
                params["category"] = "electronics"
            elif "accessories" in message_lower:
                params["category"] = "accessories"
            
            # Check for price filters
            if "under" in message_lower or "below" in message_lower:
                words = message.split()
                for i, word in enumerate(words):
                    if word in ["under", "below"] and i + 1 < len(words):
                        next_word = words[i + 1].replace('k', '000').replace(',', '')
                        if next_word.isdigit():
                            params["max_price"] = float(next_word)
                            break
            
            return {"intent": "browse_products", "confidence": 0.9, "parameters": params}
        
        elif any(word in message_lower for word in ["search", "find", "looking for"]):
            # Extract search term
            search_terms = ["search", "find", "looking for"]
            search_term = ""
            for term in search_terms:
                if term in message_lower:
                    parts = message_lower.split(term)
                    if len(parts) > 1:
                        search_term = parts[1].strip()
                        break
            
            return {"intent": "search_products", "confidence": 0.9, "parameters": {"search_term": search_term}}
        
        elif any(word in message_lower for word in ["buy", "purchase", "order", "want to buy"]):
            # Extract product name
            buy_terms = ["buy", "purchase", "order", "want to buy"]
            product_name = ""
            for term in buy_terms:
                if term in message_lower:
                    parts = message_lower.split(term)
                    if len(parts) > 1:
                        product_name = parts[1].strip()
                        break
            
            return {"intent": "buy_product", "confidence": 0.9, "parameters": {"product_name": product_name}}
        
        elif any(word in message_lower for word in ["add to cart", "add", "cart"]):
            return {"intent": "add_to_cart", "confidence": 0.8, "parameters": {}}
        
        elif any(word in message_lower for word in ["cart", "my cart", "view cart", "show cart"]):
            return {"intent": "view_cart", "confidence": 0.9, "parameters": {}}
        
        elif any(word in message_lower for word in ["track", "order status", "my order", "delivery"]):
            return {"intent": "track_order", "confidence": 0.9, "parameters": {}}
        
        elif any(word in message_lower for word in ["details", "info", "about", "how much"]):
            return {"intent": "product_details", "confidence": 0.8, "parameters": {}}
        
        elif any(word in message_lower for word in ["menu", "options", "what can i do"]):
            return {"intent": "show_customer_menu", "confidence": 0.9, "parameters": {}}
    
    # Default fallback
    return {"intent": "general_conversation", "confidence": 0.5, "parameters": {}}

# =============================================================================
# CONTEXT MANAGEMENT
# =============================================================================

maintain_context_def = {
    "name": "maintain_context",
    "description": "Keep track of ongoing conversation context",
    "parameters": {
        "type": "object",
        "properties": {
            "user_message": {
                "type": "string",
                "description": "Latest user message"
            },
            "ai_response": {
                "type": "string",
                "description": "AI's response"
            },
            "intent": {
                "type": "string",
                "description": "Detected intent"
            }
        },
        "required": ["user_message", "ai_response"]
    }
}

async def maintain_context_handler(user_message: str, ai_response: str, intent: str = ""):
    """Maintain conversation context"""
    # Get existing conversation history
    conversation_history = cl.user_session.get("conversation_history", [])
    
    # Add new exchange
    new_exchange = {
        "timestamp": cl.context.session.created_at.isoformat(),
        "user_message": user_message,
        "ai_response": ai_response,
        "intent": intent
    }
    
    conversation_history.append(new_exchange)
    
    # Keep only last 10 exchanges to avoid memory issues
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]
    
    cl.user_session.set("conversation_history", conversation_history)
    
    # Update conversation stats
    message_count = cl.user_session.get("message_count", 0) + 1
    cl.user_session.set("message_count", message_count)
    
    return {
        "success": True,
        "conversation_length": len(conversation_history),
        "total_messages": message_count,
        "last_intent": intent
    }

conversation_router_def = {
    "name": "conversation_router",
    "description": "Route conversation to appropriate handler based on intent",
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": "Detected user intent"
            },
            "parameters": {
                "type": "object",
                "description": "Intent parameters"
            },
            "user_type": {
                "type": "string",
                "description": "Current user type"
            }
        },
        "required": ["intent", "user_type"]
    }
}

async def conversation_router_handler(intent: str, user_type: str, parameters: dict = {}):
    """Route conversation to appropriate tool"""
    
    # Define routing mappings
    vendor_routes = {
        "add_product": "add_product",
        "show_products": "show_products", 
        "update_product": "update_product",
        "delete_product": "delete_product",
        "generate_report": "generate_report",
        "check_stock": "check_stock",
        "show_vendor_menu": "vendor_menu"
    }
    
    customer_routes = {
        "browse_products": "browse_products",
        "search_products": "search_products",
        "buy_product": "place_order",
        "add_to_cart": "add_to_cart",
        "view_cart": "view_cart",
        "track_order": "track_order",
        "product_details": "product_details",
        "show_customer_menu": "customer_menu"
    }
    
    # Universal routes
    universal_routes = {
        "help_request": "help_command",
        "switch_role": "switch_user_role"
    }
    
    # Determine which tool to use
    tool_to_call = None
    
    if intent in universal_routes:
        tool_to_call = universal_routes[intent]
    elif user_type == "vendor" and intent in vendor_routes:
        tool_to_call = vendor_routes[intent]
    elif user_type == "customer" and intent in customer_routes:
        tool_to_call = customer_routes[intent]
    
    if tool_to_call:
        return {
            "success": True,
            "tool_to_call": tool_to_call,
            "parameters": parameters,
            "routing_successful": True
        }
    else:
        return {
            "success": False,
            "tool_to_call": None,
            "message": f"No handler found for intent '{intent}' and user type '{user_type}'",
            "routing_successful": False
        }

# =============================================================================
# HELP SYSTEM
# =============================================================================

help_system_def = {
    "name": "help_system",
    "description": "Provide contextual help based on user type and situation",
    "parameters": {
        "type": "object",
        "properties": {
            "user_type": {
                "type": "string",
                "description": "Current user type"
            },
            "specific_topic": {
                "type": "string",
                "description": "Specific help topic requested"
            }
        },
        "required": ["user_type"]
    }
}

async def help_system_handler(user_type: str, specific_topic: str = ""):
    """Provide contextual help"""
    
    if specific_topic:
        # Specific help topics
        if specific_topic in ["orders", "ordering", "buy"]:
            return {
                "message": """🛒 **ORDERING HELP**

**How to place an order:**
1. Browse products: "Show products"
2. Add to cart: "Add [product] to cart" 
3. View cart: "View my cart"
4. Checkout: "Place order" or "Checkout"
5. Payment: Choose M-Pesa or Cash on Delivery

**Quick order:** "Buy [product name]" for instant purchase

**Track orders:** "Track my order" or "Order status"

Need more help? Just ask!"""
            }
        
        elif specific_topic in ["payments", "mpesa", "pay"]:
            return {
                "message": """💳 **PAYMENT HELP**

**M-Pesa Payment:**
1. Confirm your order
2. Choose "Pay with M-Pesa"
3. Enter your M-Pesa PIN when prompted
4. Receive confirmation SMS

**Cash on Delivery:**
• Pay when you receive your order
• Small delivery fee applies

**Payment is secure** - we use official M-Pesa integration

Questions? Ask "payment support"!"""
            }
    
    # General help by user type
    if user_type == "vendor":
        message = """🆘 **VENDOR HELP GUIDE**

**📦 Product Management:**
• "Add product [name] [price]" - Add new items
• "Show my products" - View inventory
• "Update product [name]" - Modify details
• "Delete product [name]" - Remove items
• "Check stock" - See low stock items

**📊 Business Reports:**
• "Daily report" - Today's performance
• "Weekly report" - 7-day summary
• "Monthly report" - 30-day overview
• "How are sales?" - Quick overview

**🔧 Quick Actions:**
• "Vendor menu" - See all options
• "Switch to customer" - Test customer view
• "Help [topic]" - Specific help

**💡 Natural Language:**
You can talk naturally! Say things like:
• "I need to add a new phone for 25000"
• "How did I do this week?"
• "Show me items that are running low"

**Need specific help?** Ask about: products, reports, inventory, or sales"""

    elif user_type == "customer":
        message = """🆘 **CUSTOMER HELP GUIDE**

**🛍️ Shopping:**
• "Show products" - Browse catalog
• "Search [item]" - Find specific products
• "Electronics" - Browse by category
• "Under 30k" - Filter by price
• "Details [product]" - Get product info

**🛒 Cart & Orders:**
• "Add [product] to cart" - Add items
• "View cart" - See cart contents
• "Buy [product]" - Quick purchase
• "Place order" - Checkout process
• "Track my order" - Order status

**💳 Payment & Support:**
• M-Pesa integration available
• Cash on delivery option
• "Customer support" - Get help
• "My orders" - Order history

**🎯 Smart Features:**
• "Recommend something" - Get suggestions
• "Best deals" - Current offers
• "Compare [A] vs [B]" - Product comparison

**💡 Talk Naturally:**
• "I'm looking for a good phone under 30k"
• "What laptops do you have?"
• "Add that Samsung phone to my cart"

**Need help with:** ordering, payments, delivery, or returns?"""

    else:
        message = """🆘 **SASABOT HELP**

**🎯 Getting Started:**
• Say "vendor" - Manage your business
• Say "customer" - Shop for products

**🏪 For Business Owners:**
• Manage inventory through chat
• Generate sales reports
• Get business insights
• Track performance

**🛒 For Customers:**
• Browse products easily
• Place orders with M-Pesa
• Track deliveries
• Get customer support

**🌟 Key Features:**
• Natural conversation - no commands to memorize
• M-Pesa payment integration
• Real-time inventory management
• Comprehensive business reports
• Smart product recommendations

**📱 Real Platform:**
This demo shows exactly how Sasabot works on WhatsApp for real Kenyan businesses!

**Choose your role to see it in action:**
• "vendor" - Business management
• "customer" - Shopping experience"""

    return {"message": message, "user_type": user_type, "topic": specific_topic}

# =============================================================================
# CONVERSATION TOOLS REGISTRY
# =============================================================================

conversation_tools = [
    (welcome_message_def, welcome_message_handler),
    (parse_user_intent_def, parse_user_intent_handler),
    (maintain_context_def, maintain_context_handler),
    (conversation_router_def, conversation_router_handler),
    (help_system_def, help_system_handler),
]