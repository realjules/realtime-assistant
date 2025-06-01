"""
Vendor Tools
All business owner functionality including product management, inventory, and reports
"""

import chainlit as cl
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import demo data
from .demo_data import DEMO_BUSINESSES

# =============================================================================
# VENDOR DASHBOARD
# =============================================================================

vendor_menu_def = {
    "name": "vendor_menu",
    "description": "Show vendor dashboard menu with available options",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

async def vendor_menu_handler():
    """Show vendor menu options"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    business_name = DEMO_BUSINESSES.get(business_id, {}).get("name", "Your Business")
    
    menu = f"""🏪 **{business_name.upper()} DASHBOARD**

**📦 INVENTORY MANAGEMENT:**
• "Show my products" - View product catalog
• "Add product [name] [price]" - Add new item
• "Update stock [product] [quantity]" - Adjust inventory
• "Check low stock" - See items running low
• "Delete product [name]" - Remove item

**📊 REPORTS & ANALYTICS:**
• "Daily report" - Today's performance
• "Weekly report" - 7-day summary  
• "Monthly report" - 30-day overview
• "Top selling products" - Best performers
• "Revenue forecast" - Predict future sales

**💰 QUICK STATS:**
• "How are sales today?" - Quick revenue check
• "How many orders?" - Order count
• "Show revenue" - Money overview
• "Customer analytics" - Customer insights

**🚨 ALERTS & NOTIFICATIONS:**
• "Set stock alerts" - Configure notifications
• "View alerts" - See active alerts

**What would you like to do?**"""

    return {"menu": menu, "options_count": 15, "business_name": business_name}

# =============================================================================
# PRODUCT MANAGEMENT
# =============================================================================

add_product_def = {
    "name": "add_product",
    "description": "Add a new product to inventory",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Name of the product"
            },
            "price": {
                "type": "number",
                "description": "Product price in KSh"
            },
            "stock": {
                "type": "integer",
                "description": "Initial stock quantity",
                "default": 1
            },
            "category": {
                "type": "string",
                "description": "Product category",
                "default": "General"
            },
            "description": {
                "type": "string",
                "description": "Product description",
                "default": ""
            }
        },
        "required": ["product_name", "price"]
    }
}

async def add_product_handler(product_name: str, price: float, stock: int = 1, category: str = "General", description: str = ""):
    """Add product to inventory"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    
    if business_id not in DEMO_BUSINESSES:
        return {"success": False, "message": "❌ Business not found"}
    
    # Check if product already exists
    existing_products = DEMO_BUSINESSES[business_id]["products"]
    for product in existing_products:
        if product["name"].lower() == product_name.lower():
            return {
                "success": False,
                "message": f"❌ Product '{product_name}' already exists. Use 'update product' to modify it."
            }
    
    new_product = {
        "id": str(len(existing_products) + 1),
        "name": product_name,
        "price": price,
        "stock": stock,
        "category": category,
        "description": description,
        "created_at": datetime.now().isoformat()
    }
    
    DEMO_BUSINESSES[business_id]["products"].append(new_product)
    
    return {
        "success": True,
        "message": f"✅ **Product Added Successfully!**\n\n📱 **{product_name}**\n💰 Price: KSh {price:,.0f}\n📦 Stock: {stock} units\n🏷️ Category: {category}\n📝 Description: {description or 'No description'}\n\nProduct is now available for customers!",
        "product": new_product
    }

update_product_def = {
    "name": "update_product",
    "description": "Update existing product details",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Name of product to update"
            },
            "new_price": {
                "type": "number",
                "description": "New price"
            },
            "new_stock": {
                "type": "integer", 
                "description": "New stock quantity"
            },
            "new_description": {
                "type": "string",
                "description": "New description"
            }
        },
        "required": ["product_name"]
    }
}

