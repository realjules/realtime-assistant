"""
Vendor Tools for Sasabot - Updated to use JSON Database with Enhanced Validation
Business management tools for adding, updating, and managing products
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the JSON database
from utils.simple_db import db

def validate_product_data(name: str, price: float, stock: int, 
                         category: str = "", description: str = "", 
                         brand: str = "", warranty: str = "") -> Dict[str, Any]:
    """
    Comprehensive validation for product data
    Returns validation result with detailed feedback
    """
    errors = []
    warnings = []
    
    # Name validation
    if not name or not name.strip():
        errors.append("Product name is required")
    elif len(name.strip()) < 3:
        errors.append("Product name must be at least 3 characters long")
    elif len(name.strip()) > 100:
        errors.append("Product name must be less than 100 characters")
    
    # Price validation
    try:
        price = float(price)
        if price <= 0:
            errors.append("Price must be greater than 0")
        elif price > 10000000:  # 10 million KSh
            warnings.append("Price seems very high, please confirm")
    except (ValueError, TypeError):
        errors.append("Price must be a valid number")
    
    # Stock validation
    try:
        stock = int(stock)
        if stock < 0:
            errors.append("Stock cannot be negative")
        elif stock == 0:
            warnings.append("Adding product with zero stock")
        elif stock > 10000:
            warnings.append("Stock quantity seems very high, please confirm")
    except (ValueError, TypeError):
        errors.append("Stock must be a valid integer")
    
    # Category validation
    valid_categories = ["Electronics", "Accessories", "Storage", "Audio", "Mobile", "Computing", "Gaming"]
    if not category or not category.strip():
        errors.append("Category is required")
    elif category.strip() not in valid_categories:
        warnings.append(f"Category '{category}' is not in standard list: {', '.join(valid_categories)}")
    
    # Description validation
    if not description or not description.strip():
        warnings.append("Product description is empty - consider adding details for better customer experience")
    elif len(description.strip()) < 10:
        warnings.append("Product description is very short - consider adding more details")
    
    # Brand validation
    if not brand or not brand.strip():
        warnings.append("Brand not specified - using 'Generic'")
        brand = "Generic"
    
    # Warranty validation
    if not warranty or not warranty.strip():
        warnings.append("Warranty period not specified - using '3 months'")
        warranty = "3 months"
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "validated_data": {
            "name": name.strip() if name else "",
            "price": float(price) if price else 0,
            "stock": int(stock) if stock else 0,
            "category": category.strip() if category else "Electronics",
            "description": description.strip() if description else "",
            "brand": brand.strip() if brand else "Generic",
            "warranty": warranty.strip() if warranty else "3 months"
        }
    }

def add_product_handler(business_id: str, name: str, price: float, stock: int, 
                       category: str = "Electronics", description: str = "", 
                       brand: str = "Generic", warranty: str = "3 months") -> Dict[str, Any]:
    """
    Add a new product to the business inventory with comprehensive validation
    Now requires all fields and validates them thoroughly
    """
    try:
        # Validate business exists
        business = db.get_business(business_id)
        if not business:
            return {
                "success": False,
                "message": f"Business with ID '{business_id}' not found",
                "error_type": "business_not_found",
                "data": None
            }
        
        # Comprehensive validation
        validation = validate_product_data(name, price, stock, category, description, brand, warranty)
        
        if not validation["valid"]:
            error_msg = "Cannot add product due to validation errors:\n"
            for error in validation["errors"]:
                error_msg += f"• {error}\n"
            
            return {
                "success": False,
                "message": error_msg.strip(),
                "error_type": "validation_error",
                "validation_errors": validation["errors"],
                "data": None
            }
        
        # Use validated data
        validated_data = validation["validated_data"]
        
        # Check if product with same name already exists for this business
        existing_product = db.find_product_by_name(validated_data["name"], business_id)
        if existing_product:
            return {
                "success": False,
                "message": f"Product '{validated_data['name']}' already exists for this business.\nExisting product ID: {existing_product.get('id')}\nWould you like to update the stock instead?",
                "error_type": "duplicate_product",
                "existing_product": existing_product,
                "data": None
            }
        
        # Generate SKU
        name_part = ''.join(validated_data["name"].upper().split()[:2])[:6]
        timestamp = datetime.now().strftime("%m%d")
        sku = f"{name_part}-{timestamp}"
        
        # Create new product with validated data
        new_product = {
            "name": validated_data["name"],
            "price": validated_data["price"],
            "stock": validated_data["stock"],
            "category": validated_data["category"],
            "business_id": business_id,
            "description": validated_data["description"],
            "sku": sku,
            "brand": validated_data["brand"],
            "warranty": validated_data["warranty"],
            "status": "active"
        }
        
        # Add product to database
        success = db.add_product(new_product)
        
        if success:
            # Get the saved product (with generated ID)
            saved_product = db.find_product_by_name(validated_data["name"], business_id)
            
            # Prepare success message with warnings if any
            message = f"✅ Product '{validated_data['name']}' added successfully!"
            
            if validation["warnings"]:
                message += "\n\n⚠️ Note:\n"
                for warning in validation["warnings"]:
                    message += f"• {warning}\n"
            
            message += f"\n📋 Product Details:\n"
            message += f"• ID: {saved_product.get('id')}\n"
            message += f"• Price: KSh {validated_data['price']:,}\n"
            message += f"• Stock: {validated_data['stock']} units\n"
            message += f"• Category: {validated_data['category']}\n"
            message += f"• Brand: {validated_data['brand']}\n"
            message += f"• Warranty: {validated_data['warranty']}\n"
            message += f"• SKU: {sku}"
            
            return {
                "success": True,
                "message": message,
                "warnings": validation["warnings"],
                "data": saved_product
            }
        else:
            return {
                "success": False,
                "message": "Failed to save product to database. Please try again.",
                "error_type": "database_error",
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error adding product: {str(e)}",
            "error_type": "system_error",
            "data": None
        }


def check_product_completeness(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if product data has all required fields for adding
    Returns what's missing and what's provided
    """
    required_fields = {
        "name": "Product name with specifications",
        "price": "Price in Kenyan Shillings",
        "stock": "Number of units in stock",
        "category": "Product category",
        "description": "Product description",
        "brand": "Product brand",
        "warranty": "Warranty period"
    }
    
    missing = []
    provided = {}
    
    for field, description in required_fields.items():
        if field in product_data and product_data[field] is not None and str(product_data[field]).strip():
            provided[field] = product_data[field]
        else:
            missing.append({"field": field, "description": description})
    
    return {
        "complete": len(missing) == 0,
        "missing_fields": missing,
        "provided_fields": provided,
        "completion_percentage": len(provided) / len(required_fields) * 100
    }


