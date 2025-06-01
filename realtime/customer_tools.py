"""
Customer Tools
All customer shopping functionality including product browsing, orders, and support
"""

import chainlit as cl
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import demo data
from .demo_data import DEMO_BUSINESSES, SAMPLE_ORDERS

# =============================================================================
# CUSTOMER DASHBOARD
# =============================================================================

customer_menu_def = {
    "name": "customer_menu",
    "description": "Show customer shopping menu with available options",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

async def customer_menu_handler():
    """Show customer menu options"""
    menu = """🛒 **WELCOME TO SASABOT MARKETPLACE**

**🛍️ BROWSE & DISCOVER:**
• "Show products" - View all available items
• "Electronics" - Browse electronics category
• "Under 30k" - Products below KSh 30,000
• "Search [product name]" - Find specific items
• "What's new?" - Latest arrivals
• "Best deals" - Current promotions

**💳 SHOPPING & ORDERS:**
• "Buy [product name]" - Quick purchase
• "Add to cart [product]" - Add to shopping cart
• "View my cart" - See cart contents
• "Place order" - Checkout process
• "Track my order" - Order status

**💰 PRICING & SUPPORT:**
• "How much is [product]?" - Check prices
• "Compare [product1] vs [product2]" - Price comparison
• "Customer support" - Get help
• "My order history" - Past purchases

**🎯 QUICK ACTIONS:**
• "Recommend something" - Personalized suggestions
• "Popular products" - Trending items

**What are you looking for today?**"""

    return {"menu": menu, "options_count": 16}

# =============================================================================
# PRODUCT BROWSING
# =============================================================================

browse_products_def = {
    "name": "browse_products",
    "description": "Show products available for customers to purchase",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Product category filter",
                "default": "all"
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price filter"
            },
            "min_price": {
                "type": "number",
                "description": "Minimum price filter"
            },
            "sort_by": {
                "type": "string",
                "enum": ["price_low", "price_high", "name", "stock"],
                "description": "Sort products by",
                "default": "name"
            }
        },
        "required": []
    }
}

async def browse_products_handler(category: str = "all", max_price: float = None, min_price: float = None, sort_by: str = "name"):
    """Show available products for customers"""
    all_products = []
    
    # Collect products from all businesses
    for business_id, business_data in DEMO_BUSINESSES.items():
        for product in business_data["products"]:
            if product["stock"] > 0:  # Only show in-stock items
                product_copy = product.copy()
                product_copy["business_name"] = business_data["name"]
                product_copy["business_id"] = business_id
                all_products.append(product_copy)
    
    # Apply filters
    filtered_products = all_products
    
    if category != "all":
        filtered_products = [p for p in filtered_products if category.lower() in p.get("category", "").lower()]
    
    if max_price:
        filtered_products = [p for p in filtered_products if p["price"] <= max_price]
    
    if min_price:
        filtered_products = [p for p in filtered_products if p["price"] >= min_price]
    
    # Sort products
    if sort_by == "price_low":
        filtered_products.sort(key=lambda x: x["price"])
    elif sort_by == "price_high":
        filtered_products.sort(key=lambda x: x["price"], reverse=True)
    elif sort_by == "stock":
        filtered_products.sort(key=lambda x: x["stock"], reverse=True)
    else:  # name
        filtered_products.sort(key=lambda x: x["name"])
    
    if not filtered_products:
        filter_desc = []
        if category != "all":
            filter_desc.append(f"category '{category}'")
        if max_price:
            filter_desc.append(f"under KSh {max_price:,.0f}")
        if min_price:
            filter_desc.append(f"above KSh {min_price:,.0f}")
        
        filter_text = " and ".join(filter_desc) if filter_desc else "your criteria"
        return {"message": f"😕 No products found matching {filter_text}. Try browsing all products!", "products": []}
    
    # Build product listing
    header = "🛒 **AVAILABLE PRODUCTS**"
    if category != "all":
        header += f" - {category.title()} Category"
    if max_price or min_price:
        price_range = ""
        if min_price and max_price:
            price_range = f" (KSh {min_price:,.0f} - {max_price:,.0f})"
        elif max_price:
            price_range = f" (Under KSh {max_price:,.0f})"
        elif min_price:
            price_range = f" (Above KSh {min_price:,.0f})"
        header += price_range
    
    product_list = [header + "\n"]
    
    for i, product in enumerate(filtered_products, 1):
        # Stock availability indicator
        if product["stock"] > 10:
            availability = "✅ In Stock"
        elif product["stock"] > 5:
            availability = f"📦 {product['stock']} available"
        else:
            availability = f"⚠️ Only {product['stock']} left!"
        
        product_list.append(
            f"**{i}. {product['name']}**\n"
            f"   💰 KSh {product['price']:,.0f}\n"
            f"   🏪 {product['business_name']}\n"
            f"   📦 {availability}\n"
        )
        
        # Add description if available
        if product.get("description"):
            product_list.append(f"   📝 {product['description']}\n")
    
    footer = f"\n💬 **To order:** Say 'Buy [product name]' or 'How much is [product]?'\n🛒 **Add to cart:** Say 'Add [product] to cart'"
    message = "\n".join(product_list) + footer
    
    return {
        "message": message,
        "products": filtered_products,
        "total_found": len(filtered_products),
        "filters_applied": {"category": category, "max_price": max_price, "min_price": min_price}
    }