async def update_product_handler(product_name: str, new_price: float = None, new_stock: int = None, new_description: str = None):
    """Update product details"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    
    if business_id not in DEMO_BUSINESSES:
        return {"success": False, "message": "❌ Business not found"}
    
    products = DEMO_BUSINESSES[business_id]["products"]
    
    for product in products:
        if product_name.lower() in product["name"].lower():
            old_values = product.copy()
            
            if new_price is not None:
                product["price"] = new_price
            if new_stock is not None:
                product["stock"] = new_stock
            if new_description is not None:
                product["description"] = new_description
            
            changes = []
            if new_price and new_price != old_values["price"]:
                changes.append(f"💰 Price: KSh {old_values['price']:,.0f} → KSh {new_price:,.0f}")
            if new_stock is not None and new_stock != old_values["stock"]:
                changes.append(f"📦 Stock: {old_values['stock']} → {new_stock} units")
            if new_description and new_description != old_values.get("description", ""):
                changes.append(f"📝 Description updated")
            
            if not changes:
                return {"success": False, "message": "❌ No changes specified"}
            
            message = f"✅ **{product['name']} Updated!**\n\n" + "\n".join(changes)
            
            return {
                "success": True,
                "message": message,
                "product": product,
                "changes": changes
            }
    
    return {"success": False, "message": f"❌ Product '{product_name}' not found"}

delete_product_def = {
    "name": "delete_product",
    "description": "Remove product from inventory",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Name of product to delete"
            }
        },
        "required": ["product_name"]
    }
}

async def delete_product_handler(product_name: str):
    """Delete product from inventory"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    
    if business_id not in DEMO_BUSINESSES:
        return {"success": False, "message": "❌ Business not found"}
    
    products = DEMO_BUSINESSES[business_id]["products"]
    
    for i, product in enumerate(products):
        if product_name.lower() in product["name"].lower():
            deleted_product = products.pop(i)
            
            return {
                "success": True,
                "message": f"🗑️ **Product Deleted**\n\n❌ {deleted_product['name']} has been removed from your inventory\n💰 Was priced at: KSh {deleted_product['price']:,.0f}\n📦 Had {deleted_product['stock']} units in stock",
                "deleted_product": deleted_product
            }
    
    return {"success": False, "message": f"❌ Product '{product_name}' not found"}

show_products_def = {
    "name": "show_products",
    "description": "Display vendor's product catalog with stock levels",
    "parameters": {
        "type": "object",
        "properties": {
            "show_details": {
                "type": "boolean",
                "description": "Show detailed product information",
                "default": True
            },
            "category_filter": {
                "type": "string",
                "description": "Filter by category"
            }
        },
        "required": []
    }
}

async def show_products_handler(show_details: bool = True, category_filter: str = None):
    """Show vendor's products"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    
    if business_id not in DEMO_BUSINESSES:
        return {"message": "❌ No business found", "products": []}
    
    business = DEMO_BUSINESSES[business_id]
    products = business["products"]
    
    # Apply category filter
    if category_filter:
        products = [p for p in products if category_filter.lower() in p.get("category", "").lower()]
    
    if not products:
        filter_msg = f" in category '{category_filter}'" if category_filter else ""
        return {"message": f"📦 No products found{filter_msg}. Add your first product!", "products": []}
    
    product_list = [f"📦 **{business['name']} - Product Catalog**"]
    if category_filter:
        product_list[0] += f" (Category: {category_filter})"
    product_list.append("")
    
    total_value = 0
    low_stock_count = 0
    out_of_stock_count = 0
    
    for i, product in enumerate(products, 1):
        if product["stock"] == 0:
            stock_status = "❌ OUT OF STOCK"
            out_of_stock_count += 1
        elif product["stock"] < 5:
            stock_status = "⚠️ LOW STOCK"
            low_stock_count += 1
        else:
            stock_status = "✅ IN STOCK"
            
        product_value = product["price"] * product["stock"]
        total_value += product_value
        
        if show_details:
            product_list.append(
                f"**{i}. {product['name']}**\n"
                f"   💰 KSh {product['price']:,.0f} | 📦 {product['stock']} units {stock_status}\n"
                f"   🏷️ {product.get('category', 'General')} | 💎 Value: KSh {product_value:,.0f}"
            )
            if product.get("description"):
                product_list.append(f"   📝 {product['description']}")
            product_list.append("")
        else:
            product_list.append(f"{i}. {product['name']} - KSh {product['price']:,.0f} ({product['stock']} units)")
    
    summary = f"""📊 **INVENTORY SUMMARY:**
