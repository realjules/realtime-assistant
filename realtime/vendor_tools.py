"""
Vendor Tools for Sasabot - Updated to use JSON Database with Enhanced Validation
Business management tools for adding, updating, managing products and basic performance analystics
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics


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
    Redirects to enhanced version for backward compatibility
    """
    return get_enhanced_business_stats(business_id)

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


def get_enhanced_business_stats(business_id: str) -> Dict[str, Any]:
    """
    Enhanced business statistics with comprehensive analytics
    Replaces the existing get_business_stats function
    """
    try:
        business = db.get_business(business_id)
        if not business:
            return {
                "success": False,
                "message": f"Business with ID '{business_id}' not found",
                "error_type": "business_not_found"
            }
        
        # Get data
        products = db.get_products_by_business(business_id)
        orders = db.get_orders_by_business(business_id)
        
        # Calculate all metrics
        core_metrics = _calculate_core_metrics(products, orders)
        revenue_trends = _calculate_revenue_trends(orders)
        top_products = _get_top_selling_products(orders)
        customer_metrics = _calculate_customer_metrics(orders)
        order_performance = _calculate_order_performance(orders)
        stock_alerts = _calculate_stock_alerts(products, orders)
        
        return {
            "success": True,
            "business_info": {
                "business_id": business_id,
                "business_name": business.get('name', 'Unknown Business'),
                "location": business.get('location', 'Unknown'),
                "phone": business.get('phone', 'N/A'),
                "analysis_date": datetime.now().isoformat()
            },
            "core_metrics": core_metrics,
            "revenue_trends": revenue_trends,
            "top_products": top_products,
            "customer_metrics": customer_metrics,
            "order_performance": order_performance,
            "stock_alerts": stock_alerts,
            "insights": _generate_business_insights(core_metrics, revenue_trends, top_products, stock_alerts)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error calculating enhanced business stats: {str(e)}",
            "error_type": "system_error"
        }


def get_sales_analytics(business_id: str, period: str = "monthly") -> Dict[str, Any]:
    """
    Comprehensive sales analytics and performance analysis
    """
    try:
        business = db.get_business(business_id)
        if not business:
            return {
                "success": False,
                "message": f"Business with ID '{business_id}' not found",
                "error_type": "business_not_found"
            }
        
        # Get filtered data based on period
        orders = db.get_orders_by_business(business_id)
        filtered_orders = _filter_orders_by_period(orders, period)
        
        if not filtered_orders:
            return {
                "success": True,
                "message": f"No sales data found for {period} period",
                "data": {
                    "business_name": business.get('name'),
                    "period": period,
                    "no_data": True
                }
            }
        
        # Calculate analytics
        best_performers = _analyze_product_performance(filtered_orders, "best")
        worst_performers = _analyze_product_performance(filtered_orders, "worst")
        category_performance = _analyze_category_performance(filtered_orders)
        daily_patterns = _analyze_daily_patterns(filtered_orders)
        payment_breakdown = _analyze_payment_methods(filtered_orders)
        
        return {
            "success": True,
            "business_info": {
                "business_name": business.get('name'),
                "period": period,
                "analysis_date": datetime.now().isoformat(),
                "orders_analyzed": len(filtered_orders)
            },
            "best_performers": best_performers,
            "worst_performers": worst_performers,
            "category_performance": category_performance,
            "daily_patterns": daily_patterns,
            "payment_breakdown": payment_breakdown,
            "sales_insights": _generate_sales_insights(
                best_performers, category_performance, daily_patterns, payment_breakdown
            )
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error calculating sales analytics: {str(e)}",
            "error_type": "system_error"
        }


# Helper functions for calculations

def _calculate_core_metrics(products: List[Dict], orders: List[Dict]) -> Dict[str, Any]:
    """Calculate core business metrics"""
    completed_orders = [o for o in orders if o.get('status') == 'delivered']
    total_revenue = sum(o.get('grand_total', 0) for o in completed_orders)
    
    return {
        "total_products": len(products),
        "active_products": len([p for p in products if p.get('status') == 'active']),
        "total_orders": len(orders),
        "completed_orders": len(completed_orders),
        "pending_orders": len([o for o in orders if o.get('status') in ['pending', 'confirmed', 'processing']]),
        "total_revenue": total_revenue,
        "completion_rate": (len(completed_orders) / len(orders) * 100) if orders else 0,
        "average_order_value": total_revenue / len(completed_orders) if completed_orders else 0
    }


