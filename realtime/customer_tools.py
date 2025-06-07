"""
Customer Tools - Updated to use JSON Database
These tools allow customers to browse products, search, and place orders
All data now loads from and saves to JSON files
"""

import json
from typing import Dict, Any, List
from utils.simple_db import db
from datetime import datetime

from .payment_tools import (
    initiate_mpesa_payment_handler, check_payment_status_handler,
    get_payment_help_handler, retry_payment_handler
)


def browse_products_handler(params: Dict[str, Any]) -> str:
    """
    Allow customers to browse available products from all businesses
    Now loads fresh data from JSON files
    """
    try:
        # Load fresh products from JSON database
        all_products = db.get_products()
        businesses = db.get_businesses()
        
        if not all_products:
            return "🛍️ No products available at the moment. Please check back later!"
        
        # Filter out products with zero stock or inactive status
        available_products = [
            p for p in all_products 
            if p.get('stock', 0) > 0 and p.get('status', 'active') == 'active'
        ]
        
        if not available_products:
            return "🛍️ All products are currently out of stock. Please check back later!"
        
        # Group products by business for better organization
        products_by_business = {}
        for product in available_products:
            business_id = product.get('business_id', 'unknown')
            if business_id not in products_by_business:
                products_by_business[business_id] = []
            products_by_business[business_id].append(product)
        
        result = "🛍️ **BROWSE PRODUCTS** 🛍️\n\n"
        
        # Display products grouped by business
        for business_id, products in products_by_business.items():
            business = businesses.get(business_id, {})
            business_name = business.get('name', 'Unknown Business')
            business_location = business.get('location', 'Unknown Location')
            
            result += f"🏪 **{business_name}** ({business_location})\n"
            result += f"📞 {business.get('phone', 'No phone')}\n"
            result += "─" * 50 + "\n"
            
            # Sort products by category, then by price
            products.sort(key=lambda x: (x.get('category', ''), x.get('price', 0)))
            
            current_category = None
            for product in products:
                category = product.get('category', 'Other')
                
                # Show category header if it changed
                if category != current_category:
                    result += f"\n📂 **{category}**\n"
                    current_category = category
                
                # Format product info
                name = product.get('name', 'Unknown Product')
                price = product.get('price', 0)
                stock = product.get('stock', 0)
                brand = product.get('brand', '')
                warranty = product.get('warranty', '')
                
                result += f"   🔹 **{name}**"
                if brand:
                    result += f" ({brand})"
                result += f"\n      💰 KSh {price:,}"
                result += f" | 📦 {stock} in stock"
                if warranty:
                    result += f" | 🛡️ {warranty} warranty"
                result += f"\n      🆔 Product ID: {product.get('id', 'N/A')}\n"
                
                # Add description if available
                description = product.get('description', '')
                if description:
                    # Truncate long descriptions
                    if len(description) > 80:
                        description = description[:77] + "..."
                    result += f"      📝 {description}\n"
                
                result += "\n"
            
            result += "\n" + "="*60 + "\n\n"
        
        # Add helpful instructions
        result += "💡 **How to Order:**\n"
        result += "1. Note the Product ID of items you want\n"
        result += "2. Use the 'Search Products' tool to find specific items\n"
        result += "3. Use the 'Place Order' tool with product IDs and quantities\n\n"
        
        result += f"📊 **Summary:** {len(available_products)} products available from {len(products_by_business)} businesses\n"
        result += f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return result
        
    except Exception as e:
        return f"❌ Error browsing products: {str(e)}\nPlease try again or contact support."


