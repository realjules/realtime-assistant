"""
Validation Middleware for Sasabot
Prevents hallucination by validating all inputs before function execution
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import re


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: str = None, error_type: str = "validation"):
        self.message = message
        self.field = field
        self.error_type = error_type
        super().__init__(self.message)


class ProductValidator:
    """Comprehensive product validation"""
    
    # Valid categories
    VALID_CATEGORIES = [
        "Electronics", "Accessories", "Storage", "Audio", "Mobile", 
        "Computing", "Gaming", "Cameras", "Wearables", "Home & Garden"
    ]
    
    # Common brands (for suggestions)
    COMMON_BRANDS = [
        "Apple", "Samsung", "Dell", "HP", "Sony", "LG", "Microsoft",
        "Google", "Xiaomi", "Huawei", "OnePlus", "Oppo", "Vivo",
        "Canon", "Nikon", "JBL", "Bose", "Logitech", "Generic"
    ]
    
    # Warranty patterns
    WARRANTY_PATTERNS = [
        r"^\d+\s*(month|months|year|years?)$",
        r"^(no warranty|lifetime|limited)$"
    ]
    
    @staticmethod
    def validate_product_name(name: str) -> Dict[str, Any]:
        """Validate product name"""
        if not name or not isinstance(name, str):
            return {"valid": False, "error": "Product name is required"}
        
        name = name.strip()
        
        if len(name) < 3:
            return {"valid": False, "error": "Product name must be at least 3 characters long"}
        
        if len(name) > 100:
            return {"valid": False, "error": "Product name must be less than 100 characters"}
        
        # Check for vague names that suggest hallucination
        vague_names = [
            "product", "item", "generic", "smartphone", "laptop", "phone", 
            "computer", "device", "gadget", "accessory"
        ]
        
        if name.lower().strip() in vague_names:
            return {
                "valid": False, 
                "error": f"'{name}' is too generic. Please provide specific model name and specifications",
                "suggestion": "Example: 'iPhone 13 Pro Max 256GB Blue' instead of just 'phone'"
            }
        
        return {"valid": True, "value": name}
    
    @staticmethod
    def validate_price(price: Any) -> Dict[str, Any]:
        """Validate product price"""
        try:
            price = float(price)
        except (ValueError, TypeError):
            return {"valid": False, "error": "Price must be a valid number"}
        
        if price <= 0:
            return {"valid": False, "error": "Price must be greater than 0"}
        
        if price > 10000000:  # 10 million KSh
            return {
                "valid": False, 
                "error": "Price seems unrealistically high (over 10 million KSh). Please confirm.",
                "warning": True
            }
        
        if price < 50:  # Less than 50 KSh
            return {
                "valid": True, 
                "value": price,
                "warning": "Price seems very low. Please confirm this is correct."
            }
        
        return {"valid": True, "value": price}
    
    @staticmethod
    def validate_stock(stock: Any) -> Dict[str, Any]:
        """Validate stock quantity"""
        try:
            stock = int(stock)
        except (ValueError, TypeError):
            return {"valid": False, "error": "Stock must be a whole number"}
        
        if stock < 0:
            return {"valid": False, "error": "Stock cannot be negative"}
        
        if stock == 0:
            return {
                "valid": True, 
                "value": stock,
                "warning": "Adding product with zero stock. It won't be available for purchase."
            }
        
        if stock > 10000:
            return {
                "valid": True, 
                "value": stock,
                "warning": "Stock quantity seems very high. Please confirm."
            }
        
        return {"valid": True, "value": stock}
    
    @staticmethod
    def validate_category(category: str) -> Dict[str, Any]:
        """Validate product category"""
        if not category or not isinstance(category, str):
            return {"valid": False, "error": "Category is required"}
        
        category = category.strip()
        
        # Check if category is in valid list (case insensitive)
        valid_categories_lower = [c.lower() for c in ProductValidator.VALID_CATEGORIES]
        
        if category.lower() not in valid_categories_lower:
            return {
                "valid": False,
                "error": f"Invalid category '{category}'",
                "suggestions": ProductValidator.VALID_CATEGORIES,
                "message": f"Please choose from: {', '.join(ProductValidator.VALID_CATEGORIES)}"
            }
        
        # Return the properly capitalized version
        for valid_cat in ProductValidator.VALID_CATEGORIES:
            if valid_cat.lower() == category.lower():
                return {"valid": True, "value": valid_cat}
        
        return {"valid": True, "value": category.title()}
    
    @staticmethod
    def validate_description(description: str) -> Dict[str, Any]:
        """Validate product description"""
        if not description or not isinstance(description, str):
            return {
                "valid": False, 
                "error": "Product description is required for better customer experience"
            }
        
        description = description.strip()
        
        if len(description) < 10:
            return {
                "valid": False,
                "error": "Description is too short. Please provide at least 10 characters with meaningful details."
            }
        
        if len(description) > 500:
            return {
                "valid": False,
                "error": "Description is too long. Please keep it under 500 characters."
            }
        
        # Check for generic descriptions
        generic_descriptions = [
            "good product", "nice item", "quality product", "great device",
            "excellent item", "good quality", "best product", "amazing product"
        ]
        
        if description.lower() in generic_descriptions:
            return {
                "valid": False,
                "error": f"'{description}' is too generic. Please provide specific features, specifications, or benefits.",
                "suggestion": "Example: 'Latest smartphone with 64MP camera, 128GB storage, and fast charging'"
            }
        
        return {"valid": True, "value": description}
    
    @staticmethod
    def validate_brand(brand: str) -> Dict[str, Any]:
        """Validate product brand"""
        if not brand or not isinstance(brand, str):
            return {"valid": False, "error": "Brand is required"}
        
        brand = brand.strip()
        
        if len(brand) < 2:
            return {"valid": False, "error": "Brand name must be at least 2 characters"}
        
        # Suggest common brands if not recognized
        if brand.lower() not in [b.lower() for b in ProductValidator.COMMON_BRANDS]:
            return {
                "valid": True, 
                "value": brand.title(),
                "suggestion": f"Unrecognized brand. Common brands include: {', '.join(ProductValidator.COMMON_BRANDS[:10])}"
            }
        
        return {"valid": True, "value": brand.title()}
    
    @staticmethod
    def validate_warranty(warranty: str) -> Dict[str, Any]:
        """Validate warranty period"""
        if not warranty or not isinstance(warranty, str):
            return {"valid": False, "error": "Warranty period is required"}
        
        warranty = warranty.strip().lower()
        
        # Check against patterns
        for pattern in ProductValidator.WARRANTY_PATTERNS:
            if re.match(pattern, warranty, re.IGNORECASE):
                return {"valid": True, "value": warranty}
        
        return {
            "valid": False,
            "error": "Invalid warranty format",
            "suggestion": "Examples: '12 months', '2 years', '6 months', 'no warranty', 'lifetime'"
        }


class ValidationMiddleware:
    """Main validation middleware class"""
    
    def __init__(self):
        self.validator = ProductValidator()
    
    def validate_add_product_request(self, **kwargs) -> Dict[str, Any]:
        """
        Comprehensive validation for add product requests
        Returns validation result with detailed feedback
        """
        # Required fields
        required_fields = ["name", "price", "stock", "category", "description", "brand", "warranty"]
        
        # Check for missing fields
        missing_fields = []
        for field in required_fields:
            if field not in kwargs or kwargs[field] is None or str(kwargs[field]).strip() == "":
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "valid": False,
                "error_type": "missing_fields",
                "missing_fields": missing_fields,
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "prompt_needed": True
            }
        
        # Validate each field
        validation_results = {}
        errors = []
        warnings = []
        validated_data = {}
        
        # Validate name
        name_result = self.validator.validate_product_name(kwargs.get("name"))
        validation_results["name"] = name_result
        if not name_result["valid"]:
            errors.append(f"Name: {name_result['error']}")
        else:
            validated_data["name"] = name_result["value"]
        
        # Validate price
        price_result = self.validator.validate_price(kwargs.get("price"))
        validation_results["price"] = price_result
        if not price_result["valid"]:
            errors.append(f"Price: {price_result['error']}")
        else:
            validated_data["price"] = price_result["value"]
            if "warning" in price_result:
                warnings.append(f"Price: {price_result['warning']}")
        
        # Validate stock
        stock_result = self.validator.validate_stock(kwargs.get("stock"))
        validation_results["stock"] = stock_result
        if not stock_result["valid"]:
            errors.append(f"Stock: {stock_result['error']}")
        else:
            validated_data["stock"] = stock_result["value"]
            if "warning" in stock_result:
                warnings.append(f"Stock: {stock_result['warning']}")
        
        # Validate category
        category_result = self.validator.validate_category(kwargs.get("category"))
        validation_results["category"] = category_result
        if not category_result["valid"]:
            errors.append(f"Category: {category_result['error']}")
            if "suggestions" in category_result:
                errors.append(f"Valid categories: {', '.join(category_result['suggestions'])}")
        else:
            validated_data["category"] = category_result["value"]
        
        # Validate description
        description_result = self.validator.validate_description(kwargs.get("description"))
        validation_results["description"] = description_result
        if not description_result["valid"]:
            errors.append(f"Description: {description_result['error']}")
        else:
            validated_data["description"] = description_result["value"]
        
        # Validate brand
        brand_result = self.validator.validate_brand(kwargs.get("brand"))
        validation_results["brand"] = brand_result
        if not brand_result["valid"]:
            errors.append(f"Brand: {brand_result['error']}")
        else:
            validated_data["brand"] = brand_result["value"]
            if "suggestion" in brand_result:
                warnings.append(f"Brand: {brand_result['suggestion']}")
        
        # Validate warranty
        warranty_result = self.validator.validate_warranty(kwargs.get("warranty"))
        validation_results["warranty"] = warranty_result
        if not warranty_result["valid"]:
            errors.append(f"Warranty: {warranty_result['error']}")
            if "suggestion" in warranty_result:
                errors.append(f"Warranty suggestion: {warranty_result['suggestion']}")
        else:
            validated_data["warranty"] = warranty_result["value"]
        
        # Return validation result
        if errors:
            return {
                "valid": False,
                "error_type": "validation_errors",
                "errors": errors,
                "warnings": warnings,
                "validation_results": validation_results,
                "message": "Product validation failed:\n" + "\n".join(f"• {error}" for error in errors)
            }
        
        return {
            "valid": True,
            "validated_data": validated_data,
            "warnings": warnings,
            "message": "Product data validation passed" + (f" with {len(warnings)} warnings" if warnings else "")
        }
    
    def create_information_request(self, missing_fields: List[str], provided_data: Dict = None) -> str:
        """
        Create a user-friendly request for missing information
        """
        field_descriptions = {
            "name": "What is the exact product name and model? (e.g., 'iPhone 13 Pro Max 256GB Blue')",
            "price": "What is the price in Kenyan Shillings (KSh)?",
            "stock": "How many units do you have in stock?",
            "category": f"What category does this belong to? Choose from: {', '.join(ProductValidator.VALID_CATEGORIES)}",
            "description": "Please provide a detailed description with features and specifications",
            "brand": f"What is the brand name? Common brands: {', '.join(ProductValidator.COMMON_BRANDS[:8])}",
            "warranty": "What is the warranty period? (e.g., '12 months', '2 years', 'no warranty')"
        }
        
        message = "I need some additional information to add this product properly:\n\n"
        
        for field in missing_fields:
            if field in field_descriptions:
                message += f"• **{field.title()}**: {field_descriptions[field]}\n"
        
        if provided_data:
            message += "\n**Information you've already provided:**\n"
            for key, value in provided_data.items():
                if value is not None and str(value).strip():
                    message += f"• {key.title()}: {value}\n"
        
        message += "\nPlease provide the missing details so I can add your product correctly."
        
        return message
    
    def validate_business_id(self, business_id: str) -> Dict[str, Any]:
        """Validate business ID"""
        if not business_id or not isinstance(business_id, str):
            return {"valid": False, "error": "Business ID is required"}
        
        # Add more business ID validation as needed
        return {"valid": True, "value": business_id.strip()}


# Global middleware instance
validation_middleware = ValidationMiddleware()


def validate_product_input(func: Callable) -> Callable:
    """
    Decorator to validate product input before function execution
    """
    def wrapper(*args, **kwargs):
        # Validate the input
        validation_result = validation_middleware.validate_add_product_request(**kwargs)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": validation_result["message"],
                "error_type": validation_result["error_type"],
                "validation_details": validation_result,
                "data": None
            }
        
        # If validation passed, update kwargs with validated data
        kwargs.update(validation_result["validated_data"])
        
        # Call the original function
        result = func(*args, **kwargs)
        
        # Add warnings to successful result
        if result.get("success") and validation_result.get("warnings"):
            if isinstance(result.get("message"), str):
                result["message"] += "\n\n⚠️ Warnings:\n" + "\n".join(f"• {w}" for w in validation_result["warnings"])
        
        return result
    
    return wrapper


# Export the main components
__all__ = [
    "ValidationMiddleware", 
    "ProductValidator", 
    "ValidationError", 
    "validation_middleware", 
    "validate_product_input"
]