def _calculate_revenue_trends(orders: List[Dict]) -> Dict[str, Any]:
    """Calculate revenue trends for last 30 days"""
    try:
        # Get orders from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        sixty_days_ago = datetime.now() - timedelta(days=60)
        
        recent_orders = []
        previous_orders = []
        
        for order in orders:
            if order.get('status') == 'delivered':
                try:
                    order_date = datetime.fromisoformat(order.get('created_at', ''))
                    if order_date >= thirty_days_ago:
                        recent_orders.append(order)
                    elif order_date >= sixty_days_ago:
                        previous_orders.append(order)
                except (ValueError, TypeError):
                    continue
        
        # Calculate weekly breakdown for last 30 days
        weekly_revenue = _group_orders_by_week(recent_orders)
        
        # Calculate growth
        recent_revenue = sum(o.get('grand_total', 0) for o in recent_orders)
        previous_revenue = sum(o.get('grand_total', 0) for o in previous_orders)
        
        growth_percentage = 0
        if previous_revenue > 0:
            growth_percentage = ((recent_revenue - previous_revenue) / previous_revenue) * 100
        
        # Find best performing week
        best_week = "Week 1"
        if weekly_revenue:
            best_week_index = weekly_revenue.index(max(weekly_revenue))
            best_week = f"Week {best_week_index + 1}"
        
        return {
            "last_30_days_revenue": recent_revenue,
            "weekly_breakdown": weekly_revenue,
            "growth_percentage": round(growth_percentage, 1),
            "best_week": best_week,
            "total_orders_30_days": len(recent_orders)
        }
        
    except Exception as e:
        return {
            "last_30_days_revenue": 0,
            "weekly_breakdown": [0, 0, 0, 0],
            "growth_percentage": 0,
            "best_week": "Week 1",
            "total_orders_30_days": 0,
            "error": str(e)
        }


def _get_top_selling_products(orders: List[Dict], limit: int = 5) -> List[Dict]:
    """Get top selling products by revenue"""
    product_performance = defaultdict(lambda: {"units_sold": 0, "revenue": 0, "orders": 0})
    
    # Aggregate sales data
    for order in orders:
        if order.get('status') == 'delivered':
            for item in order.get('items', []):
                product_name = item.get('product_name', 'Unknown Product')
                product_id = item.get('product_id', 'N/A')
                quantity = item.get('quantity', 0)
                revenue = item.get('total_price', 0)
                
                product_performance[product_name]["units_sold"] += quantity
                product_performance[product_name]["revenue"] += revenue
                product_performance[product_name]["orders"] += 1
                product_performance[product_name]["product_id"] = product_id
    
    # Get current stock levels
    products = db.get_products()
    stock_lookup = {p.get('name', ''): p.get('stock', 0) for p in products}
    
    # Sort by revenue and format
    top_products = []
    sorted_products = sorted(
        product_performance.items(),
        key=lambda x: x[1]["revenue"],
        reverse=True
    )
    
    for i, (product_name, stats) in enumerate(sorted_products[:limit]):
        current_stock = stock_lookup.get(product_name, 0)
        
        top_products.append({
            "rank": i + 1,
            "product_name": product_name,
            "product_id": stats.get("product_id", "N/A"),
            "units_sold": stats["units_sold"],
            "revenue": stats["revenue"],
            "orders": stats["orders"],
            "current_stock": current_stock,
            "stock_status": "critical" if current_stock <= 2 else "low" if current_stock <= 5 else "ok"
        })
    
    return top_products