def search_products_handler(params: Dict[str, Any]) -> str:
    """
    Search for products by name, category, or price range
    Now searches through current JSON data
    """
    try:
        query = params.get('query', '').strip().lower()
        max_price = params.get('max_price')
        category = params.get('category', '').strip().lower()
        business_id = params.get('business_id', '').strip()
        
        if not query and not max_price and not category and not business_id:
            return "❌ Please provide at least one search criteria:\n- query: product name to search\n- max_price: maximum price\n- category: product category\n- business_id: specific business"
        
        # Load fresh products from JSON database
        all_products = db.get_products()
        businesses = db.get_businesses()
        
        if not all_products:
            return "🔍 No products available to search."
        
        # Filter products based on search criteria
        matching_products = []
        
        for product in all_products:
            # Skip out of stock or inactive products
            if product.get('stock', 0) <= 0 or product.get('status', 'active') != 'active':
                continue
            
            matches = True
            
            # Search by name/description
            if query:
                product_name = product.get('name', '').lower()
                product_desc = product.get('description', '').lower()
                product_brand = product.get('brand', '').lower()
                
                if not (query in product_name or query in product_desc or query in product_brand):
                    matches = False
            
            # Filter by max price
            if max_price is not None:
                try:
                    if product.get('price', 0) > float(max_price):
                        matches = False
                except ValueError:
                    pass
            
            # Filter by category
            if category:
                product_category = product.get('category', '').lower()
                if category not in product_category:
                    matches = False
            
            # Filter by business
            if business_id:
                if product.get('business_id', '') != business_id:
                    matches = False
            
            if matches:
                matching_products.append(product)
        
        if not matching_products:
            return f"🔍 No products found matching your search criteria.\n\n💡 Try:\n- Different keywords\n- Higher price limit\n- Different category\n- Browse all products to see what's available"
        
        # Sort results by relevance (name match first, then price)
        if query:
            matching_products.sort(key=lambda x: (
                0 if query in x.get('name', '').lower() else 1,
                x.get('price', 0)
            ))
        else:
            matching_products.sort(key=lambda x: x.get('price', 0))
        
        result = "🔍 **SEARCH RESULTS** 🔍\n\n"
        
        # Show search criteria
        criteria = []
        if query:
            criteria.append(f"Query: '{query}'")
        if max_price:
            criteria.append(f"Max Price: KSh {max_price:,}")
        if category:
            criteria.append(f"Category: '{category}'")
        if business_id:
            business_name = businesses.get(business_id, {}).get('name', business_id)
            criteria.append(f"Business: {business_name}")
        
        result += f"📋 Search criteria: {' | '.join(criteria)}\n"
        result += f"📊 Found {len(matching_products)} products\n\n"
        result += "─" * 60 + "\n\n"
        
        # Group by business for display
        products_by_business = {}
        for product in matching_products:
            business_id = product.get('business_id', 'unknown')
            if business_id not in products_by_business:
                products_by_business[business_id] = []
            products_by_business[business_id].append(product)
        
        # Display results
        for business_id, products in products_by_business.items():
            business = businesses.get(business_id, {})
            business_name = business.get('name', 'Unknown Business')
            
            result += f"🏪 **{business_name}**\n"
            result += f"📍 {business.get('location', 'Unknown Location')}\n"
            result += f"📞 {business.get('phone', 'No phone')}\n\n"
            
            for product in products:
                name = product.get('name', 'Unknown Product')
                price = product.get('price', 0)
                stock = product.get('stock', 0)
                category = product.get('category', 'Other')
                brand = product.get('brand', '')
                
                result += f"   🔹 **{name}**"
                if brand:
                    result += f" ({brand})"
                result += f"\n      💰 KSh {price:,} | 📂 {category} | 📦 {stock} available"
                result += f"\n      🆔 Product ID: {product.get('id', 'N/A')}\n"
                
                # Highlight matching terms in description
                description = product.get('description', '')
                if description and len(description) <= 100:
                    result += f"      📝 {description}\n"
                
                result += "\n"
            
            result += "─" * 40 + "\n\n"
        
        result += "💡 To order any of these products, use the 'Place Order' tool with the Product ID."
        
        return result
        
    except Exception as e:
        return f"❌ Error searching products: {str(e)}\nPlease try again with valid search criteria."


