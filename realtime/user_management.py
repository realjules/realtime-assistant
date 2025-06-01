"""
User Management Tools
Handles user authentication, role detection, and session management
"""

import chainlit as cl
from typing import Dict, List, Optional

# =============================================================================
# USER TYPE DETECTION
# =============================================================================

detect_user_type_def = {
    "name": "detect_user_type",
    "description": "Identify if user is a vendor (business owner) or customer based on their message",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The user's message to analyze"
            }
        },
        "required": ["message"]
    }
}

async def detect_user_type_handler(message: str):
    """Detect user type from message content"""
    vendor_keywords = ["manage", "inventory", "stock", "add product", "business", "sales", "report", "vendor", "my store", "dashboard"]
    customer_keywords = ["buy", "purchase", "order", "shopping", "price", "customer", "want to buy", "looking for", "how much"]
    
    message_lower = message.lower()
    vendor_score = sum(1 for keyword in vendor_keywords if keyword in message_lower)
    customer_score = sum(1 for keyword in customer_keywords if keyword in message_lower)
    
    if vendor_score > customer_score:
        return {"user_type": "vendor", "confidence": 0.8, "keywords_matched": vendor_score}
    elif customer_score > vendor_score:
        return {"user_type": "customer", "confidence": 0.8, "keywords_matched": customer_score}
    else:
        return {"user_type": "unknown", "confidence": 0.5, "keywords_matched": 0}

# =============================================================================
# USER ROLE MANAGEMENT
# =============================================================================

set_user_role_def = {
    "name": "set_user_role",
    "description": "Assign vendor or customer role to user session",
    "parameters": {
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "enum": ["vendor", "customer"],
                "description": "User role to set"
            },
            "business_id": {
                "type": "string",
                "description": "Business ID for vendors",
                "default": "mama_jane_electronics"
            }
        },
        "required": ["role"]
    }
}

async def set_user_role_handler(role: str, business_id: str = "mama_jane_electronics"):
    """Set user role in session"""
    cl.user_session.set("user_type", role)
    cl.user_session.set("role_set_at", cl.context.session.created_at)
    
    if role == "vendor":
        cl.user_session.set("business_id", business_id)
        cl.user_session.set("permissions", ["manage_products", "view_reports", "manage_inventory"])
    else:
        cl.user_session.set("permissions", ["browse_products", "place_orders", "track_orders"])
    
    return {
        "success": True, 
        "role": role, 
        "business_id": business_id if role == "vendor" else None,
        "message": f"Role set to {role}"
    }

get_user_context_def = {
    "name": "get_user_context",
    "description": "Retrieve user's conversation context and session data",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

async def get_user_context_handler():
    """Get current user context"""
    user_type = cl.user_session.get("user_type", "unknown")
    business_id = cl.user_session.get("business_id", None)
    permissions = cl.user_session.get("permissions", [])
    conversation_history = cl.user_session.get("conversation_history", [])
    
    return {
        "user_type": user_type,
        "business_id": business_id,
        "permissions": permissions,
        "conversation_count": len(conversation_history),
        "session_active": True,
        "context": "Active session"
    }

switch_user_role_def = {
    "name": "switch_user_role",
    "description": "Switch between vendor and customer roles for demo purposes",
    "parameters": {
        "type": "object",
        "properties": {
            "new_role": {
                "type": "string",
                "enum": ["vendor", "customer"],
                "description": "Role to switch to"
            }
        },
        "required": ["new_role"]
    }
}

async def switch_user_role_handler(new_role: str):
    """Switch user role"""
    current_role = cl.user_session.get("user_type", "unknown")
    
    if current_role == new_role:
        return {
            "success": False,
            "message": f"You are already in {new_role} mode",
            "current_role": current_role
        }
    
    # Set new role
    result = await set_user_role_handler(new_role)
    
    if new_role == "vendor":
        message = "🏪 **Switched to VENDOR mode**\n\nYou can now manage your business, add products, and view reports."
    else:
        message = "🛒 **Switched to CUSTOMER mode**\n\nYou can now browse products, place orders, and shop."
    
    return {
        "success": True,
        "message": message,
        "previous_role": current_role,
        "current_role": new_role
    }

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

reset_user_session_def = {
    "name": "reset_user_session",
    "description": "Clear user session data and start fresh",
    "parameters": {
        "type": "object",
        "properties": {
            "keep_history": {
                "type": "boolean",
                "description": "Whether to keep conversation history",
                "default": False
            }
        },
        "required": []
    }
}

async def reset_user_session_handler(keep_history: bool = False):
    """Reset user session"""
    # Store current data
    current_user_type = cl.user_session.get("user_type", "unknown")
    conversation_history = cl.user_session.get("conversation_history", []) if keep_history else []
    
    # Clear all session data
    session_keys = ["user_type", "business_id", "permissions", "pending_order", "cart_items"]
    for key in session_keys:
        if cl.user_session.get(key):
            cl.user_session.set(key, None)
    
    # Reset to fresh state
    cl.user_session.set("user_type", "unknown")
    if keep_history:
        cl.user_session.set("conversation_history", conversation_history)
    
    return {
        "success": True,
        "message": "🔄 Session reset successfully. You can now choose vendor or customer mode.",
        "previous_user_type": current_user_type,
        "history_kept": keep_history
    }

validate_user_permissions_def = {
    "name": "validate_user_permissions",
    "description": "Check if user has permission to perform specific action",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to validate (e.g., 'manage_products', 'place_orders')"
            }
        },
        "required": ["action"]
    }
}

async def validate_user_permissions_handler(action: str):
    """Validate user permissions"""
    user_type = cl.user_session.get("user_type", "unknown")
    permissions = cl.user_session.get("permissions", [])
    
    # Define permission mappings
    vendor_permissions = ["manage_products", "view_reports", "manage_inventory", "view_analytics"]
    customer_permissions = ["browse_products", "place_orders", "track_orders", "view_cart"]
    
    has_permission = action in permissions
    
    if user_type == "unknown":
        return {
            "valid": False,
            "message": "Please choose vendor or customer mode first",
            "required_role": "any"
        }
    
    if not has_permission:
        if action in vendor_permissions:
            required_role = "vendor"
        elif action in customer_permissions:
            required_role = "customer"
        else:
            required_role = "unknown"
            
        return {
            "valid": False,
            "message": f"Action '{action}' requires {required_role} role. You are currently: {user_type}",
            "required_role": required_role,
            "current_role": user_type
        }
    
    return {
        "valid": True,
        "message": "Permission granted",
        "action": action,
        "user_type": user_type
    }

# =============================================================================
# USER TOOLS REGISTRY
# =============================================================================

user_tools = [
    (detect_user_type_def, detect_user_type_handler),
    (set_user_role_def, set_user_role_handler),
    (get_user_context_def, get_user_context_handler),
    (switch_user_role_def, switch_user_role_handler),
    (reset_user_session_def, reset_user_session_handler),
    (validate_user_permissions_def, validate_user_permissions_handler),
]