def _calculate_customer_metrics(orders: List[Dict]) -> Dict[str, Any]:
    """Calculate customer-related metrics"""
    if not orders:
        return {
            "total_customers": 0,
            "new_customers": 0,
            "repeat_customers": 0,
            "retention_rate": 0,
            "avg_orders_per_customer": 0,
            "top_locations": []
        }
    
    # Group orders by customer phone
    customers = defaultdict(list)
    for order in orders:
        phone = order.get('customer_phone', 'unknown')
        customers[phone].append(order)
    
    # Calculate metrics
    total_customers = len(customers)
    repeat_customers = len([phone for phone, orders in customers.items() if len(orders) > 1])
    
    # Get customers from last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_customers = 0
    
    for phone, customer_orders in customers.items():
        # Sort orders by date and check if first order was in last 30 days
        sorted_orders = sorted(customer_orders, key=lambda x: x.get('created_at', ''))
        if sorted_orders:
            try:
                first_order_date = datetime.fromisoformat(sorted_orders[0].get('created_at', ''))
                if first_order_date >= thirty_days_ago:
                    new_customers += 1
            except (ValueError, TypeError):
                continue
    
    # Top delivery locations
    locations = Counter()
    for order in orders:
        address = order.get('delivery_address', 'Unknown')
        # Extract area/neighborhood (first part before comma)
        area = address.split(',')[0].strip() if ',' in address else address
        locations[area] += 1
    
    top_locations = [{"area": area, "orders": count} for area, count in locations.most_common(3)]
    
    return {
        "total_customers": total_customers,
        "new_customers": new_customers,
        "repeat_customers": repeat_customers,
        "retention_rate": round((repeat_customers / total_customers * 100), 1) if total_customers > 0 else 0,
        "avg_orders_per_customer": round(len(orders) / total_customers, 1) if total_customers > 0 else 0,
        "top_locations": top_locations
    }


def _calculate_order_performance(orders: List[Dict]) -> Dict[str, Any]:
    """Calculate order fulfillment and performance metrics"""
    if not orders:
        return {
            "completion_rate": 0,
            "avg_processing_hours": 0,
            "pending_orders": 0,
            "payment_success_rate": 0
        }
    
    # Status analysis
    status_counts = Counter(o.get('status', 'unknown') for o in orders)
    completed = status_counts.get('delivered', 0)
    pending = status_counts.get('pending', 0) + status_counts.get('confirmed', 0) + status_counts.get('processing', 0)
    
    # Processing time analysis
    processing_times = []
    for order in orders:
        if order.get('status') == 'delivered' and order.get('created_at') and order.get('delivered_at'):
            try:
                created = datetime.fromisoformat(order['created_at'])
                delivered = datetime.fromisoformat(order['delivered_at'])
                hours = (delivered - created).total_seconds() / 3600
                processing_times.append(hours)
            except (ValueError, TypeError):
                continue
    
    # Payment success rate
    payment_successful = len([o for o in orders if o.get('payment_status') != 'failed'])
    payment_success_rate = (payment_successful / len(orders) * 100) if orders else 0
    
    return {
        "completion_rate": round((completed / len(orders) * 100), 1) if orders else 0,
        "avg_processing_hours": round(statistics.mean(processing_times), 1) if processing_times else 0,
        "pending_orders": pending,
        "payment_success_rate": round(payment_success_rate, 1),
        "status_distribution": dict(status_counts)
    }


def _calculate_stock_alerts(products: List[Dict], orders: List[Dict]) -> List[Dict]:
    """Calculate stock alerts with sales velocity"""
    alerts = []
    
    # Calculate sales velocity for each product
    product_velocity = _calculate_sales_velocity(orders)
    
    for product in products:
        if product.get('status') != 'active':
            continue
            
        product_name = product.get('name', '')
        current_stock = product.get('stock', 0)
        velocity = product_velocity.get(product_name, 0)  # units per week
        
        # Calculate weeks of stock remaining
        weeks_remaining = current_stock / velocity if velocity > 0 else float('inf')
        
        # Determine priority
        priority = "ok"
        if current_stock == 0:
            priority = "out_of_stock"
        elif weeks_remaining <= 1:
            priority = "critical"
        elif weeks_remaining <= 2:
            priority = "warning"
        elif current_stock <= 5:
            priority = "low"
        
        if priority in ["critical", "warning", "low", "out_of_stock"]:
            alerts.append({
                "product_name": product_name,
                "product_id": product.get('id'),
                "current_stock": current_stock,
                "weekly_velocity": round(velocity, 1),
                "weeks_remaining": round(weeks_remaining, 1) if weeks_remaining != float('inf') else "No recent sales",
                "priority": priority,
                "recommendation": _get_stock_recommendation(current_stock, velocity, priority)
            })
    
    # Sort by priority
    priority_order = {"out_of_stock": 0, "critical": 1, "warning": 2, "low": 3}
    alerts.sort(key=lambda x: priority_order.get(x["priority"], 4))
    
    return alerts