def place_order_handler(params: Dict[str, Any]) -> str:
    """
    Place an order for products
    Now saves orders to JSON and updates product stock
    """
    try:
        # Required parameters
        customer_name = params.get('customer_name', '').strip()
        customer_phone = params.get('customer_phone', '').strip()
        customer_email = params.get('customer_email', '').strip()
        delivery_address = params.get('delivery_address', '').strip()
        
        # Order items - expect list of {product_id, quantity}
        order_items = params.get('items', [])
        
        # Optional parameters
        payment_method = params.get('payment_method', 'mpesa').lower()
        delivery_instructions = params.get('delivery_instructions', '').strip()
        
        # Validation
        if not all([customer_name, customer_phone, delivery_address]):
            return "❌ Missing required information:\n- customer_name\n- customer_phone\n- delivery_address"
        
        if not order_items or not isinstance(order_items, list):
            return "❌ No items specified. Please provide 'items' as a list of {product_id, quantity}"
        
        # Validate phone number format
        if not customer_phone.startswith('+254') and not customer_phone.startswith('07') and not customer_phone.startswith('01'):
            return "❌ Invalid phone number format. Use +254 format or 07/01 format."
        
        # Normalize phone number
        if customer_phone.startswith('07') or customer_phone.startswith('01'):
            customer_phone = '+254' + customer_phone[1:]
        
        # Load current products and businesses
        products = db.get_products()
        businesses = db.get_businesses()
        
        # Process order items
        order_details = []
        total_amount = 0
        business_id = None
        errors = []
        
        for item in order_items:
            if not isinstance(item, dict):
                errors.append("Each item must be a dictionary with product_id and quantity")
                continue
                
            product_id = str(item.get('product_id', ''))
            try:
                quantity = int(item.get('quantity', 0))
            except (ValueError, TypeError):
                errors.append(f"Invalid quantity for product {product_id}")
                continue
            
            if quantity <= 0:
                errors.append(f"Quantity must be positive for product {product_id}")
                continue
            
            # Find the product
            product = db.get_product_by_id(product_id)
            if not product:
                errors.append(f"Product {product_id} not found")
                continue
            
            # Check if product is active
            if product.get('status', 'active') != 'active':
                errors.append(f"Product {product.get('name', product_id)} is not available")
                continue
            
            # Check stock
            available_stock = product.get('stock', 0)
            if quantity > available_stock:
                errors.append(f"Not enough stock for {product.get('name', product_id)}. Available: {available_stock}, Requested: {quantity}")
                continue
            
            # Check business consistency (all products must be from same business)
            product_business = product.get('business_id')
            if business_id is None:
                business_id = product_business
            elif business_id != product_business:
                errors.append("All products must be from the same business in one order")
                continue
            
            # Calculate item total
            unit_price = product.get('price', 0)
            item_total = unit_price * quantity
            
            order_details.append({
                'product_id': product_id,
                'product_name': product.get('name', 'Unknown'),
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': item_total
            })
            
            total_amount += item_total
        
        # Return errors if any
        if errors:
            return "❌ Order cannot be processed due to the following errors:\n" + "\n".join(f"• {error}" for error in errors)
        
        if not order_details:
            return "❌ No valid items in the order."
        
        # Get business info
        business = businesses.get(business_id, {})
        business_name = business.get('name', 'Unknown Business')
        
        # Calculate delivery fee (simple logic)
        delivery_fee = 200  # Standard delivery fee
        grand_total = total_amount + delivery_fee
        
        # Create order object
        new_order = {
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'customer_email': customer_email,
            'business_id': business_id,
            'items': order_details,
            'total_amount': total_amount,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
            'status': 'pending',
            'payment_method': payment_method,
            'payment_status': 'pending',
            'delivery_address': delivery_address,
            'delivery_instructions': delivery_instructions
        }
        
        # Save order to database
        order_saved = db.add_order(new_order)
        if not order_saved:
            return "❌ Failed to save order. Please try again."
        
        # Update product stock
        stock_updates_failed = []
        for item in order_details:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Get current product
            product = db.get_product_by_id(product_id)
            new_stock = product.get('stock', 0) - quantity
            
            # Update stock
            success = db.update_product(product_id, {'stock': new_stock})
            if not success:
                stock_updates_failed.append(product.get('name', product_id))
        
        # Get the order ID that was generated
        orders = db.get_orders()
        latest_order = max(orders, key=lambda x: x.get('created_at', ''))
        order_id = latest_order.get('id', 'Unknown')
        
        # Prepare response
        result = "✅ **ORDER PLACED SUCCESSFULLY!** ✅\n\n"
        result += f"🆔 **Order ID:** {order_id}\n"
        result += f"🏪 **Business:** {business_name}\n"
        result += f"👤 **Customer:** {customer_name}\n"
        result += f"📞 **Phone:** {customer_phone}\n"
        if customer_email:
            result += f"📧 **Email:** {customer_email}\n"
        result += f"📍 **Delivery Address:** {delivery_address}\n"
        if delivery_instructions:
            result += f"📝 **Delivery Instructions:** {delivery_instructions}\n"
        
        result += "\n📦 **ORDER ITEMS:**\n"
        for item in order_details:
            result += f"   • {item['product_name']} x{item['quantity']} @ KSh {item['unit_price']:,} = KSh {item['total_price']:,}\n"
        
        result += f"\n💰 **PAYMENT SUMMARY:**\n"
        result += f"   Subtotal: KSh {total_amount:,}\n"
        result += f"   Delivery: KSh {delivery_fee:,}\n"
        result += f"   **TOTAL: KSh {grand_total:,}**\n"
        
        result += f"\n💳 **Payment Method:** {payment_method.upper()}\n"
        result += f"📋 **Order Status:** PENDING\n"
        result += f"💲 **Payment Status:** PENDING\n"
        
        result += f"\n📞 **Next Steps:**\n"
        result += f"1. The business will contact you to confirm the order\n"
        result += f"2. To pay now: Type 'pay for order {order_id}'\n"
        result += f"3. Your order will be prepared after payment\n"
        result += f"4. Track your order using: 'order status {order_id}'\n"
        
        # Show business contact info
        if business.get('phone'):
            result += f"\n🏪 **Business Contact:** {business.get('phone')}\n"
        
        # Warn about stock update failures
        if stock_updates_failed:
            result += f"\n⚠️ **Warning:** Stock update failed for: {', '.join(stock_updates_failed)}\n"
        
        result += f"\n🕒 **Order placed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return result
        
    except Exception as e:
        return f"❌ Error placing order: {str(e)}\nPlease check your order details and try again."


