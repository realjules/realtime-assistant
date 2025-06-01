"""
Demo Data
Sample business and product data for demonstration purposes
"""

import chainlit as cl
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# =============================================================================
# DEMO BUSINESS DATA
# =============================================================================

DEMO_BUSINESSES = {
    "mama_jane_electronics": {
        "name": "Mama Jane's Electronics",
        "owner_phone": "+254700000001",
        "description": "Quality electronics and accessories in Nairobi",
        "location": "Nairobi, Kenya",
        "established": "2020-01-15",
        "products": [
            {
                "id": "1",
                "name": "Samsung Galaxy A54",
                "price": 35000,
                "stock": 8,
                "category": "Electronics",
                "description": "Latest Samsung smartphone with excellent camera and long battery life"
            },
            {
                "id": "2", 
                "name": "Dell Inspiron Laptop",
                "price": 55000,
                "stock": 3,
                "category": "Electronics",
                "description": "High-performance laptop perfect for work and study. Intel i5 processor, 8GB RAM"
            },
            {
                "id": "3",
                "name": "Sony Wireless Headphones",
                "price": 4500,
                "stock": 15,
                "category": "Accessories",
                "description": "Premium wireless headphones with noise cancellation and superior sound quality"
            },
            {
                "id": "4",
                "name": "iPhone 13",
                "price": 75000,
                "stock": 2,
                "category": "Electronics", 
                "description": "Apple iPhone 13 with advanced camera system and A15 Bionic chip"
            },
            {
                "id": "5",
                "name": "MacBook Air M1",
                "price": 120000,
                "stock": 1,
                "category": "Electronics",
                "description": "Apple MacBook Air with M1 chip. Ultra-fast performance and all-day battery"
            },
            {
                "id": "6",
                "name": "Bluetooth Speaker",
                "price": 2500,
                "stock": 20,
                "category": "Accessories",
                "description": "Portable Bluetooth speaker with excellent sound quality and waterproof design"
            },
            {
                "id": "7",
                "name": "Phone Charger Cable",
                "price": 500,
                "stock": 50,
                "category": "Accessories",
                "description": "Universal USB charging cable compatible with most smartphones"
            },
            {
                "id": "8",
                "name": "Tablet 10-inch",
                "price": 18000,
                "stock": 6,
                "category": "Electronics",
                "description": "Android tablet perfect for entertainment, reading, and light work"
            }
        ],
        "sales_data": {
            "daily": {
                "revenue": 85000,
                "orders": 4,
                "customers": 4,
                "top_product": "Samsung Galaxy A54"
            },
            "weekly": {
                "revenue": 520000,
                "orders": 22,
                "customers": 18,
                "top_product": "Dell Inspiron Laptop"
            },
            "monthly": {
                "revenue": 2100000,
                "orders": 89,
                "customers": 67,
                "top_product": "Sony Wireless Headphones"
            },
            "quarterly": {
                "revenue": 6300000,
                "orders": 245,
                "customers": 189,
                "top_product": "Samsung Galaxy A54"
            },
            "yearly": {
                "revenue": 24500000,
                "orders": 892,
                "customers": 543,
                "top_product": "Bluetooth Speaker"
            }
        },
        "business_metrics": {
            "customer_satisfaction": 4.7,
            "average_order_value": 21250,
            "repeat_customer_rate": 0.35,
            "inventory_turnover": 8.2
        }
    },
    
    "pete_tech_store": {
        "name": "Pete's Tech Paradise",
        "owner_phone": "+254700000002", 
        "description": "Your one-stop shop for all tech needs",
        "location": "Mombasa, Kenya",
        "established": "2019-08-20",
        "products": [
            {
                "id": "101",
                "name": "Gaming Laptop",
                "price": 95000,
                "stock": 2,
                "category": "Electronics",
                "description": "High-end gaming laptop with dedicated graphics card and RGB keyboard"
            },
            {
                "id": "102",
                "name": "Wireless Mouse",
                "price": 1500,
                "stock": 25,
                "category": "Accessories",
                "description": "Ergonomic wireless mouse with precision tracking"
            },
            {
                "id": "103",
                "name": "External Hard Drive 1TB",
                "price": 6500,
                "stock": 12,
                "category": "Storage",
                "description": "Portable external hard drive for backup and extra storage"
            }
        ],
        "sales_data": {
            "daily": {"revenue": 47500, "orders": 2, "customers": 2},
            "weekly": {"revenue": 285000, "orders": 12, "customers": 10},
            "monthly": {"revenue": 1140000, "orders": 48, "customers": 39}
        }
    }
}