def _calculate_sales_velocity(orders: List[Dict]) -> Dict[str, float]:
    """Calculate weekly sales velocity for products"""
    # Get orders from last 8 weeks for velocity calculation
    eight_weeks_ago = datetime.now() - timedelta(weeks=8)
    
    product_sales = defaultdict(int)
    valid_orders = 0
    
    for order in orders:
        if order.get('status') == 'delivered':
            try:
                order_date = datetime.fromisoformat(order.get('created_at', ''))
                if order_date >= eight_weeks_ago:
                    valid_orders += 1
                    for item in order.get('items', []):
                        product_name = item.get('product_name', '')
                        quantity = item.get('quantity', 0)
                        product_sales[product_name] += quantity
            except (ValueError, TypeError):
                continue
    
    # Calculate weekly velocity (total sales / 8 weeks)
    velocity = {}
    for product_name, total_sold in product_sales.items():
        velocity[product_name] = total_sold / 8  # weekly velocity
    
    return velocity


def _filter_orders_by_period(orders: List[Dict], period: str) -> List[Dict]:
    """Filter orders by specified period"""
    now = datetime.now()
    
    if period == "daily":
        start_date = now - timedelta(days=1)
    elif period == "weekly":
        start_date = now - timedelta(weeks=1)
    elif period == "monthly":
        start_date = now - timedelta(days=30)
    elif period == "quarterly":
        start_date = now - timedelta(days=90)
    else:  # all time
        return orders
    
    filtered_orders = []
    for order in orders:
        try:
            order_date = datetime.fromisoformat(order.get('created_at', ''))
            if order_date >= start_date:
                filtered_orders.append(order)
        except (ValueError, TypeError):
            continue
    
    return filtered_orders


def _analyze_product_performance(orders: List[Dict], analysis_type: str) -> List[Dict]:
    """Analyze product performance - best or worst performers"""
    product_stats = defaultdict(lambda: {"revenue": 0, "units": 0, "orders": 0})
    
    for order in orders:
        if order.get('status') == 'delivered':
            for item in order.get('items', []):
                product_name = item.get('product_name', 'Unknown')
                product_stats[product_name]["revenue"] += item.get('total_price', 0)
                product_stats[product_name]["units"] += item.get('quantity', 0)
                product_stats[product_name]["orders"] += 1
    
    # Sort and return appropriate performers
    sorted_products = sorted(
        product_stats.items(),
        key=lambda x: x[1]["revenue"],
        reverse=(analysis_type == "best")
    )
    
    limit = 5 if analysis_type == "best" else 3
    results = []
    
    for i, (product_name, stats) in enumerate(sorted_products[:limit]):
        results.append({
            "rank": i + 1,
            "product_name": product_name,
            "revenue": stats["revenue"],
            "units_sold": stats["units"],
            "orders": stats["orders"],
            "avg_order_value": stats["revenue"] / stats["orders"] if stats["orders"] > 0 else 0
        })
    
    return results