def get_order_status_handler(params: Dict[str, Any]) -> str:
    """
    Check the status of an existing order
    Loads order info from JSON database
    """
    try:
        order_id = params.get('order_id', '').strip()
        customer_phone = params.get('customer_phone', '').strip()
        
        if not order_id:
            return "❌ Please provide the order_id to check status."
        
        # Load order from database
        order = db.get_order_by_id(order_id)
        if not order:
            return f"❌ Order {order_id} not found. Please check the order ID and try again."
        
        # Verify customer phone if provided (for security)
        if customer_phone and order.get('customer_phone') != customer_phone:
            return "❌ Phone number doesn't match the order. Access denied."
        
        # Load business info
        businesses = db.get_businesses()
        business = businesses.get(order.get('business_id'), {})
        
        # Format order status
        result = f"📋 **ORDER STATUS: {order_id}** 📋\n\n"
        
        # Customer info
        result += f"👤 **Customer:** {order.get('customer_name', 'Unknown')}\n"
        result += f"📞 **Phone:** {order.get('customer_phone', 'Unknown')}\n"
        if order.get('customer_email'):
            result += f"📧 **Email:** {order.get('customer_email')}\n"
        
        # Business info
        result += f"🏪 **Business:** {business.get('name', 'Unknown Business')}\n"
        if business.get('phone'):
            result += f"📞 **Business Phone:** {business.get('phone')}\n"
        
        # Order details
        result += f"\n📦 **ORDER ITEMS:**\n"
        for item in order.get('items', []):
            result += f"   • {item.get('product_name', 'Unknown')} x{item.get('quantity', 0)} @ KSh {item.get('unit_price', 0):,}\n"
        
        # Financial summary
        result += f"\n💰 **FINANCIAL SUMMARY:**\n"
        result += f"   Subtotal: KSh {order.get('total_amount', 0):,}\n"
        result += f"   Delivery: KSh {order.get('delivery_fee', 0):,}\n"
        result += f"   **TOTAL: KSh {order.get('grand_total', 0):,}**\n"
        
        # Status info
        status = order.get('status', 'unknown').upper()
        payment_status = order.get('payment_status', 'unknown').upper()
        
        result += f"\n📋 **Current Status:** {status}\n"
        result += f"💳 **Payment Status:** {payment_status}\n"
        result += f"💳 **Payment Method:** {order.get('payment_method', 'unknown').upper()}\n"
        
        # Delivery info
        result += f"\n📍 **Delivery Address:** {order.get('delivery_address', 'Unknown')}\n"
        if order.get('delivery_instructions'):
            result += f"📝 **Delivery Instructions:** {order.get('delivery_instructions')}\n"
        
        # Timeline
        result += f"\n⏰ **ORDER TIMELINE:**\n"
        if order.get('created_at'):
            result += f"   📅 Placed: {order.get('created_at')}\n"
        if order.get('confirmed_at'):
            result += f"   ✅ Confirmed: {order.get('confirmed_at')}\n"
        if order.get('shipped_at'):
            result += f"   🚚 Shipped: {order.get('shipped_at')}\n"
        if order.get('delivered_at'):
            result += f"   📦 Delivered: {order.get('delivered_at')}\n"
        
        # Status-specific messages
        if status == 'PENDING':
            result += f"\n💡 **Next:** Waiting for business confirmation. They will contact you soon.\n"
        elif status == 'CONFIRMED':
            result += f"\n💡 **Next:** Order is being prepared for shipment.\n"
        elif status == 'SHIPPED':
            result += f"\n💡 **Next:** Your order is on the way!\n"
        elif status == 'DELIVERED':
            result += f"\n🎉 **Your order has been delivered!** Thank you for your business.\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error checking order status: {str(e)}\nPlease try again with a valid order ID."