• Total Products: {len(products)}
• Total Value: KSh {total_value:,.0f}
• Low Stock Items: {low_stock_count}
• Out of Stock: {out_of_stock_count}"""
    
    if low_stock_count > 0 or out_of_stock_count > 0:
        summary += f"\n🚨 **Action Needed:** Restock {low_stock_count + out_of_stock_count} items!"
    
    message = "\n".join(product_list) + "\n" + summary
    
    return {
        "message": message,
        "products": products,
        "total_value": total_value,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count
    }

# =============================================================================
# INVENTORY MANAGEMENT
# =============================================================================

check_stock_def = {
    "name": "check_stock",
    "description": "Check stock levels and identify low stock items",
    "parameters": {
        "type": "object",
        "properties": {
            "threshold": {
                "type": "integer",
                "description": "Low stock threshold",
                "default": 5
            }
        },
        "required": []
    }
}

async def check_stock_handler(threshold: int = 5):
    """Check stock levels"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    
    if business_id not in DEMO_BUSINESSES:
        return {"message": "❌ Business not found"}
    
    products = DEMO_BUSINESSES[business_id]["products"]
    low_stock = [p for p in products if p["stock"] <= threshold and p["stock"] > 0]
    out_of_stock = [p for p in products if p["stock"] == 0]
    
    if not low_stock and not out_of_stock:
        return {
            "message": f"✅ **All products have sufficient stock!**\n\nAll items are above {threshold} units. Your inventory is well-managed! 🎉",
            "status": "good"
        }
    
    message_parts = ["🚨 **STOCK ALERT**\n"]
    
    if out_of_stock:
        message_parts.append("❌ **OUT OF STOCK:**")
        for product in out_of_stock:
            message_parts.append(f"• {product['name']} - URGENT: Restock needed!")
        message_parts.append("")
    
    if low_stock:
        message_parts.append(f"⚠️ **LOW STOCK (≤{threshold} units):**")
        for product in low_stock:
            message_parts.append(f"• {product['name']}: {product['stock']} units remaining")
        message_parts.append("")
    
    message_parts.append(f"💡 **Recommendation:** Reorder {len(low_stock + out_of_stock)} products soon!")
    
    return {
        "message": "\n".join(message_parts),
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "status": "attention_needed"
    }

update_stock_def = {
    "name": "update_stock",
    "description": "Update stock quantity for a product",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Name of product to update"
            },
            "new_quantity": {
                "type": "integer",
                "description": "New stock quantity"
            },
            "operation": {
                "type": "string",
                "enum": ["set", "add", "subtract"],
                "description": "How to update stock",
                "default": "set"
            }
        },
        "required": ["product_name", "new_quantity"]
    }
}