# =============================================================================
# SAMPLE ORDERS DATA
# =============================================================================

SAMPLE_ORDERS = [
    {
        "id": "ORD001",
        "customer_name": "John Kamau",
        "customer_phone": "+254701234567",
        "product": "Samsung Galaxy A54",
        "quantity": 1,
        "amount": 35000,
        "status": "delivered",
        "business_id": "mama_jane_electronics",
        "created_at": "2024-01-15T10:30:00",
        "delivery_address": "Westlands, Nairobi"
    },
    {
        "id": "ORD002", 
        "customer_name": "Mary Wanjiku",
        "customer_phone": "+254702345678",
        "product": "Dell Inspiron Laptop",
        "quantity": 1,
        "amount": 55000,
        "status": "shipped",
        "business_id": "mama_jane_electronics",
        "created_at": "2024-01-16T14:15:00",
        "delivery_address": "Karen, Nairobi"
    },
    {
        "id": "ORD003",
        "customer_name": "Peter Ochieng",
        "customer_phone": "+254703456789",
        "product": "Sony Wireless Headphones",
        "quantity": 2,
        "amount": 9000,
        "status": "processing",
        "business_id": "mama_jane_electronics", 
        "created_at": "2024-01-16T16:45:00",
        "delivery_address": "Kilimani, Nairobi"
    },
    {
        "id": "ORD004",
        "customer_name": "Grace Nyong",
        "customer_phone": "+254704567890",
        "product": "iPhone 13",
        "quantity": 1,
        "amount": 75000,
        "status": "confirmed",
        "business_id": "mama_jane_electronics",
        "created_at": "2024-01-17T09:20:00",
        "delivery_address": "Kileleshwa, Nairobi"
    },
    {
        "id": "ORD005",
        "customer_name": "David Mwangi",
        "customer_phone": "+254705678901",
        "product": "Bluetooth Speaker",
        "quantity": 3,
        "amount": 7500,
        "status": "pending",
        "business_id": "mama_jane_electronics",
        "created_at": "2024-01-17T11:10:00",
        "delivery_address": "Eastleigh, Nairobi"
    }
]

# =============================================================================
# CUSTOMER DATA
# =============================================================================

SAMPLE_CUSTOMERS = [
    {
        "id": "CUST001",
        "name": "John Kamau",
        "phone": "+254701234567",
        "email": "john.kamau@email.com",
        "location": "Westlands, Nairobi",
        "total_orders": 5,
        "total_spent": 145000,
        "last_order": "2024-01-15",
        "preferred_categories": ["Electronics", "Accessories"]
    },
    {
        "id": "CUST002", 
        "name": "Mary Wanjiku",
        "phone": "+254702345678",
        "email": "mary.wanjiku@email.com",
        "location": "Karen, Nairobi",
        "total_orders": 3,
        "total_spent": 89000,
        "last_order": "2024-01-16",
        "preferred_categories": ["Electronics"]
    },
    {
        "id": "CUST003",
        "name": "Peter Ochieng", 
        "phone": "+254703456789",
        "email": "peter.ochieng@email.com",
        "location": "Kilimani, Nairobi",
        "total_orders": 2,
        "total_spent": 39500,
        "last_order": "2024-01-16",
        "preferred_categories": ["Accessories", "Storage"]
    }
]

# =============================================================================
# DEMO DATA TOOLS
# =============================================================================

load_demo_data_def = {
    "name": "load_demo_data",
    "description": "Initialize sample business and product data for demo",
    "parameters": {
        "type": "object",
        "properties": {
            "include_sample_orders": {
                "type": "boolean",
                "description": "Include sample order history",
                "default": True
            }
        },
        "required": []
    }
}