def suggest_product_details(partial_name: str) -> Dict[str, Any]:
    """
    Suggest product details based on partial name to help users
    """
    suggestions = {}
    
    name_lower = partial_name.lower()
    
    # Category suggestions
    if any(word in name_lower for word in ["phone", "smartphone", "mobile"]):
        suggestions["category"] = "Electronics"
        suggestions["warranty"] = "12 months"
        suggestions["example_description"] = "Latest smartphone with advanced features"
    elif any(word in name_lower for word in ["laptop", "computer", "pc"]):
        suggestions["category"] = "Computing"
        suggestions["warranty"] = "24 months"
        suggestions["example_description"] = "High-performance laptop for work and entertainment"
    elif any(word in name_lower for word in ["headphone", "earphone", "speaker"]):
        suggestions["category"] = "Audio"
        suggestions["warranty"] = "6 months"
        suggestions["example_description"] = "Premium audio device with superior sound quality"
    elif any(word in name_lower for word in ["cable", "charger", "adapter"]):
        suggestions["category"] = "Accessories"
        suggestions["warranty"] = "3 months"
        suggestions["example_description"] = "Quality accessory for your devices"
    else:
        suggestions["category"] = "Electronics"
        suggestions["warranty"] = "6 months"
        suggestions["example_description"] = "Quality product with reliable performance"
    
    # Brand suggestions
    if "iphone" in name_lower or "macbook" in name_lower or "ipad" in name_lower:
        suggestions["brand"] = "Apple"
    elif "samsung" in name_lower or "galaxy" in name_lower:
        suggestions["brand"] = "Samsung"
    elif "dell" in name_lower:
        suggestions["brand"] = "Dell"
    elif "hp" in name_lower:
        suggestions["brand"] = "HP"
    elif "sony" in name_lower:
        suggestions["brand"] = "Sony"
    else:
        suggestions["brand"] = "Generic"
    
    return suggestions


# Updated functions for realtime/vendor_tools.py

