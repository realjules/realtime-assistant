"""
Vendor Tools for Sasabot - Updated to use JSON Database
Business management tools for adding, updating, and managing products
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the JSON database
from utils.simple_db import db

def add_product_handler(business_id: str, name: str, price: float, stock: int, 
                       category: str = "Electronics", description: str = "", 
                       brand: str = "Generic", warranty: str = "3 months") -> Dict[str, Any]:
    """
    Add a new product to the business inventory
    Now saves directly to JSON database
    """
    try:
        # Validate business exists
        business = db.get_business(business_id)
        if not business:
            return {
                "success": False,
                "message": f"Business with ID '{business_id}' not found",
                "data": None
            }
        
        # Validate input data
        if not name or not name.strip():
            return {
                "success": False,
                "message": "Product name cannot be empty",
                "data": None
            }
        
        if price <= 0:
            return {
                "success": False,
                "message": "Product price must be greater than 0",
                "data": None
            }
        
        if stock < 0:
            return {
                "success": False,
                "message": "Stock cannot be negative",
                "data": None
            }
        
        # Check if product with same name already exists for this business
        existing_product = db.find_product_by_name(name.strip(), business_id)
        if existing_product:
            return {
                "success": False,
                "message": f"Product '{name}' already exists for this business",
                "data": existing_product
            }
        
        # Generate SKU
        name_part = ''.join(name.upper().split()[:2])[:6]
        timestamp = datetime.now().strftime("%m%d")
        sku = f"{name_part}-{timestamp}"
        
        # Create new product
        new_product = {
            "name": name.strip(),
            "price": float(price),
            "stock": int(stock),
            "category": category.strip(),
            "business_id": business_id,
            "description": description.strip(),
            "sku": sku,
            "brand": brand.strip(),
            "warranty": warranty.strip(),
            "status": "active"
        }
        
        # Add product to database
        success = db.add_product(new_product)
        
        if success:
            # Get the saved product (with generated ID)
            saved_product = db.find_product_by_name(name.strip(), business_id)
            
            return {
                "success": True,
                "message": f"Product '{name}' added successfully",
                "data": saved_product
            }
        else:
            return {
                "success": False,
                "message": "Failed to save product to database",
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error adding product: {str(e)}",
            "data": None
        }


def update_product_handler(business_id: str, product_identifier: str, 
                          **updates) -> Dict[str, Any]:
    """
    Update an existing product
    Now saves changes directly to JSON database
    """
    try:
        # Find the product by ID or name
        product = None
        
        # Try finding by ID first
        if product_identifier.isdigit():
            product = db.get_product_by_id(product_identifier)
        
        # If not found by ID, try by name
        if not product:
            product = db.find_product_by_name(product_identifier, business_id)
        
        if not product:
            return {
                "success": False,
                "message": f"Product '{product_identifier}' not found",
                "data": None
            }
        
        # Check if product belongs to the business
        if product.get('business_id') != business_id:
            return {
                "success": False,
                "message": "You can only update products from your own business",
                "data": None
            }
        
        # Prepare updates
        valid_updates = {}
        
        # Validate and prepare updates
        if 'name' in updates:
            if not updates['name'] or not updates['name'].strip():
                return {
                    "success": False,
                    "message": "Product name cannot be empty",
                    "data": None
                }
            valid_updates['name'] = updates['name'].strip()
        
        if 'price' in updates:
            try:
                price = float(updates['price'])
                if price <= 0:
                    return {
                        "success": False,
                        "message": "Price must be greater than 0",
                        "data": None
                    }
                valid_updates['price'] = price
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "message": "Invalid price format",
                    "data": None
                }
        
        if 'stock' in updates:
            try:
                stock = int(updates['stock'])
                if stock < 0:
                    return {
                        "success": False,
                        "message": "Stock cannot be negative",
                        "data": None
                    }
                valid_updates['stock'] = stock
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "message": "Invalid stock format",
                    "data": None
                }
        
        # Update other fields if provided
        for field in ['category', 'description', 'brand', 'warranty']:
            if field in updates:
                valid_updates[field] = str(updates[field]).strip()
        
        if not valid_updates:
            return {
                "success": False,
                "message": "No valid updates provided",
                "data": product
            }
        
        # Update product in database
        success = db.update_product(product['id'], valid_updates)
        
        if success:
            # Get updated product
            updated_product = db.get_product_by_id(product['id'])
            
            return {
                "success": True,
                "message": f"Product '{product['name']}' updated successfully",
                "data": updated_product
            }
        else:
            return {
                "success": False,
                "message": "Failed to update product in database",
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating product: {str(e)}",
            "data": None
        }


def delete_product_handler(business_id: str, product_identifier: str) -> Dict[str, Any]:
    """
    Delete a product from inventory
    Now removes from JSON database
    """
    try:
        # Find the product by ID or name
        product = None
        
        # Try finding by ID first
        if product_identifier.isdigit():
            product = db.get_product_by_id(product_identifier)
        
        # If not found by ID, try by name
        if not product:
            product = db.find_product_by_name(product_identifier, business_id)
        
        if not product:
            return {
                "success": False,
                "message": f"Product '{product_identifier}' not found",
                "data": None
            }
        
        # Check if product belongs to the business
        if product.get('business_id') != business_id:
            return {
                "success": False,
                "message": "You can only delete products from your own business",
                "data": None
            }
        
        # Store product info before deletion
        deleted_product = product.copy()
        
        # Delete product from database
        success = db.delete_product(product['id'])
        
        if success:
            return {
                "success": True,
                "message": f"Product '{product['name']}' deleted successfully",
                "data": deleted_product
            }
        else:
            return {
                "success": False,
                "message": "Failed to delete product from database",
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting product: {str(e)}",
            "data": None
        }


def show_products_handler(business_id: str, category: str = None, 
                         search_term: str = None) -> Dict[str, Any]:
    """
    Display products for a business
    Now loads fresh data from JSON database
    """
    try:
        # Validate business exists
        business = db.get_business(business_id)
        if not business:
            return {
                "success": False,
                "message": f"Business with ID '{business_id}' not found",
                "data": None
            }
        
        # Get products for this business
        products = db.get_products_by_business(business_id)
        
        if not products:
            return {
                "success": True,
                "message": f"No products found for {business['name']}",
                "data": {
                    "business": business,
                    "products": [],
                    "total_products": 0,
                    "total_value": 0
                }
            }
        
        # Filter by category if specified
        if category:
            products = [p for p in products if p.get('category', '').lower() == category.lower()]
        
        # Filter by search term if specified
        if search_term:
            search_lower = search_term.lower()
            products = [
                p for p in products 
                if search_lower in p.get('name', '').lower() 
                or search_lower in p.get('description', '').lower()
                or search_lower in p.get('brand', '').lower()
            ]
        
        # Calculate totals
        total_products = len(products)
        total_value = sum(p.get('price', 0) * p.get('stock', 0) for p in products)
        
        # Sort products by name
        products.sort(key=lambda x: x.get('name', '').lower())
        
        return {
            "success": True,
            "message": f"Found {total_products} products for {business['name']}",
            "data": {
                "business": business,
                "products": products,
                "total_products": total_products,
                "total_value": total_value,
                "filters": {
                    "category": category,
                    "search_term": search_term
                }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving products: {str(e)}",
            "data": None
        }


def update_stock_handler(business_id: str, product_identifier: str, 
                        new_stock: int) -> Dict[str, Any]:
    """
    Update product stock level
    Convenience function for stock management
    """
    try:
        new_stock = int(new_stock)
        if new_stock < 0:
            return {
                "success": False,
                "message": "Stock cannot be negative",
                "data": None
            }
        
        return update_product_handler(business_id, product_identifier, stock=new_stock)
        
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Invalid stock value",
            "data": None
        }


def get_low_stock_products(business_id: str, threshold: int = 5) -> Dict[str, Any]:
    """
    Get products with low stock levels
    """
    try:
        # Get all products for the business
        products = db.get_products_by_business(business_id)
        
        # Filter for low stock products
        low_stock_products = [
            p for p in products 
            if p.get('stock', 0) <= threshold and p.get('status') == 'active'
        ]
        
        # Sort by stock level (lowest first)
        low_stock_products.sort(key=lambda x: x.get('stock', 0))
        
        business = db.get_business(business_id)
        business_name = business['name'] if business else 'Unknown Business'
        
        return {
            "success": True,
            "message": f"Found {len(low_stock_products)} products with low stock",
            "data": {
                "business_name": business_name,
                "threshold": threshold,
                "low_stock_products": low_stock_products,
                "count": len(low_stock_products)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error checking stock levels: {str(e)}",
            "data": None
        }


def get_business_stats(business_id: str) -> Dict[str, Any]:
    """
    Get business statistics
    """
    try:
        business = db.get_business(business_id)
        if not business:
            return {
                "success": False,
                "message": f"Business with ID '{business_id}' not found",
                "data": None
            }
        
        # Get products and orders
        products = db.get_products_by_business(business_id)
        orders = db.get_orders_by_business(business_id)
        
        # Calculate product stats
        total_products = len(products)
        active_products = len([p for p in products if p.get('status') == 'active'])
        total_inventory_value = sum(p.get('price', 0) * p.get('stock', 0) for p in products)
        low_stock_count = len([p for p in products if p.get('stock', 0) <= 5])
        
        # Calculate order stats
        total_orders = len(orders)
        completed_orders = len([o for o in orders if o.get('status') == 'delivered'])
        pending_orders = len([o for o in orders if o.get('status') in ['pending', 'processing', 'confirmed']])
        total_revenue = sum(o.get('grand_total', 0) for o in orders if o.get('status') == 'delivered')
        
        # Get categories
        categories = list(set(p.get('category', 'Uncategorized') for p in products))
        
        return {
            "success": True,
            "message": f"Statistics for {business['name']}",
            "data": {
                "business": business,
                "products": {
                    "total": total_products,
                    "active": active_products,
                    "low_stock": low_stock_count,
                    "categories": categories,
                    "inventory_value": total_inventory_value
                },
                "orders": {
                    "total": total_orders,
                    "completed": completed_orders,
                    "pending": pending_orders,
                    "total_revenue": total_revenue
                },
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating statistics: {str(e)}",
            "data": None
        }


def bulk_update_prices(business_id: str, price_adjustment: float, 
                      adjustment_type: str = "percentage") -> Dict[str, Any]:
    """
    Bulk update prices for all products in a business
    adjustment_type: 'percentage' or 'fixed'
    """
    try:
        products = db.get_products_by_business(business_id)
        
        if not products:
            return {
                "success": False,
                "message": "No products found for this business",
                "data": None
            }
        
        updated_count = 0
        errors = []
        
        for product in products:
            try:
                current_price = product.get('price', 0)
                
                if adjustment_type == "percentage":
                    new_price = current_price * (1 + price_adjustment / 100)
                else:  # fixed amount
                    new_price = current_price + price_adjustment
                
                # Ensure price doesn't go below 0
                new_price = max(0, round(new_price, 2))
                
                # Update the product
                success = db.update_product(product['id'], {'price': new_price})
                if success:
                    updated_count += 1
                else:
                    errors.append(f"Failed to update {product['name']}")
                    
            except Exception as e:
                errors.append(f"Error updating {product['name']}: {str(e)}")
        
        return {
            "success": updated_count > 0,
            "message": f"Updated {updated_count} products. {len(errors)} errors.",
            "data": {
                "updated_count": updated_count,
                "total_products": len(products),
                "errors": errors,
                "adjustment": {
                    "value": price_adjustment,
                    "type": adjustment_type
                }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in bulk price update: {str(e)}",
            "data": None
        }


# =============================================================================
# TOOL DEFINITIONS FOR REGISTRY
# =============================================================================

vendor_tools = [
    {
        "name": "add_product",
        "description": "Add a new product to business inventory. Saves to JSON database.",
        "handler": add_product_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string", "description": "Business ID"},
                "name": {"type": "string", "description": "Product name"},
                "price": {"type": "number", "description": "Product price"},
                "stock": {"type": "integer", "description": "Stock quantity"},
                "category": {"type": "string", "description": "Product category", "default": "Electronics"},
                "description": {"type": "string", "description": "Product description", "default": ""},
                "brand": {"type": "string", "description": "Product brand", "default": "Generic"},
                "warranty": {"type": "string", "description": "Warranty period", "default": "3 months"}
            },
            "required": ["business_id", "name", "price", "stock"]
        }
    },
    {
        "name": "show_products", 
        "description": "Display all products for a business. Loads from JSON database.",
        "handler": show_products_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string", "description": "Business ID"},
                "category": {"type": "string", "description": "Filter by category"},
                "search_term": {"type": "string", "description": "Search term"}
            },
            "required": ["business_id"]
        }
    },
    {
        "name": "update_product",
        "description": "Update an existing product. Saves changes to JSON database.",
        "handler": update_product_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string", "description": "Business ID"},
                "product_identifier": {"type": "string", "description": "Product ID or name"},
                "name": {"type": "string", "description": "New product name"},
                "price": {"type": "number", "description": "New price"},
                "stock": {"type": "integer", "description": "New stock quantity"},
                "category": {"type": "string", "description": "New category"},
                "description": {"type": "string", "description": "New description"},
                "brand": {"type": "string", "description": "New brand"},
                "warranty": {"type": "string", "description": "New warranty"}
            },
            "required": ["business_id", "product_identifier"]
        }
    },
    {
        "name": "delete_product",
        "description": "Delete a product from inventory. Removes from JSON database.",
        "handler": delete_product_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string", "description": "Business ID"},
                "product_identifier": {"type": "string", "description": "Product ID or name to delete"}
            },
            "required": ["business_id", "product_identifier"]
        }
    },
    {
        "name": "get_business_stats",
        "description": "Get comprehensive business statistics and analytics.",
        "handler": get_business_stats,
        "parameters": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string", "description": "Business ID"}
            },
            "required": ["business_id"]
        }
    },
    {
        "name": "get_low_stock_products",
        "description": "Get products with low stock levels.",
        "handler": get_low_stock_products,
        "parameters": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string", "description": "Business ID"},
                "threshold": {"type": "integer", "description": "Stock threshold", "default": 5}
            },
            "required": ["business_id"]
        }
    }
]