import chainlit as cl
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import the database helper
from utils.simple_db import db

# =============================================================================
# DYNAMIC DATA LOADING FROM JSON FILES
# =============================================================================

def load_businesses_from_json() -> Dict:
    """Load businesses from JSON file"""
    try:
        businesses = db.get_businesses()
        print(f"✅ Loaded {len(businesses)} businesses from JSON")
        return businesses
    except Exception as e:
        print(f"❌ Error loading businesses: {e}")
        return {}

def load_products_from_json() -> List[Dict]:
    """Load products from JSON file"""
    try:
        products = db.get_products()
        print(f"✅ Loaded {len(products)} products from JSON")
        return products
    except Exception as e:
        print(f"❌ Error loading products: {e}")
        return []

def load_orders_from_json() -> List[Dict]:
    """Load orders from JSON file"""
    try:
        orders = db.get_orders()
        print(f"✅ Loaded {len(orders)} orders from JSON")
        return orders
    except Exception as e:
        print(f"❌ Error loading orders: {e}")
        return []

def get_products_for_business(business_id: str) -> List[Dict]:
    """Get all products for a specific business from JSON"""
    try:
        products = db.get_products_by_business(business_id)
        return products
    except Exception as e:
        print(f"❌ Error loading products for business {business_id}: {e}")
        return []

def get_demo_businesses() -> Dict:
    """Get businesses data - loads from JSON"""
    businesses_data = load_businesses_from_json()
    
    # Add products to each business (for backward compatibility)
    for business_id, business in businesses_data.items():
        business_products = get_products_for_business(business_id)
        business['products'] = business_products
    
    return businesses_data

# Main variable that existing code expects - now loads from JSON
DEMO_BUSINESSES = get_demo_businesses()

# Sample orders - now loads from JSON
SAMPLE_ORDERS = load_orders_from_json()

# =============================================================================
# DATA MODIFICATION FUNCTIONS
# =============================================================================

def add_product_to_json(business_id: str, product_data: Dict) -> bool:
    """Add a new product and save to JSON"""
    try:
        # Ensure business_id is set
        product_data['business_id'] = business_id
        
        # Add the product using database helper
        success = db.add_product(product_data)
        
        if success:
            # Reload the DEMO_BUSINESSES to reflect changes
            global DEMO_BUSINESSES
            DEMO_BUSINESSES = get_demo_businesses()
            print(f"✅ Added product '{product_data.get('name')}' to JSON")
        
        return success
    except Exception as e:
        print(f"❌ Error adding product to JSON: {e}")
        return False

def update_product_in_json(product_id: str, updates: Dict) -> bool:
    """Update a product and save to JSON"""
    try:
        success = db.update_product(product_id, updates)
        
        if success:
            # Reload the DEMO_BUSINESSES to reflect changes
            global DEMO_BUSINESSES
            DEMO_BUSINESSES = get_demo_businesses()
            print(f"✅ Updated product {product_id} in JSON")
        
        return success
    except Exception as e:
        print(f"❌ Error updating product in JSON: {e}")
        return False

def delete_product_from_json(product_id: str) -> bool:
    """Delete a product and save to JSON"""
    try:
        success = db.delete_product(product_id)
        
        if success:
            # Reload the DEMO_BUSINESSES to reflect changes
            global DEMO_BUSINESSES
            DEMO_BUSINESSES = get_demo_businesses()
            print(f"✅ Deleted product {product_id} from JSON")
        
        return success
    except Exception as e:
        print(f"❌ Error deleting product from JSON: {e}")
        return False

def add_order_to_json(order_data: Dict) -> bool:
    """Add a new order and save to JSON"""
    try:
        success = db.add_order(order_data)
        
        if success:
            # Reload orders
            global SAMPLE_ORDERS
            SAMPLE_ORDERS = load_orders_from_json()
            print(f"✅ Added order to JSON")
        
        return success
    except Exception as e:
        print(f"❌ Error adding order to JSON: {e}")
        return False

def update_product_stock(product_id: str, new_stock: int) -> bool:
    """Update product stock level"""
    try:
        return update_product_in_json(product_id, {"stock": new_stock})
    except Exception as e:
        print(f"❌ Error updating stock for product {product_id}: {e}")
        return False

def reduce_product_stock(product_id: str, quantity: int) -> bool:
    """Reduce product stock by specified quantity"""
    try:
        product = db.get_product_by_id(product_id)
        if not product:
            print(f"❌ Product {product_id} not found")
            return False
        
        current_stock = product.get('stock', 0)
        new_stock = max(0, current_stock - quantity)
        
        return update_product_stock(product_id, new_stock)
    except Exception as e:
        print(f"❌ Error reducing stock for product {product_id}: {e}")
        return False

