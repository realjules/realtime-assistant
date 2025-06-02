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