search_products_def = {
    "name": "search_products",
    "description": "Search for specific products by name or description",
    "parameters": {
        "type": "object",
        "properties": {
            "search_term": {
                "type": "string",
                "description": "Product name or description to search for"
            }
        },
        "required": ["search_term"]
    }
}

async def search_products_handler(search_term: str):
    """Search for products"""
    all_products = []
    
    # Collect all products
    for business_id, business_data in DEMO_BUSINESSES.items():
        for product in business_data["products"]:
            if product["stock"] > 0:
                product_copy = product.copy()
                product_copy["business_name"] = business_data["name"]
                all_products.append(product_copy)
    
    # Search in name and description
    search_lower = search_term.lower()
    matching_products = []
    
    for product in all_products:
        if (search_lower in product["name"].lower() or 
            search_lower in product.get("description", "").lower() or
            search_lower in product.get("category", "").lower()):
            matching_products.append(product)
    
    if not matching_products:
        return {
            "message": f"🔍 No products found for '{search_term}'\n\n💡 **Try searching for:**\n• Phone, Laptop, Headphones\n• Electronics, Accessories\n• Or browse all products",
            "products": []
        }
    
    product_list = [f"🔍 **Search Results for '{search_term}'** ({len(matching_products)} found)\n"]
    
    for i, product in enumerate(matching_products, 1):
        availability = "✅ Available" if product["stock"] > 5 else f"⚠️ Only {product['stock']} left"
        
        product_list.append(
            f"**{i}. {product['name']}**\n"
            f"   💰 KSh {product['price']:,.0f}\n"
            f"   🏪 {product['business_name']}\n"
            f"   📦 {availability}\n"
        )
    
    footer = "\n💬 Say 'Buy [product name]' to purchase or 'Details [product]' for more info"
    message = "\n".join(product_list) + footer
    
    return {
        "message": message,
        "products": matching_products,
        "search_term": search_term,
        "results_count": len(matching_products)
    }

product_details_def = {
    "name": "product_details",
    "description": "Get detailed information about a specific product",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Name of product to get details for"
            }
        },
        "required": ["product_name"]
    }
}