# =============================================================================
# DATA REFRESH FUNCTIONS
# =============================================================================

def reload_demo_data() -> Dict:
    """Reload all demo data from JSON files"""
    try:
        global DEMO_BUSINESSES, SAMPLE_ORDERS
        
        # Reload all data
        DEMO_BUSINESSES = get_demo_businesses()
        SAMPLE_ORDERS = load_orders_from_json()
        
        stats = db.get_stats()
        print(f"✅ Reloaded demo data: {stats}")
        
        return {
            "success": True,
            "businesses": len(DEMO_BUSINESSES),
            "products": stats.get('products_count', 0),
            "orders": len(SAMPLE_ORDERS),
            "message": "Demo data reloaded from JSON files"
        }
    except Exception as e:
        print(f"❌ Error reloading demo data: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to reload demo data"
        }

def get_fresh_business_data(business_id: str) -> Optional[Dict]:
    """Get fresh business data from JSON"""
    try:
        businesses = load_businesses_from_json()
        business = businesses.get(business_id)
        
        if business:
            # Add fresh products
            business['products'] = get_products_for_business(business_id)
        
        return business
    except Exception as e:
        print(f"❌ Error getting fresh business data: {e}")
        return None

def get_fresh_products() -> List[Dict]:
    """Get fresh products data from JSON"""
    return load_products_from_json()

def get_fresh_orders() -> List[Dict]:
    """Get fresh orders data from JSON"""
    return load_orders_from_json()

# =============================================================================
# SEARCH AND FILTER FUNCTIONS
# =============================================================================

def find_product_by_name(product_name: str, business_id: str = None) -> Optional[Dict]:
    """Find a product by name in JSON data"""
    try:
        return db.find_product_by_name(product_name, business_id)
    except Exception as e:
        print(f"❌ Error finding product '{product_name}': {e}")
        return None

def get_products_by_category(category: str, business_id: str = None) -> List[Dict]:
    """Get products by category from JSON"""
    try:
        products = db.get_products()
        
        if business_id:
            products = [p for p in products if p.get('business_id') == business_id]
        
        if category:
            products = [p for p in products if category.lower() in p.get('category', '').lower()]
        
        return products
    except Exception as e:
        print(f"❌ Error getting products by category '{category}': {e}")
        return []

def get_low_stock_products(business_id: str, threshold: int = 5) -> List[Dict]:
    """Get products with low stock from JSON"""
    try:
        products = get_products_for_business(business_id)
        return [p for p in products if p.get('stock', 0) <= threshold and p.get('stock', 0) > 0]
    except Exception as e:
        print(f"❌ Error getting low stock products: {e}")
        return []

def get_out_of_stock_products(business_id: str) -> List[Dict]:
    """Get products that are out of stock from JSON"""
    try:
        products = get_products_for_business(business_id)
        return [p for p in products if p.get('stock', 0) == 0]
    except Exception as e:
        print(f"❌ Error getting out of stock products: {e}")
        return []

# =============================================================================
# DEMO DATA TOOLS (UPDATED TO USE JSON)
# =============================================================================

load_demo_data_def = {
    "name": "load_demo_data",
    "description": "Initialize and load demo data from JSON files",
    "parameters": {
        "type": "object",
        "properties": {
            "reload_from_files": {
                "type": "boolean",
                "description": "Force reload from JSON files",
                "default": True
            }
        },
        "required": []
    }
}

async def load_demo_data_handler(reload_from_files: bool = True):
    """Load demo business data from JSON files"""
    try:
        if reload_from_files:
            result = reload_demo_data()
            if not result['success']:
                return {
                    "message": f"❌ Failed to load demo data: {result.get('error', 'Unknown error')}",
                    "demo_ready": False
                }
        
        # Get current stats
        stats = db.get_stats()
        businesses = DEMO_BUSINESSES
        
        # Calculate inventory value
        total_inventory_value = 0
        for business in businesses.values():
            for product in business.get('products', []):
                total_inventory_value += product.get('price', 0) * product.get('stock', 0)
        
        message = f"""🎯 **DYNAMIC JSON DATABASE LOADED**

🏪 **BUSINESSES:** {stats.get('businesses_count', 0)} active businesses
• Data loaded from data/businesses.json

📦 **INVENTORY:**
• Total Products: {stats.get('products_count', 0)} items
• Total Value: KSh {total_inventory_value:,.0f}
• Data source: data/products.json

📋 **ORDERS:** {stats.get('orders_count', 0)} orders
• Order history from data/orders.json
• Real-time order processing

💾 **DATABASE STATUS:**
• All changes now persist to JSON files
• CRUD operations are fully functional
• Data survives application restarts

🔧 **DYNAMIC FEATURES:**
• Add/Edit/Delete products - saves to JSON
• Real inventory tracking
• Persistent order history
• Live stock updates

**✅ Dynamic JSON database is ready!** All changes will be saved to JSON files."""

        return {
            "message": message,
            "businesses_count": stats.get('businesses_count', 0),
            "products_count": stats.get('products_count', 0),
            "orders_count": stats.get('orders_count', 0),
            "inventory_value": total_inventory_value,
            "demo_ready": True,
            "database_type": "JSON Files"
        }
        
    except Exception as e:
        return {
            "message": f"❌ Error loading demo data: {str(e)}",
            "demo_ready": False,
            "error": str(e)
        }