def update_product_handler(business_id: str, product_identifier: str, 
                          **updates) -> Dict[str, Any]:
    """
    Update an existing product with enhanced validation and LLM-friendly error responses
    """
    try:
        # Enhanced product validation with full context
        validation_result = db.validate_product_reference(product_identifier, business_id)
        
        if not validation_result["exists"]:
            # Return rich context for LLM processing
            context = validation_result["context"]
            
            return {
                "success": False,
                "message": f"Product '{product_identifier}' not found",
                "error_type": "product_not_found",
                "context": {
                    "user_input": product_identifier,
                    "available_products": context["all_products"],
                    "business_name": context["business_name"],
                    "total_products": context["total_count"],
                    "suggestion_prompt": f"User wants to update '{product_identifier}' but it doesn't exist. Help them find the right product from the available list.",
                    "quick_reference": db.get_product_quick_reference(business_id)
                },
                "data": None
            }
        
        product = validation_result["product"]
        
        # Validate updates (existing logic remains the same)
        valid_updates = {}
        validation_errors = []
        
        # Validate each update field
        if 'name' in updates:
            if not updates['name'] or not updates['name'].strip():
                validation_errors.append("Product name cannot be empty")
            elif len(updates['name'].strip()) < 3:
                validation_errors.append("Product name must be at least 3 characters")
            else:
                valid_updates['name'] = updates['name'].strip()
        
        if 'price' in updates:
            try:
                price = float(updates['price'])
                if price <= 0:
                    validation_errors.append("Price must be greater than 0")
                else:
                    valid_updates['price'] = price
            except (ValueError, TypeError):
                validation_errors.append("Invalid price format - must be a number")
        
        if 'stock' in updates:
            try:
                stock = int(updates['stock'])
                if stock < 0:
                    validation_errors.append("Stock cannot be negative")
                else:
                    valid_updates['stock'] = stock
            except (ValueError, TypeError):
                validation_errors.append("Invalid stock format - must be a whole number")
        
        # Update other fields if provided
        for field in ['category', 'description', 'brand', 'warranty']:
            if field in updates and updates[field] is not None:
                valid_updates[field] = str(updates[field]).strip()
        
        if validation_errors:
            return {
                "success": False,
                "message": "Validation errors",
                "error_type": "validation_error",
                "validation_errors": validation_errors,
                "context": {
                    "product_found": product,
                    "attempted_updates": updates,
                    "suggestion_prompt": "Help user fix these validation errors and retry the update."
                },
                "data": None
            }
        
        if not valid_updates:
            return {
                "success": False,
                "message": "No valid updates provided",
                "error_type": "no_updates",
                "context": {
                    "current_product": product,
                    "suggestion_prompt": "User didn't provide any valid updates. Show them the current product details and ask what they want to change."
                },
                "data": product
            }
        
        # Update product in database
        success = db.update_product(product['id'], valid_updates)
        
        if success:
            # Get updated product
            updated_product = db.get_product_by_id(product['id'])
            
            # Create detailed update message with prominent ID
            update_details = []
            for field, value in valid_updates.items():
                if field == 'price':
                    update_details.append(f"• {field.title()}: KSh {value:,}")
                else:
                    update_details.append(f"• {field.title()}: {value}")
            
            message = f"✅ Product updated successfully!\n\n"
            message += db.format_product_display(updated_product)
            message += f"\n\nChanges made:\n" + "\n".join(update_details)
            
            return {
                "success": True,
                "message": message,
                "updated_fields": list(valid_updates.keys()),
                "data": updated_product
            }
        else:
            return {
                "success": False,
                "message": "Failed to update product in database",
                "error_type": "database_error",
                "context": {
                    "product": product,
                    "attempted_updates": valid_updates,
                    "suggestion_prompt": "Database update failed. Suggest user to try again."
                },
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating product: {str(e)}",
            "error_type": "system_error",
            "context": {
                "user_input": product_identifier,
                "error_details": str(e),
                "suggestion_prompt": "System error occurred. Suggest user to try again or contact support."
            },
            "data": None
        }


