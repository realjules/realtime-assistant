"""
Main Tools Registry
Imports and combines all tool categories for the Sasabot system
"""

# Import all tool categories
from .tools.user_management import user_tools
from .tools.vendor_tools import vendor_tools
from .tools.customer_tools import customer_tools
from .tools.conversation_flow import conversation_tools
from .tools.demo_data import demo_tools

# =============================================================================
# TOOL COMBINATIONS BY USER TYPE
# =============================================================================

# Tools available to vendors
vendor_tool_set = (
    user_tools +           # User management (role switching, context)
    vendor_tools +         # Business management, inventory, reports
    conversation_tools +   # Conversation flow, welcome messages
    demo_tools            # Demo data and explanations
)

# Tools available to customers  
customer_tool_set = (
    user_tools +           # User management (role switching, context)
    customer_tools +       # Product browsing, shopping, orders
    conversation_tools +   # Conversation flow, welcome messages
    demo_tools            # Demo data and explanations
)

# Tools available to unknown users (pre-role selection)
onboarding_tool_set = (
    user_tools +           # User management (role detection, setting)
    conversation_tools +   # Welcome messages, help
    demo_tools            # Demo explanations
)

# =============================================================================
# MAIN EXPORT - ALL TOOLS COMBINED
# =============================================================================

# Export all tools for the main application
# This combines vendor and customer tools (some overlap is handled by the AI)
tools = list(set(vendor_tool_set + customer_tool_set))

# =============================================================================
# TOOL REGISTRY INFORMATION
# =============================================================================

TOOL_REGISTRY_INFO = {
    "total_tools": len(tools),
    "user_management_tools": len(user_tools),
    "vendor_tools": len(vendor_tools), 
    "customer_tools": len(customer_tools),
    "conversation_tools": len(conversation_tools),
    "demo_tools": len(demo_tools),
    "categories": [
        "User Management",
        "Vendor Operations", 
        "Customer Shopping",
        "Conversation Flow",
        "Demo & Testing"
    ]
}

# =============================================================================
# TOOL FILTERING FUNCTIONS
# =============================================================================

def get_tools_for_user_type(user_type: str):
    """Get appropriate tools based on user type"""
    if user_type == "vendor":
        return vendor_tool_set
    elif user_type == "customer":
        return customer_tool_set
    elif user_type == "unknown":
        return onboarding_tool_set
    else:
        return tools  # All tools as fallback

def get_tools_by_category(category: str):
    """Get tools by category"""
    category_mapping = {
        "user_management": user_tools,
        "vendor": vendor_tools,
        "customer": customer_tools,
        "conversation": conversation_tools,
        "demo": demo_tools
    }
    return category_mapping.get(category, [])

def get_tool_info():
    """Get information about the tool registry"""
    return TOOL_REGISTRY_INFO

# =============================================================================
# TOOL VALIDATION
# =============================================================================

def validate_tools():
    """Validate that all tools are properly formatted"""
    errors = []
    
    for tool_def, tool_handler in tools:
        # Check tool definition format
        if not isinstance(tool_def, dict):
            errors.append(f"Tool definition is not a dict: {tool_handler.__name__}")
            continue
            
        required_fields = ["name", "description", "parameters"]
        for field in required_fields:
            if field not in tool_def:
                errors.append(f"Missing {field} in tool: {tool_def.get('name', 'unknown')}")
        
        # Check if handler is callable
        if not callable(tool_handler):
            errors.append(f"Tool handler is not callable: {tool_def.get('name', 'unknown')}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "total_tools_validated": len(tools)
    }

# =============================================================================
# USAGE EXAMPLE
# =============================================================================

"""
Usage in main app.py:

from realtime.tools import tools, get_tools_for_user_type, get_tool_info

# Get all tools
all_tools = tools

# Get tools for specific user type
vendor_tools = get_tools_for_user_type("vendor")
customer_tools = get_tools_for_user_type("customer")

# Get registry information
info = get_tool_info()
print(f"Total tools available: {info['total_tools']}")

# Validate tools
validation = validate_tools()
if not validation['valid']:
    print("Tool validation errors:", validation['errors'])
"""