def _analyze_category_performance(orders: List[Dict]) -> Dict[str, Dict]:
    """Analyze performance by product category"""
    # Get products to map names to categories
    products = db.get_products()
    product_categories = {p.get('name', ''): p.get('category', 'Unknown') for p in products}
    
    category_stats = defaultdict(lambda: {"revenue": 0, "units": 0, "orders": set()})
    total_revenue = 0
    
    for order in orders:
        if order.get('status') == 'delivered':
            for item in order.get('items', []):
                product_name = item.get('product_name', 'Unknown')
                category = product_categories.get(product_name, 'Unknown')
                revenue = item.get('total_price', 0)
                
                category_stats[category]["revenue"] += revenue
                category_stats[category]["units"] += item.get('quantity', 0)
                category_stats[category]["orders"].add(order.get('id'))
                total_revenue += revenue
    
    # Format results with percentages
    results = {}
    for category, stats in category_stats.items():
        share_percentage = (stats["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        results[category] = {
            "revenue": stats["revenue"],
            "units_sold": stats["units"],
            "orders": len(stats["orders"]),
            "share_percentage": round(share_percentage, 1)
        }
    
    return results


def _analyze_daily_patterns(orders: List[Dict]) -> Dict[str, Any]:
    """Analyze daily and weekly sales patterns"""
    weekday_orders = defaultdict(int)
    weekday_revenue = defaultdict(float)
    hourly_orders = defaultdict(int)
    
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for order in orders:
        if order.get('status') == 'delivered':
            try:
                order_date = datetime.fromisoformat(order.get('created_at', ''))
                weekday = weekdays[order_date.weekday()]
                hour = order_date.hour
                
                weekday_orders[weekday] += 1
                weekday_revenue[weekday] += order.get('grand_total', 0)
                hourly_orders[hour] += 1
                
            except (ValueError, TypeError):
                continue
    
    # Find peak patterns
    peak_day = max(weekday_orders.items(), key=lambda x: x[1])[0] if weekday_orders else "No data"
    peak_hour = max(hourly_orders.items(), key=lambda x: x[1])[0] if hourly_orders else 0
    
    # Calculate weekend vs weekday performance
    weekend_orders = weekday_orders.get('Saturday', 0) + weekday_orders.get('Sunday', 0)
    weekday_total = sum(weekday_orders[day] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    total_orders = weekend_orders + weekday_total
    
    weekend_percentage = (weekend_orders / total_orders * 100) if total_orders > 0 else 0
    
    return {
        "peak_day": peak_day,
        "peak_hour": f"{peak_hour}:00",
        "weekday_distribution": dict(weekday_orders),
        "weekend_percentage": round(weekend_percentage, 1),
        "hourly_distribution": dict(hourly_orders)
    }


def _analyze_payment_methods(orders: List[Dict]) -> Dict[str, Dict]:
    """Analyze payment method performance"""
    payment_stats = defaultdict(lambda: {"revenue": 0, "orders": 0, "orders_list": []})
    
    for order in orders:
        if order.get('status') == 'delivered':
            method = order.get('payment_method', 'unknown').lower()
            revenue = order.get('grand_total', 0)
            
            payment_stats[method]["revenue"] += revenue
            payment_stats[method]["orders"] += 1
            payment_stats[method]["orders_list"].append(revenue)
    
    # Calculate totals and percentages
    total_revenue = sum(stats["revenue"] for stats in payment_stats.values())
    total_orders = sum(stats["orders"] for stats in payment_stats.values())
    
    results = {}
    for method, stats in payment_stats.items():
        avg_order_value = stats["revenue"] / stats["orders"] if stats["orders"] > 0 else 0
        revenue_share = (stats["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        order_share = (stats["orders"] / total_orders * 100) if total_orders > 0 else 0
        
        results[method] = {
            "revenue": stats["revenue"],
            "orders": stats["orders"],
            "avg_order_value": round(avg_order_value, 0),
            "revenue_share": round(revenue_share, 1),
            "order_share": round(order_share, 1)
        }
    
    return results


# Helper functions for insights and recommendations

def _generate_business_insights(core_metrics: Dict, revenue_trends: Dict, 
                              top_products: List[Dict], stock_alerts: List[Dict]) -> List[str]:
    """Generate actionable business insights"""
    insights = []
    
    # Revenue growth insight
    growth = revenue_trends.get('growth_percentage', 0)
    if growth > 10:
        insights.append(f"🚀 Excellent growth! Revenue up {growth}% - consider expanding inventory")
    elif growth > 0:
        insights.append(f"📈 Positive growth of {growth}% - on the right track")
    elif growth < -10:
        insights.append(f"📉 Revenue declined {abs(growth)}% - review pricing and inventory")
    
    # Stock management insight
    critical_alerts = [alert for alert in stock_alerts if alert["priority"] == "critical"]
    if critical_alerts:
        insights.append(f"⚠️ {len(critical_alerts)} products need immediate restocking")
    
    # Customer insight
    retention = core_metrics.get('completion_rate', 0)
    if retention > 90:
        insights.append("✅ Excellent order completion rate - customers are satisfied")
    elif retention < 80:
        insights.append("❗ Order completion rate below 80% - check fulfillment process")
    
    # Product performance insight
    if top_products:
        top_product = top_products[0]
        insights.append(f"🏆 {top_product['product_name']} is your top performer with KSh {top_product['revenue']:,}")
    
    return insights


def _generate_sales_insights(best_performers: List[Dict], category_performance: Dict,
                           daily_patterns: Dict, payment_breakdown: Dict) -> List[str]:
    """Generate sales-specific insights"""
    insights = []
    
    # Best performer insight
    if best_performers:
        top_product = best_performers[0]
        insights.append(f"🏆 {top_product['product_name']} leads with KSh {top_product['revenue']:,} revenue")
    
    # Category insight
    if category_performance:
        top_category = max(category_performance.items(), key=lambda x: x[1]['revenue'])
        insights.append(f"📱 {top_category[0]} dominates with {top_category[1]['share_percentage']}% of sales")
    
    # Timing insight
    weekend_pct = daily_patterns.get('weekend_percentage', 0)
    if weekend_pct > 40:
        insights.append(f"🏖️ Weekend sales strong ({weekend_pct}%) - focus weekend promotions")
    
    # Payment insight
    if 'mpesa' in payment_breakdown:
        mpesa_share = payment_breakdown['mpesa']['revenue_share']
        insights.append(f"📱 M-Pesa preferred ({mpesa_share}% of revenue) - mobile-first strategy working")
    
    return insights


def _get_stock_recommendation(stock: int, velocity: float, priority: str) -> str:
    """Get specific stock management recommendation"""
    if priority == "out_of_stock":
        return "URGENT: Restock immediately - losing sales"
    elif priority == "critical":
        return f"Restock within 1 week (selling {velocity:.1f}/week)"
    elif priority == "warning":
        return f"Plan restock soon (2 weeks stock left)"
    elif priority == "low":
        return "Monitor closely - below minimum threshold"
    else:
        return "Stock levels adequate"


def _group_orders_by_week(orders: List[Dict]) -> List[float]:
    """Group orders by week and return weekly revenue"""
    weekly_revenue = [0, 0, 0, 0]  # 4 weeks
    now = datetime.now()
    
    for order in orders:
        try:
            order_date = datetime.fromisoformat(order.get('created_at', ''))
            days_ago = (now - order_date).days
            week_index = min(days_ago // 7, 3)  # 0-3 for weeks 1-4
            weekly_revenue[3 - week_index] += order.get('grand_total', 0)  # Reverse order
        except (ValueError, TypeError):
            continue
    
    return weekly_revenue

def safe_analytics_call(func):
    """Decorator for safe analytics function calls with error handling"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": "Unable to generate analytics. Please try again.",
                    "data": None
                }
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Analytics temporarily unavailable: {str(e)[:100]}",
                "error_type": "system_error",
                "data": None
            }
    return wrapper

# Apply decorator to main functions:
get_enhanced_business_stats = safe_analytics_call(get_enhanced_business_stats)
get_sales_analytics = safe_analytics_call(get_sales_analytics)

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
        "handler": get_enhanced_business_stats,
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
    },
{
    "name": "get_sales_analytics", 
    "description": "Get detailed sales analytics including product performance, category analysis, and sales patterns",
    "handler": get_sales_analytics,
    "parameters": {
        "type": "object",
        "properties": {
            "business_id": {
                "type": "string",
                "description": "Business ID to analyze"
            },
            "period": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly", "quarterly", "all"],
                "description": "Analysis period",
                "default": "monthly"
            }
        },
        "required": ["business_id"]
    }
}]