def delete_product_handler(business_id: str, product_identifier: str) -> Dict[str, Any]:
    """
    Delete a product from inventory with enhanced validation and safety checks
    """
    try:
        # Enhanced product validation with full context
        validation_result = db.validate_product_reference(product_identifier, business_id)
        
        if not validation_result["exists"]:
            # Return rich context for LLM processing
            context = validation_result["context"]
            
            return {
                "success": False,
                "message": f"Product '{product_identifier}' not found",
                "error_type": "product_not_found",
                "context": {
                    "user_input": product_identifier,
                    "available_products": context["all_products"],
                    "business_name": context["business_name"],
                    "total_products": context["total_count"],
                    "suggestion_prompt": f"User wants to delete '{product_identifier}' but it doesn't exist. Help them find the right product from the available list.",
                    "quick_reference": db.get_product_quick_reference(business_id)
                },
                "data": None
            }
        
        product = validation_result["product"]
        
        # Safety check - warn if product has high value or stock
        warnings = []
        product_value = product.get('price', 0) * product.get('stock', 0)
        
        if product.get('stock', 0) > 10:
            warnings.append(f"Product has {product.get('stock')} units in stock")
        
        if product_value > 100000:  # 100k KSh
            warnings.append(f"Product inventory value is KSh {product_value:,}")
        
        # Store product info before deletion
        deleted_product = product.copy()
        
        # Delete product from database
        success = db.delete_product(product['id'])
        
        if success:
            message = f"✅ Product deleted successfully!\n\n"
            message += f"**Deleted Product:**\n{db.format_product_display(deleted_product)}"
            
            if warnings:
                message += f"\n\n⚠️ **Note:** This product had:\n" + "\n".join(f"• {warning}" for warning in warnings)
            
            message += f"\n\n💰 **Total Value Removed:** KSh {product_value:,}"
            
            return {
                "success": True,
                "message": message,
                "warnings": warnings,
                "data": deleted_product
            }
        else:
            return {
                "success": False,
                "message": "Failed to delete product from database",
                "error_type": "database_error",
                "context": {
                    "product": product,
                    "suggestion_prompt": "Database deletion failed. Suggest user to try again."
                },
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting product: {str(e)}",
            "error_type": "system_error",
            "context": {
                "user_input": product_identifier,
                "error_details": str(e),
                "suggestion_prompt": "System error occurred. Suggest user to try again or contact support."
            },
            "data": None
        }


def show_products_handler(business_id: str, category: str = None, 
                         search_term: str = None) -> Dict[str, Any]:
    """
    Display products for a business with enhanced formatting and prominent IDs
    """
    try:
        # Validate business exists
        business = db.get_business(business_id)
        if not business:
            return {
                "success": False,
                "message": f"Business with ID '{business_id}' not found",
                "error_type": "business_not_found",
                "data": None
            }
        
        # Get products for this business
        products = db.get_products_by_business(business_id)
        
        if not products:
            return {
                "success": True,
                "message": f"No products found for {business['name']}.\n\n💡 Try adding some products to get started!\n\nUse: 'Add product [name] [price] [stock] [category] [description] [brand] [warranty]'",
                "data": {
                    "business": business,
                    "products": [],
                    "total_products": 0,
                    "total_value": 0
                }
            }
        
        # Filter by category if specified
        if category:
            original_count = len(products)
            products = [p for p in products if p.get('category', '').lower() == category.lower()]
            if len(products) == 0:
                available_categories = list(set(p.get('category', 'Unknown') for p in db.get_products_by_business(business_id)))
                return {
                    "success": True,
                    "message": f"No products found in category '{category}'.\n\n**Available categories:** {', '.join(available_categories)}",
                    "context": {
                        "available_categories": available_categories,
                        "suggestion_prompt": f"User searched for category '{category}' but none found. Show available categories."
                    },
                    "data": {
                        "business": business,
                        "products": [],
                        "available_categories": available_categories,
                        "total_products": 0,
                        "total_value": 0
                    }
                }
        
        # Filter by search term if specified
        if search_term:
            original_count = len(products)
            search_lower = search_term.lower()
            products = [
                p for p in products 
                if search_lower in p.get('name', '').lower() 
                or search_lower in p.get('description', '').lower()
                or search_lower in p.get('brand', '').lower()
            ]
            
            if len(products) == 0:
                # Get context for LLM to suggest alternatives
                context = db.get_contextual_product_info(business_id, search_term)
                
                return {
                    "success": True,
                    "message": f"No products found matching '{search_term}'",
                    "context": {
                        "search_term": search_term,
                        "available_products": context["all_products"],
                        "suggestion_prompt": f"User searched for '{search_term}' but no matches found. Help them find similar products."
                    },
                    "data": {
                        "business": business,
                        "products": [],
                        "search_term": search_term,
                        "total_products": 0,
                        "total_value": 0
                    }
                }
        
        # Calculate totals and analytics
        total_products = len(products)
        total_value = sum(p.get('price', 0) * p.get('stock', 0) for p in products)
        low_stock_count = len([p for p in products if p.get('stock', 0) <= 5])
        out_of_stock_count = len([p for p in products if p.get('stock', 0) == 0])
        
        # Sort products by name
        products.sort(key=lambda x: x.get('name', '').lower())
        
        # Format products with prominent IDs
        formatted_products = []
        for product in products:
            formatted_products.append({
                "display": db.format_product_display(product),
                "data": product
            })
        
        return {
            "success": True,
            "message": f"📋 **{business['name']} - Product Inventory**\n\nFound {total_products} products",
            "data": {
                "business": business,
                "products": products,
                "formatted_products": formatted_products,
                "total_products": total_products,
                "total_value": total_value,
                "low_stock_count": low_stock_count,
                "out_of_stock_count": out_of_stock_count,
                "filters": {
                    "category": category,
                    "search_term": search_term
                },
                "analytics": {
                    "total_inventory_value": total_value,
                    "average_product_price": sum(p.get('price', 0) for p in products) / len(products) if products else 0,
                    "total_stock_units": sum(p.get('stock', 0) for p in products)
                },
                "quick_reference": db.get_product_quick_reference(business_id)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving products: {str(e)}",
            "error_type": "system_error",
            "context": {
                "error_details": str(e),
                "suggestion_prompt": "System error occurred while fetching products. Suggest user to try again."
            },
            "data": None
        }

# Rest of the functions remain the same...
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
                "error_type": "validation_error",
                "data": None
            }
        
        return update_product_handler(business_id, product_identifier, stock=new_stock)
        
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Invalid stock value - must be a whole number",
            "error_type": "validation_error",
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
            "message": f"Found {len(low_stock_products)} products with low stock (≤{threshold} units)",
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
            "error_type": "system_error",
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
                "error_type": "business_not_found",
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
            "error_type": "system_error",
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
                "error_type": "no_products",
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
            "error_type": "system_error",
            "data": None
        }


