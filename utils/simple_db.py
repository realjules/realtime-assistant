"""
Simple JSON Database Helper
Handles all JSON file operations for the Sasabot demo
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class JSONDatabase:
    """Simple JSON file database for demo purposes"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(data_dir) / "backups"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create data and backup directories if they don't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
    
    def _get_file_path(self, filename: str) -> Path:
        """Get full path for a data file"""
        if not filename.endswith('.json'):
            filename += '.json'
        return self.data_dir / filename
    
    def _create_backup(self, filename: str) -> bool:
        """Create a timestamped backup of a file before modifying it"""
        try:
            file_path = self._get_file_path(filename)
            if not file_path.exists():
                return True  # No file to backup
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filename.replace('.json', '')}_{timestamp}.json"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f"Warning: Could not create backup for {filename}: {e}")
            return False
    
    def load_json(self, filename: str) -> Any:
        """Load data from a JSON file"""
        try:
            file_path = self._get_file_path(filename)
            
            if not file_path.exists():
                print(f"Warning: {filename} not found, returning empty data")
                return {} if filename in ['businesses', 'customers'] else []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Loaded {filename} successfully")
                return data
                
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {filename}: {e}")
            return {} if filename in ['businesses', 'customers'] else []
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return {} if filename in ['businesses', 'customers'] else []
    
    def save_json(self, filename: str, data: Any, create_backup: bool = True) -> bool:
        """Save data to a JSON file"""
        try:
            # Create backup before saving
            if create_backup:
                self._create_backup(filename)
            
            file_path = self._get_file_path(filename)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = file_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Replace original file with temp file
            temp_path.replace(file_path)
            
            print(f"✅ Saved {filename} successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            # Clean up temp file if it exists
            temp_path = file_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    # =============================================================================
    # BUSINESSES
    # =============================================================================
    
    def get_businesses(self) -> Dict:
        """Load businesses from JSON file"""
        return self.load_json('businesses')
    
    def save_businesses(self, businesses: Dict) -> bool:
        """Save businesses to JSON file"""
        return self.save_json('businesses', businesses)
    
    def get_business(self, business_id: str) -> Optional[Dict]:
        """Get a specific business by ID"""
        businesses = self.get_businesses()
        return businesses.get(business_id)
    
    # =============================================================================
    # PRODUCTS
    # =============================================================================
    
    def get_products(self) -> List[Dict]:
        """Load products from JSON file"""
        return self.load_json('products')
    
    def save_products(self, products: List[Dict]) -> bool:
        """Save products to JSON file"""
        return self.save_json('products', products)
    
    def get_products_by_business(self, business_id: str) -> List[Dict]:
        """Get all products for a specific business"""
        products = self.get_products()
        return [p for p in products if p.get('business_id') == business_id]
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Find a product by ID"""
        products = self.get_products()
        for product in products:
            if product.get('id') == product_id:
                return product
        return None
    
    def add_product(self, product: Dict) -> bool:
        """Add a new product"""
        products = self.get_products()
        
        # Generate new ID if not provided
        if 'id' not in product:
            existing_ids = [int(p.get('id', 0)) for p in products if p.get('id', '0').isdigit()]
            new_id = max(existing_ids, default=0) + 1
            product['id'] = str(new_id)
        
        # Add timestamp
        product['created_at'] = datetime.now().isoformat()
        product['updated_at'] = datetime.now().isoformat()
        
        products.append(product)
        return self.save_products(products)
    
    def update_product(self, product_id: str, updates: Dict) -> bool:
        """Update an existing product"""
        products = self.get_products()
        
        for i, product in enumerate(products):
            if product.get('id') == product_id:
                # Update fields
                products[i].update(updates)
                products[i]['updated_at'] = datetime.now().isoformat()
                return self.save_products(products)
        
        print(f"❌ Product with ID {product_id} not found")
        return False
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product by ID"""
        products = self.get_products()
        original_length = len(products)
        
        products = [p for p in products if p.get('id') != product_id]
        
        if len(products) < original_length:
            return self.save_products(products)
        else:
            print(f"❌ Product with ID {product_id} not found")
            return False
    
    def find_product_by_name(self, name: str, business_id: str = None) -> Optional[Dict]:
        """Find a product by name (partial match)"""
        products = self.get_products()
        
        if business_id:
            products = [p for p in products if p.get('business_id') == business_id]
        
        name_lower = name.lower()
        for product in products:
            if name_lower in product.get('name', '').lower():
                return product
        return None
    
    # =============================================================================
    # ORDERS
    # =============================================================================
    
    def get_orders(self) -> List[Dict]:
        """Load orders from JSON file"""
        return self.load_json('orders')
    
    def save_orders(self, orders: List[Dict]) -> bool:
        """Save orders to JSON file"""
        return self.save_json('orders', orders)
    
    def add_order(self, order: Dict) -> bool:
        """Add a new order"""
        orders = self.get_orders()
        
        # Generate new ID if not provided
        if 'id' not in order:
            existing_numbers = []
            for o in orders:
                order_id = o.get('id', '')
                if order_id.startswith('ORD'):
                    try:
                        num = int(order_id[3:])
                        existing_numbers.append(num)
                    except ValueError:
                        pass
            
            new_number = max(existing_numbers, default=0) + 1
            order['id'] = f"ORD{new_number:03d}"
        
        # Add timestamp
        order['created_at'] = datetime.now().isoformat()
        order['updated_at'] = datetime.now().isoformat()
        
        orders.append(order)
        return self.save_orders(orders)
    
    def get_orders_by_business(self, business_id: str) -> List[Dict]:
        """Get all orders for a specific business"""
        orders = self.get_orders()
        return [o for o in orders if o.get('business_id') == business_id]
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Find an order by ID"""
        orders = self.get_orders()
        for order in orders:
            if order.get('id') == order_id:
                return order
        return None
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        orders = self.get_orders()
        
        for i, order in enumerate(orders):
            if order.get('id') == order_id:
                orders[i]['status'] = status
                orders[i]['updated_at'] = datetime.now().isoformat()
                
                # Add status-specific timestamps
                if status == 'confirmed':
                    orders[i]['confirmed_at'] = datetime.now().isoformat()
                elif status == 'shipped':
                    orders[i]['shipped_at'] = datetime.now().isoformat()
                elif status == 'delivered':
                    orders[i]['delivered_at'] = datetime.now().isoformat()
                
                return self.save_orders(orders)
        
        print(f"❌ Order with ID {order_id} not found")
        return False
    
    # =============================================================================
    # CUSTOMERS
    # =============================================================================
    
    def get_customers(self) -> List[Dict]:
        """Load customers from JSON file"""
        return self.load_json('customers')
    
    def save_customers(self, customers: List[Dict]) -> bool:
        """Save customers to JSON file"""
        return self.save_json('customers', customers)
    
    def get_customer_by_phone(self, phone: str) -> Optional[Dict]:
        """Find customer by phone number"""
        customers = self.get_customers()
        for customer in customers:
            if customer.get('phone') == phone:
                return customer
        return None
    
    # =============================================================================
    # UTILITY FUNCTIONS
    # =============================================================================
    
    def reload_all_data(self) -> Dict[str, Any]:
        """Reload all data from JSON files"""
        return {
            'businesses': self.get_businesses(),
            'products': self.get_products(),
            'orders': self.get_orders(),
            'customers': self.get_customers()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            businesses = self.get_businesses()
            products = self.get_products()
            orders = self.get_orders()
            customers = self.get_customers()
            
            return {
                'businesses_count': len(businesses),
                'products_count': len(products),
                'orders_count': len(orders),
                'customers_count': len(customers),
                'data_directory': str(self.data_dir),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def validate_data_files(self) -> Dict[str, bool]:
        """Check if all required data files exist and are valid"""
        files_to_check = ['businesses.json', 'products.json', 'orders.json', 'customers.json']
        results = {}
        
        for filename in files_to_check:
            try:
                data = self.load_json(filename.replace('.json', ''))
                results[filename] = isinstance(data, (dict, list))
            except Exception:
                results[filename] = False
        
        return results
    
    def create_full_backup(self) -> str:
        """Create a complete backup of all data files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = self.backup_dir / f"full_backup_{timestamp}"
            backup_folder.mkdir(exist_ok=True)
            
            files_to_backup = ['businesses.json', 'products.json', 'orders.json', 'customers.json']
            
            for filename in files_to_backup:
                source = self.data_dir / filename
                if source.exists():
                    shutil.copy2(source, backup_folder / filename)
            
            return str(backup_folder)
        except Exception as e:
            print(f"❌ Error creating full backup: {e}")
            return ""
        
    def get_contextual_product_info(self, business_id: str, user_search: str = "") -> Dict:
        """Get rich product context for LLM processing"""
        try:
            products = self.get_products_by_business(business_id)
            business = self.get_business(business_id)
            
            return {
                "all_products": [
                    {
                        "id": p.get('id'),
                        "name": p.get('name'),
                        "price": p.get('price', 0),
                        "stock": p.get('stock', 0),
                        "category": p.get('category', ''),
                        "brand": p.get('brand', '')
                    }
                    for p in products if p.get('status') == 'active'
                ],
                "user_search_term": user_search,
                "business_name": business.get('name', 'Unknown Business') if business else 'Unknown Business',
                "business_id": business_id,
                "total_count": len(products),
                "categories": list(set(p.get('category', 'Unknown') for p in products))
            }
        except Exception as e:
            return {
                "all_products": [],
                "user_search_term": user_search,
                "business_name": "Unknown Business",
                "business_id": business_id,
                "total_count": 0,
                "categories": [],
                "error": str(e)
            }

    def validate_product_reference(self, product_identifier: str, business_id: str) -> Dict:
        """
        Validate if product exists and provide context if not
        Returns comprehensive validation result for LLM processing
        """
        try:
            # Try finding by ID first
            product = None
            if product_identifier.isdigit():
                product = self.get_product_by_id(product_identifier)
                # Verify it belongs to the business
                if product and product.get('business_id') != business_id:
                    product = None
            
            # If not found by ID, try by name
            if not product:
                product = self.find_product_by_name(product_identifier, business_id)
            
            if product:
                return {
                    "exists": True,
                    "product": product,
                    "match_type": "exact",
                    "context": None
                }
            else:
                # Product not found - get full context for LLM
                context = self.get_contextual_product_info(business_id, product_identifier)
                
                return {
                    "exists": False,
                    "product": None,
                    "match_type": "none",
                    "context": context,
                    "search_term": product_identifier,
                    "suggestion_prompt": f"User searched for '{product_identifier}' but it wasn't found. Help them find the right product from the available list."
                }
        except Exception as e:
            return {
                "exists": False,
                "product": None,
                "match_type": "error",
                "context": self.get_contextual_product_info(business_id, product_identifier),
                "error": str(e)
            }

    def format_product_display(self, product: Dict) -> str:
        """Standardized product display format with prominent ID"""
        try:
            name = product.get('name', 'Unknown Product')
            price = product.get('price', 0)
            stock = product.get('stock', 0)
            product_id = product.get('id', 'N/A')
            brand = product.get('brand', '')
            category = product.get('category', '')
            
            display = f"🆔 **ID: {product_id}**"
            
            if brand:
                display += f" | 🏷️ {brand} {name}"
            else:
                display += f" | 📱 {name}"
                
            display += f" | 💰 KSh {price:,}"
            display += f" | 📦 {stock} in stock"
            
            if category:
                display += f" | 📂 {category}"
                
            return display
        except Exception:
            return f"🆔 **ID: {product.get('id', 'Unknown')}** | {product.get('name', 'Unknown Product')}"

    def get_product_quick_reference(self, business_id: str) -> str:
        """Generate quick reference guide for product operations"""
        try:
            products = self.get_products_by_business(business_id)
            if not products:
                return "No products available"
            
            reference = "💡 **Quick Reference:**\n"
            reference += "To update: 'update product [ID]' or 'update [product name]'\n"
            reference += "To delete: 'delete product [ID]' or 'delete [product name]'\n\n"
            reference += "**Available Product IDs:**\n"
            
            for product in products[:10]:  # Show first 10
                reference += f"• ID: {product.get('id')} = {product.get('name', 'Unknown')}\n"
                
            if len(products) > 10:
                reference += f"... and {len(products) - 10} more products\n"
                
            return reference
        except Exception:
            return "Error generating quick reference"

    # =============================================================================
    # PAYMENTS (ADD TO EXISTING CLASS)
    # =============================================================================
    
    def get_payments(self) -> List[Dict]:
        """Load payments from JSON file"""
        return self.load_json('payments')
    
    def save_payments(self, payments: List[Dict]) -> bool:
        """Save payments to JSON file"""
        return self.save_json('payments', payments)
    
    def get_payment_by_id(self, payment_id: str) -> Optional[Dict]:
        """Find a payment by ID"""
        payments = self.get_payments()
        for payment in payments:
            if payment.get('payment_id') == payment_id:
                return payment
        return None
    
    def get_payments_by_order(self, order_id: str) -> List[Dict]:
        """Get all payments for a specific order"""
        payments = self.get_payments()
        return [p for p in payments if p.get('order_id') == order_id]
    
    def get_payments_by_customer(self, customer_phone: str) -> List[Dict]:
        """Get all payments for a specific customer"""
        payments = self.get_payments()
        return [p for p in payments if p.get('customer_phone') == customer_phone]
    
    def add_payment(self, payment: Dict) -> bool:
        """Add a new payment record"""
        payments = self.get_payments()
        
        # Generate new ID if not provided
        if 'payment_id' not in payment:
            existing_numbers = []
            for p in payments:
                payment_id = p.get('payment_id', '')
                if payment_id.startswith('PAY'):
                    try:
                        num = int(payment_id[3:])
                        existing_numbers.append(num)
                    except ValueError:
                        pass
            
            new_number = max(existing_numbers, default=0) + 1
            payment['payment_id'] = f"PAY{new_number:03d}"
        
        # Add timestamp
        if 'initiated_at' not in payment:
            payment['initiated_at'] = datetime.now().isoformat()
        
        payments.append(payment)
        return self.save_payments(payments)
    
    def update_payment_status(self, payment_id: str, status: str, **additional_fields) -> bool:
        """Update payment status and additional fields"""
        payments = self.get_payments()
        
        for i, payment in enumerate(payments):
            if payment.get('payment_id') == payment_id:
                payments[i]['status'] = status
                payments[i]['updated_at'] = datetime.now().isoformat()
                
                # Add status-specific timestamps and fields
                if status == 'completed':
                    payments[i]['completed_at'] = datetime.now().isoformat()
                elif status == 'failed':
                    payments[i]['failed_at'] = datetime.now().isoformat()
                elif status == 'cancelled':
                    payments[i]['cancelled_at'] = datetime.now().isoformat()
                
                # Add any additional fields
                for key, value in additional_fields.items():
                    payments[i][key] = value
                
                return self.save_payments(payments)
        
        print(f"❌ Payment with ID {payment_id} not found")
        return False
    
    # =============================================================================
    # ENHANCED ORDER METHODS FOR PAYMENT INTEGRATION
    # =============================================================================
    
    def update_order_payment_status(self, order_id: str, payment_status: str, payment_id: str = None) -> bool:
        """Update order payment status"""
        orders = self.get_orders()
        
        for i, order in enumerate(orders):
            if order.get('id') == order_id:
                orders[i]['payment_status'] = payment_status
                orders[i]['updated_at'] = datetime.now().isoformat()
                
                if payment_id:
                    orders[i]['payment_id'] = payment_id
                
                if payment_status == 'completed':
                    orders[i]['payment_completed_at'] = datetime.now().isoformat()
                
                return self.save_orders(orders)
        
        print(f"❌ Order with ID {order_id} not found")
        return False

# =============================================================================
# GLOBAL DATABASE INSTANCE
# =============================================================================

# Create a global instance for easy importing
db = JSONDatabase()

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_db() -> JSONDatabase:
    """Get the global database instance"""
    return db

def initialize_database(data_dir: str = "data") -> JSONDatabase:
    """Initialize database with custom data directory"""
    global db
    db = JSONDatabase(data_dir)
    return db