# =============================================================================
# TOOL DEFINITIONS FOR REGISTRY
# =============================================================================

customer_tools = [
    {
        "name": "browse_products",
        "description": "Browse all available products from all businesses. Shows current inventory and prices from JSON database.",
        "handler": browse_products_handler,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "search_products", 
        "description": "Search for products by name, category, price range, or business. Searches current JSON data.",
        "handler": search_products_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term for product name, description, or brand"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter"
                },
                "category": {
                    "type": "string", 
                    "description": "Product category filter"
                },
                "business_id": {
                    "type": "string",
                    "description": "Filter by specific business ID"
                }
            },
            "required": []
        }
    },
    {
        "name": "place_order",
        "description": "Place an order for products. Saves order to JSON database and updates product stock.",
        "handler": place_order_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer's full name"
                },
                "customer_phone": {
                    "type": "string", 
                    "description": "Customer's phone number (preferably +254 format)"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer's email address (optional)"
                },
                "delivery_address": {
                    "type": "string",
                    "description": "Full delivery address"
                },
                "items": {
                    "type": "array",
                    "description": "List of items to order",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "quantity": {"type": "integer"}
                        },
                        "required": ["product_id", "quantity"]
                    }
                },
                "payment_method": {
                    "type": "string",
                    "description": "Payment method: mpesa, cash, or bank",
                    "default": "mpesa"
                },
                "delivery_instructions": {
                    "type": "string",
                    "description": "Special delivery instructions (optional)"
                }
            },
            "required": ["customer_name", "customer_phone", "delivery_address", "items"]
        }
    },
    {
        "name": "get_order_status",
        "description": "Check the status of an existing order using order ID. Loads from JSON database.",
        "handler": get_order_status_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to check (e.g., ORD001)"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer phone number for verification (optional)"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "initiate_mpesa_payment",
        "description": "Start M-Pesa payment process for an order",
        "handler": initiate_mpesa_payment_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to pay for (e.g., ORD001)"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer's M-Pesa phone number (optional)"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "check_payment_status",
        "description": "Check the current status of a payment",
        "handler": check_payment_status_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {
                    "type": "string",
                    "description": "Payment ID to check status for"
                }
            },
            "required": ["payment_id"]
        }
    },
    {
        "name": "get_payment_help",
        "description": "Get help and troubleshooting for M-Pesa payments",
        "handler": get_payment_help_handler,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "retry_payment",
        "description": "Retry payment for an order after failure",
        "handler": retry_payment_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to retry payment for"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer phone number (optional)"
                }
            },
            "required": ["order_id"]
        }
    }
]