# =============================================================================
# TOOL DEFINITIONS FOR REGISTRY - UPDATED
# =============================================================================

vendor_tools = [
    {
        "name": "validate_product_data",
        "description": "Validate product information before adding to inventory",
        "handler": validate_product_data,
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Complete product name"},
                "price": {"type": "number", "description": "Product price"},
                "stock": {"type": "integer", "description": "Stock quantity"},
                "category": {"type": "string", "description": "Product category"},
                "description": {"type": "string", "description": "Product description"},
                "brand": {"type": "string", "description": "Product brand"},
                "warranty": {"type": "string", "description": "Warranty period"}
            },
            "required": ["name", "price", "stock"]
        }
    },
    {
        "name": "check_product_completeness",
        "description": "Check if product data has all required fields",
        "handler": check_product_completeness,
        "parameters": {
            "type": "object",
            "properties": {
                "product_data": {"type": "object", "description": "Product data to check"}
            },
            "required": ["product_data"]
        }
    },
    {
        "name": "suggest_product_details",
        "description": "Suggest product details based on partial name",
        "handler": suggest_product_details,
        "parameters": {
            "type": "object",
            "properties": {
                "partial_name": {"type": "string", "description": "Partial product name"}
            },
            "required": ["partial_name"]
        }
    },
    {
        "name": "add_product",
        "description": "Add a new product to business inventory. ALL fields are required.",
        "handler": add_product_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string", "description": "Business ID"},
                "name": {"type": "string", "description": "Complete product name with specifications"},
                "price": {"type": "number", "description": "Product price in KSh"},
                "stock": {"type": "integer", "description": "Stock quantity"},
                "category": {"type": "string", "description": "Product category"},
                "description": {"type": "string", "description": "Detailed product description"},
                "brand": {"type": "string", "description": "Product brand"},
                "warranty": {"type": "string", "description": "Warranty period"}
            },
            "required": ["business_id", "name", "price", "stock", "category", "description", "brand", "warranty"]
        }
    },
    {
        "name": "show_products", 
        "description": "Display all products for a business with analytics",
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
        "description": "Update an existing product with validation",
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
        "description": "Delete a product from inventory with safety checks",
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
        "description": "Get comprehensive business statistics and analytics",
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
        "description": "Get products with low stock levels",
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