async def product_details_handler(product_name: str):
    """Get detailed product information"""
    # Search for product across all businesses
    for business_id, business_data in DEMO_BUSINESSES.items():
        for product in business_data["products"]:
            if product_name.lower() in product["name"].lower():
                # Stock status with detailed info
                if product["stock"] == 0:
                    stock_status = "❌ Out of Stock"
                    stock_detail = "This item is currently unavailable"
                elif product["stock"] < 3:
                    stock_status = f"⚠️ Limited Stock"
                    stock_detail = f"Only {product['stock']} units remaining - order soon!"
                elif product["stock"] < 10:
                    stock_status = f"📦 {product['stock']} Available"
                    stock_detail = f"{product['stock']} units in stock"
                else:
                    stock_status = "✅ In Stock"
                    stock_detail = "Plenty available"
                
                # Calculate potential savings or value
                similar_price_range = f"KSh {product['price'] * 0.9:,.0f} - {product['price'] * 1.1:,.0f}"
                
                message = f"""📱 **{product['name']} - Product Details**

💰 **Price:** KSh {product['price']:,.0f}
🏷️ **Category:** {product.get('category', 'General')}
📦 **Availability:** {stock_status}
🔍 **Stock Info:** {stock_detail}
🏪 **Seller:** {business_data['name']}

📝 **Description:**
{product.get('description', 'Quality product with reliable performance')}

💡 **Price Range:** Similar products cost {similar_price_range}

{"🛒 **Ready to order?** Say 'Buy " + product['name'] + "' or 'Add " + product['name'] + " to cart'" if product['stock'] > 0 else "😔 This item is currently out of stock. Try browsing similar products."}

❓ **Need help?** Ask about delivery, warranty, or payment options!"""

                return {
                    "message": message,
                    "product": product,
                    "business": business_data['name'],
                    "available": product['stock'] > 0,
                    "stock_level": product['stock']
                }
    
    return {
        "message": f"❌ Sorry, I couldn't find '{product_name}'. \n\n🔍 **Try:**\n• Check spelling\n• Search for similar products\n• Browse our catalog",
        "product": None,
        "available": False
    }

# =============================================================================
# SHOPPING CART
# =============================================================================

add_to_cart_def = {
    "name": "add_to_cart",
    "description": "Add product to customer's shopping cart",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Name of product to add to cart"
            },
            "quantity": {
                "type": "integer",
                "description": "Quantity to add",
                "default": 1
            }
        },
        "required": ["product_name"]
    }
}

async def add_to_cart_handler(product_name: str, quantity: int = 1):
    """Add product to cart"""
    # Find the product
    found_product = None
    business_name = None
    
    for business_id, business_data in DEMO_BUSINESSES.items():
        for product in business_data["products"]:
            if product_name.lower() in product["name"].lower():
                found_product = product
                business_name = business_data["name"]
                break
        if found_product:
            break
    
    if not found_product:
        return {
            "success": False,
            "message": f"❌ Product '{product_name}' not found. Try browsing our catalog first."
        }
    
    if found_product["stock"] < quantity:
        return {
            "success": False,
            "message": f"❌ Sorry, only {found_product['stock']} units of {found_product['name']} available."
        }
    
    # Get or create cart
    cart = cl.user_session.get("cart_items", [])
    
    # Check if product already in cart
    for item in cart:
        if item["product_id"] == found_product["id"]:
            new_quantity = item["quantity"] + quantity
            if new_quantity > found_product["stock"]:
                return {
                    "success": False,
                    "message": f"❌ Cannot add {quantity} more. You already have {item['quantity']} in cart. Stock: {found_product['stock']}"
                }
            item["quantity"] = new_quantity
            break
    else:
        # Add new item to cart
        cart_item = {
            "product_id": found_product["id"],
            "product_name": found_product["name"],
            "price": found_product["price"],
            "quantity": quantity,
            "business_name": business_name
        }
        cart.append(cart_item)
    
    cl.user_session.set("cart_items", cart)
    
    total_items = sum(item["quantity"] for item in cart)
    cart_total = sum(item["price"] * item["quantity"] for item in cart)
    
    return {
        "success": True,
        "message": f"🛒 **Added to Cart!**\n\n✅ {found_product['name']} x{quantity}\n💰 KSh {found_product['price']:,.0f} each\n\n📦 **Cart Summary:**\n• {total_items} items total\n💳 Total: KSh {cart_total:,.0f}\n\n💬 Say 'View cart' to see all items or 'Checkout' to place order!",
        "cart_total": cart_total,
        "total_items": total_items
    }