demo_explanation_def = {
    "name": "demo_explanation", 
    "description": "Explain how the JSON database works",
    "parameters": {
        "type": "object",
        "properties": {
            "focus_area": {
                "type": "string",
                "enum": ["overview", "json_benefits", "crud_operations", "persistence", "real_world"],
                "description": "Specific area to focus explanation on",
                "default": "overview"
            }
        },
        "required": []
    }
}

async def demo_explanation_handler(focus_area: str = "overview"):
    """Explain the JSON database implementation"""
    
    explanations = {
        "overview": """🗄️ **JSON DATABASE IMPLEMENTATION**

**📁 File Structure:**
• `data/businesses.json` - Business information
• `data/products.json` - Product catalog with stock
• `data/orders.json` - Order history and tracking
• `data/customers.json` - Customer profiles

**🔄 How It Works:**
• All data loads from JSON files on startup
• Changes save immediately to JSON files
• No data loss when app restarts
• Easy to inspect and modify data manually

**💾 CRUD Operations:**
• **Create**: Add products → saves to JSON
• **Read**: Browse products → loads from JSON  
• **Update**: Edit products → updates JSON
• **Delete**: Remove products → deletes from JSON

**This is now a REAL database demo - changes persist!**""",

        "crud_operations": """⚙️ **CRUD OPERATIONS IN ACTION**

**✅ CREATE - Adding Products:**
• Vendor says "Add iPhone for 75k"
• New product object created
• Saved to `data/products.json`
• Auto-generates unique ID
• Adds timestamps

**📖 READ - Browsing Products:**
• Customer says "Show products"
• Loads fresh data from JSON files
• Displays current stock levels
• Shows real-time inventory

**✏️ UPDATE - Editing Products:**
• Vendor says "Update iPhone price to 70k"
• Finds product in JSON
• Updates price field
• Saves entire file back
• Maintains data integrity

**🗑️ DELETE - Removing Products:**
• Vendor says "Delete iPhone"
• Removes from products array
• Saves updated JSON file
• Product permanently removed

**All operations persist between app sessions!**""",

        "persistence": """💾 **DATA PERSISTENCE BENEFITS**

**🔄 Survives Restarts:**
• Add a product, restart the app
• Product is still there!
• All changes saved to JSON files
• No data loss ever

**📊 Real Inventory Tracking:**
• Customer buys 2 phones
• Stock reduces from 10 to 8
• Change saved to JSON immediately
• Next customer sees updated stock

**📈 Order History:**
• Every order saves to JSON
• Complete order tracking
• Customer order history
• Business analytics possible

**🛠️ Easy Maintenance:**
• Can edit JSON files directly
• Backup by copying files
• Reset demo by restoring files
• Simple but powerful

**Perfect for demonstrating real e-commerce functionality!**"""
    }
    
    message = explanations.get(focus_area, explanations["overview"])
    
    return {
        "message": message,
        "focus_area": focus_area,
        "database_type": "JSON Files",
        "persistence": True
    }

# =============================================================================
# DEMO TOOLS REGISTRY
# =============================================================================

demo_tools = [
    (load_demo_data_def, load_demo_data_handler),
    (demo_explanation_def, demo_explanation_handler),
]

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_demo_data():
    """Initialize demo data on module import"""
    try:
        # Validate that JSON files exist
        validation = db.validate_data_files()
        missing_files = [f for f, exists in validation.items() if not exists]
        
        if missing_files:
            print(f"⚠️ Missing JSON files: {missing_files}")
            print("Please ensure all JSON files exist in the data/ directory")
        else:
            print("✅ All JSON database files found")
            
        # Load initial data
        global DEMO_BUSINESSES, SAMPLE_ORDERS
        DEMO_BUSINESSES = get_demo_businesses()
        SAMPLE_ORDERS = load_orders_from_json()
        
        stats = db.get_stats()
        print(f"✅ Demo data initialized from JSON: {stats}")
        
    except Exception as e:
        print(f"❌ Error initializing demo data: {e}")

# Initialize when module is imported
initialize_demo_data()