async def load_demo_data_handler(include_sample_orders: bool = True):
    """Load demo business data"""
    businesses_loaded = len(DEMO_BUSINESSES)
    total_products = sum(len(biz["products"]) for biz in DEMO_BUSINESSES.values())
    total_orders = len(SAMPLE_ORDERS) if include_sample_orders else 0
    
    # Calculate total inventory value
    total_inventory_value = 0
    for business in DEMO_BUSINESSES.values():
        for product in business["products"]:
            total_inventory_value += product["price"] * product["stock"]
    
    message = f"""🎯 **DEMO DATA LOADED SUCCESSFULLY**

🏪 **BUSINESSES:** {businesses_loaded} active businesses
• Mama Jane's Electronics (Nairobi)
• Pete's Tech Paradise (Mombasa)

📦 **INVENTORY:**
• Total Products: {total_products} items
• Total Value: KSh {total_inventory_value:,.0f}
• Categories: Electronics, Accessories, Storage

📋 **SAMPLE ORDERS:** {total_orders} orders
• Various order statuses (pending to delivered)
• Realistic customer data
• M-Pesa payment records

💰 **SALES DATA:**
• Daily, weekly, monthly reports available
• Revenue analytics and trends
• Customer behavior insights

🇰🇪 **KENYAN CONTEXT:**
• Pricing in KSh (Kenyan Shillings)
• Local business names and locations
• Realistic product catalog for Kenyan market

**✅ Demo is ready!** Try vendor or customer commands to explore the full system."""

    # Store demo status in session
    cl.user_session.set("demo_data_loaded", True)
    cl.user_session.set("demo_load_time", datetime.now().isoformat())
    
    return {
        "message": message,
        "businesses_count": businesses_loaded,
        "products_count": total_products,
        "orders_count": total_orders,
        "inventory_value": total_inventory_value,
        "demo_ready": True
    }

demo_explanation_def = {
    "name": "demo_explanation", 
    "description": "Explain how the real WhatsApp version works",
    "parameters": {
        "type": "object",
        "properties": {
            "focus_area": {
                "type": "string",
                "enum": ["overview", "vendor_features", "customer_features", "technical", "business_value"],
                "description": "Specific area to focus explanation on",
                "default": "overview"
            }
        },
        "required": []
    }
}

async def demo_explanation_handler(focus_area: str = "overview"):
    """Explain the real WhatsApp implementation"""
    
    explanations = {
        "overview": """🌟 **HOW SASABOT WORKS ON WHATSAPP**

**📱 Real Implementation:**
• Business owners chat with Sasabot via WhatsApp Business
• Customers text the business WhatsApp number
• AI handles ALL conversations automatically 24/7
• No apps to download - just use WhatsApp!

**🏪 For Business Owners:**
• Complete business management through chat
• Voice messages supported (Swahili + English)
• Real-time notifications and alerts
• Works on any phone - smartphone or basic

**🛒 For Customers:**
• Natural shopping conversations
• M-Pesa payments integrated
• Order tracking via WhatsApp
• Customer support always available

**🇰🇪 Built for Kenya:**
• M-Pesa STK Push integration
• Swahili language support
• Local business workflows
• Affordable pricing for SMEs

**This demo shows the EXACT experience - imagine it happening in WhatsApp!**""",

        "business_value": """💼 **BUSINESS VALUE PROPOSITION**

**💰 COST SAVINGS:**
• 80% reduction in customer service costs
• No need for separate e-commerce platform
• Eliminate manual order processing
• Reduce inventory management overhead

**📈 REVENUE GROWTH:**
• 24/7 availability increases sales
• Personalized recommendations boost AOV
• Faster order processing
• Reduced cart abandonment

**🎯 COMPETITIVE ADVANTAGE:**
• First-mover advantage in AI business automation
• Superior customer experience
• Data-driven business insights
• Scalable operations

**🇰🇪 KENYAN MARKET FIT:**
• 90%+ WhatsApp penetration in Kenya
• M-Pesa ubiquity for payments
• Language localization
• SME-focused features and pricing

**📊 MEASURABLE RESULTS:**
• Average 40% increase in sales
• 60% reduction in response time
• 95% customer satisfaction
• 3x faster order processing"""
    }
    
    message = explanations.get(focus_area, explanations["overview"])
    
    return {
        "message": message,
        "focus_area": focus_area,
        "is_demo": True,
        "real_platform": "WhatsApp"
    }

# =============================================================================
# DEMO TOOLS REGISTRY
# =============================================================================

demo_tools = [
    (load_demo_data_def, load_demo_data_handler),
    (demo_explanation_def, demo_explanation_handler),
]