view_cart_def = {
    "name": "view_cart",
    "description": "Show customer's shopping cart contents",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

async def view_cart_handler():
    """View shopping cart"""
    cart = cl.user_session.get("cart_items", [])
    
    if not cart:
        return {
            "message": "🛒 **Your cart is empty**\n\n🛍️ Start shopping by saying:\n• 'Show products'\n• 'Search [product name]'\n• 'Browse electronics'",
            "cart_empty": True
        }
    
    cart_list = ["🛒 **YOUR SHOPPING CART**\n"]
    total_amount = 0
    total_items = 0
    
    for i, item in enumerate(cart, 1):
        item_total = item["price"] * item["quantity"]
        total_amount += item_total
        total_items += item["quantity"]
        
        cart_list.append(
            f"**{i}. {item['product_name']}**\n"
            f"   💰 KSh {item['price']:,.0f} x {item['quantity']} = KSh {item_total:,.0f}\n"
            f"   🏪 {item['business_name']}\n"
        )
    
    summary = f"""💳 **CART SUMMARY:**
• Total Items: {total_items}
• Total Amount: KSh {total_amount:,.0f}

🎯 **Next Steps:**
• "Checkout" - Place your order
• "Remove [product]" - Remove item
• "Clear cart" - Empty cart
• "Continue shopping" - Browse more products"""
    
    message = "\n".join(cart_list) + "\n" + summary
    
    return {
        "message": message,
        "cart_items": cart,
        "total_amount": total_amount,
        "total_items": total_items,
        "cart_empty": False
    }

# =============================================================================
# ORDER PROCESSING
# =============================================================================

place_order_def = {
    "name": "place_order",
    "description": "Create an order for customer (from cart or direct purchase)",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Single product to order (if not using cart)"
            },
            "quantity": {
                "type": "integer",
                "description": "Quantity for single product order",
                "default": 1
            },
            "use_cart": {
                "type": "boolean",
                "description": "Use items from cart for order",
                "default": True
            }
        },
        "required": []
    }
}

async def place_order_handler(product_name: str = None, quantity: int = 1, use_cart: bool = True):
    """Create customer order"""
    order_items = []
    
    if use_cart and not product_name:
        # Use cart items
        cart = cl.user_session.get("cart_items", [])
        if not cart:
            return {
                "success": False,
                "message": "🛒 Your cart is empty! Add products first or specify a product to buy directly."
            }
        order_items = cart.copy()
    
    elif product_name:
        # Direct product order
        found_product = None
        business_name = None
        
        for business_id, business_data in DEMO_BUSINESSES.items():
            for product in business_data["products"]:
                if product_name.lower() in product["name"].lower():
                    found_product = product
                    business_name = business_data["name"]
                    break
            if found_product:
                break
        
        if not found_product:
            return {
                "success": False,
                "message": f"❌ Product '{product_name}' not found."
            }
        
        if found_product["stock"] < quantity:
            return {
                "success": False,
                "message": f"❌ Sorry, only {found_product['stock']} units available."
            }
        
        order_items = [{
            "product_id": found_product["id"],
            "product_name": found_product["name"],
            "price": found_product["price"],
            "quantity": quantity,
            "business_name": business_name
        }]
    
    else:
        return {
            "success": False,
            "message": "❌ Please specify a product or add items to cart first."
        }
    
    # Calculate order total
    total_amount = sum(item["price"] * item["quantity"] for item in order_items)
    order_id = f"ORD{random.randint(1000, 9999)}"
    
    # Create order summary
    order_summary = [f"🛒 **ORDER CREATED - {order_id}**\n"]
    
    for item in order_items:
        item_total = item["price"] * item["quantity"]
        order_summary.append(
            f"📱 {item['product_name']}\n"
            f"   🔢 Quantity: {item['quantity']}\n"
            f"   💰 KSh {item['price']:,.0f} x {item['quantity']} = KSh {item_total:,.0f}\n"
        )
    
    order_summary.append(f"💳 **Total Amount: KSh {total_amount:,.0f}**")
    
    # Payment and delivery info
    payment_info = f"""
📋 **ORDER DETAILS:**
• Order ID: {order_id}
• Items: {len(order_items)} products
• Total: KSh {total_amount:,.0f}

📱 **PAYMENT OPTIONS:**
• M-Pesa: Pay via mobile money
• Cash on Delivery: Pay when you receive

🚚 **DELIVERY:**
• Same day delivery in Nairobi
• 1-2 days other areas
• Delivery fee: KSh 200

**To confirm order, say: "CONFIRM ORDER {order_id}"**
**To pay now: "PAY WITH MPESA"**"""
    
    message = "\n".join(order_summary) + payment_info
    
    # Store order in session
    cl.user_session.set("pending_order", {
        "order_id": order_id,
        "items": order_items,
        "total": total_amount,
        "status": "pending_confirmation",
        "created_at": datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "message": message,
        "order_id": order_id,
        "total": total_amount,
        "items_count": len(order_items)
    }

track_order_def = {
    "name": "track_order",
    "description": "Track customer order status",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order ID to track (optional, will use latest if not provided)"
            }
        },
        "required": []
    }
}