async def update_stock_handler(product_name: str, new_quantity: int, operation: str = "set"):
    """Update product stock"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    
    if business_id not in DEMO_BUSINESSES:
        return {"success": False, "message": "❌ Business not found"}
    
    products = DEMO_BUSINESSES[business_id]["products"]
    
    for product in products:
        if product_name.lower() in product["name"].lower():
            old_stock = product["stock"]
            
            if operation == "set":
                product["stock"] = new_quantity
            elif operation == "add":
                product["stock"] += new_quantity
            elif operation == "subtract":
                product["stock"] = max(0, product["stock"] - new_quantity)
            
            operation_text = {
                "set": "updated to",
                "add": f"increased by {new_quantity} to",
                "subtract": f"decreased by {new_quantity} to"
            }
            
            stock_status = ""
            if product["stock"] == 0:
                stock_status = " ❌ (OUT OF STOCK)"
            elif product["stock"] < 5:
                stock_status = " ⚠️ (LOW STOCK)"
            else:
                stock_status = " ✅"
            
            return {
                "success": True,
                "message": f"📦 **Stock Updated**\n\n**{product['name']}**\n🔄 Stock {operation_text[operation]} {product['stock']} units{stock_status}\n📊 Previous: {old_stock} units",
                "product": product,
                "old_stock": old_stock,
                "new_stock": product["stock"]
            }
    
    return {"success": False, "message": f"❌ Product '{product_name}' not found"}

# =============================================================================
# SALES REPORTS
# =============================================================================

generate_report_def = {
    "name": "generate_report",
    "description": "Generate sales reports for different time periods",
    "parameters": {
        "type": "object",
        "properties": {
            "period": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                "description": "Time period for the report",
                "default": "daily"
            },
            "include_analytics": {
                "type": "boolean",
                "description": "Include advanced analytics",
                "default": True
            }
        },
        "required": []
    }
}

async def generate_report_handler(period: str = "daily", include_analytics: bool = True):
    """Generate business reports"""
    business_id = cl.user_session.get("business_id", "mama_jane_electronics")
    
    if business_id not in DEMO_BUSINESSES:
        return {"message": "❌ Business not found"}
    
    business = DEMO_BUSINESSES[business_id]
    sales_data = business["sales_data"].get(period, {})
    
    if not sales_data:
        return {"message": f"❌ No {period} data available"}
    
    period_emoji = {
        "daily": "📅",
        "weekly": "📆", 
        "monthly": "🗓️",
        "quarterly": "📋",
        "yearly": "📊"
    }
    
    # Calculate additional metrics
    avg_order_value = sales_data['revenue'] / max(sales_data['orders'], 1)
    revenue_per_customer = sales_data['revenue'] / max(sales_data['customers'], 1)
    
    message = f"""{period_emoji[period]} **{period.upper()} BUSINESS REPORT**
📅 Period: {period.title()} Summary

💰 **FINANCIAL PERFORMANCE:**
• Total Revenue: KSh {sales_data['revenue']:,.0f}
• Orders Processed: {sales_data['orders']} orders
• Unique Customers: {sales_data['customers']} customers
• Average Order Value: KSh {avg_order_value:,.0f}
• Revenue per Customer: KSh {revenue_per_customer:,.0f}"""

    if include_analytics:
        # Add performance insights
        products = business["products"]
        total_inventory_value = sum(p["price"] * p["stock"] for p in products)
        
        # Simulate top products for demo
        top_products = [
            {"name": "Samsung Phone", "units_sold": 8, "revenue": 224000},
            {"name": "Wireless Headphones", "units_sold": 12, "revenue": 54000},
            {"name": "Laptop Dell", "units_sold": 3, "revenue": 165000}
        ]
        
        message += f"""

📊 **BUSINESS ANALYTICS:**
• Inventory Value: KSh {total_inventory_value:,.0f}
• Products in Catalog: {len(products)} items
• Revenue Conversion: {(sales_data['revenue']/max(total_inventory_value, 1)*100):.1f}%

🏆 **TOP PERFORMERS:**"""
        
        for i, product in enumerate(top_products[:3], 1):
            message += f"\n{i}. {product['name']}: {product['units_sold']} sold (KSh {product['revenue']:,.0f})"
        
        # Performance insights
        if sales_data['revenue'] > 100000:
            message += "\n\n🎉 **INSIGHT:** Excellent performance! Revenue target exceeded."
        elif sales_data['revenue'] > 50000:
            message += "\n\n📈 **INSIGHT:** Good performance! Consider increasing marketing."
        else:
            message += "\n\n💡 **INSIGHT:** Room for growth. Focus on customer acquisition."
    
    return {
        "message": message,
        "sales_data": sales_data,
        "period": period,
        "avg_order_value": avg_order_value
    }

# =============================================================================
# VENDOR TOOLS REGISTRY
# =============================================================================

vendor_tools = [
    (vendor_menu_def, vendor_menu_handler),
    (add_product_def, add_product_handler),
    (update_product_def, update_product_handler),
    (delete_product_def, delete_product_handler),
    (show_products_def, show_products_handler),
    (check_stock_def, check_stock_handler),
    (update_stock_def, update_stock_handler),
    (generate_report_def, generate_report_handler),
]