async def track_order_handler(order_id: str = None):
    """Track order status"""
    if order_id:
        # Look for specific order in sample orders
        for order in SAMPLE_ORDERS:
            if order_id.upper() in order["id"]:
                status_emoji = {
                    "pending": "⏳",
                    "confirmed": "✅",
                    "processing": "📦",
                    "shipped": "🚚",
                    "delivered": "✅",
                    "cancelled": "❌"
                }
                
                message = f"""📋 **ORDER TRACKING - {order['id']}**

📱 **Product:** {order['product']}
👤 **Customer:** {order['customer']}
💰 **Amount:** KSh {order['amount']:,.0f}
📊 **Status:** {status_emoji.get(order['status'], '📋')} {order['status'].title()}

🚚 **Delivery Updates:**"""
                
                if order['status'] == 'delivered':
                    message += "\n✅ Order delivered successfully!"
                elif order['status'] == 'shipped':
                    message += "\n🚚 Your order is on the way! Expected delivery: Today"
                elif order['status'] == 'processing':
                    message += "\n📦 Order is being prepared for shipment"
                elif order['status'] == 'confirmed':
                    message += "\n✅ Order confirmed. Processing will begin shortly"
                else:
                    message += "\n⏳ Order received, awaiting confirmation"
                
                message += "\n\n📞 **Need help?** Contact customer support"
                
                return {
                    "message": message,
                    "order": order,
                    "found": True
                }
    
    # Check for pending order in session
    pending_order = cl.user_session.get("pending_order")
    if pending_order:
        message = f"""📋 **YOUR LATEST ORDER - {pending_order['order_id']}**

📦 **Items:** {len(pending_order['items'])} products
💰 **Total:** KSh {pending_order['total']:,.0f}
📊 **Status:** ⏳ {pending_order['status'].replace('_', ' ').title()}

🎯 **Next Steps:**
• Confirm your order
• Choose payment method
• Provide delivery address

Say "CONFIRM ORDER" to proceed!"""
        
        return {
            "message": message,
            "order": pending_order,
            "found": True
        }
    
    return {
        "message": "❌ No orders found.\n\n🛒 **Start shopping:**\n• Browse products\n• Add items to cart\n• Place your first order",
        "found": False
    }

# =============================================================================
# CUSTOMER TOOLS REGISTRY
# =============================================================================

customer_tools = [
    (customer_menu_def, customer_menu_handler),
    (browse_products_def, browse_products_handler),
    (search_products_def, search_products_handler),
    (product_details_def, product_details_handler),
    (add_to_cart_def, add_to_cart_handler),
    (view_cart_def, view_cart_handler),
    (place_order_def, place_order_handler),
    (track_order_def, track_order_handler),
]