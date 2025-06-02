"""
Sasabot Assistant
Main AI assistant that coordinates between different tools and handles conversation flow
"""

import json
import chainlit as cl
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import all tool modules
from .user_management import user_tools
from .vendor_tools import vendor_tools
from .customer_tools import customer_tools
from .conversation_flow import conversation_tools
from .demo_data import demo_tools


class SasabotAssistant:
    """Main assistant class that handles conversation and tool routing"""
    
    def __init__(self):
        self.tools = {}
        self._register_all_tools()
        
    def _register_all_tools(self):
        """Register all available tools"""
        all_tool_sets = [
            user_tools,
            vendor_tools, 
            customer_tools,
            conversation_tools,
            demo_tools
        ]
        
        for tool_set in all_tool_sets:
            for tool_def in tool_set:
                if isinstance(tool_def, dict):
                    # New format: {"name": "...", "handler": ..., ...}
                    tool_name = tool_def.get("name")
                    tool_handler = tool_def.get("handler")
                    if tool_name and tool_handler:
                        self.tools[tool_name] = tool_def
                elif isinstance(tool_def, tuple) and len(tool_def) == 2:
                    # Old format: (definition_dict, handler_function)
                    tool_definition, tool_handler = tool_def
                    tool_name = tool_definition.get("name")
                    if tool_name:
                        self.tools[tool_name] = {
                            **tool_definition,
                            "handler": tool_handler
                        }
        
        print(f"✅ Registered {len(self.tools)} tools")
    
    async def process_message(self, message: str) -> str:
        """Process user message and return response"""
        try:
            # Get user context
            user_type = cl.user_session.get("user_type", "unknown")
            business_id = cl.user_session.get("business_id", "mama_jane_electronics")
            
            # Simple intent detection and routing
            response = await self._route_message(message, user_type, business_id)
            
            return response
            
        except Exception as e:
            return f"❌ Sorry, I encountered an error: {str(e)}\nPlease try rephrasing your request."
    
    async def _route_message(self, message: str, user_type: str, business_id: str) -> str:
        """Route message to appropriate handler based on content"""
        message_lower = message.lower()
        
        # Database commands
        if any(cmd in message_lower for cmd in ["stats", "database stats", "show database stats"]):
            return await self._call_tool("get_database_stats", {})
        
        # Role switching
        if "vendor" in message_lower and "switch" in message_lower:
            return await self._call_tool("switch_user_role", {"new_role": "vendor"})
        
        if "customer" in message_lower and "switch" in message_lower:
            return await self._call_tool("switch_user_role", {"new_role": "customer"})
        
        # Set initial role
        if user_type == "unknown":
            if "vendor" in message_lower or "business" in message_lower:
                await self._call_tool("set_user_role", {"role": "vendor", "business_id": business_id})
                return await self._call_tool("welcome_message", {"user_type": "vendor", "business_name": "Demo Business"})
            
            elif "customer" in message_lower or "shop" in message_lower:
                await self._call_tool("set_user_role", {"role": "customer"})
                return await self._call_tool("welcome_message", {"user_type": "customer"})
            
            else:
                return await self._call_tool("welcome_message", {"user_type": "unknown"})
        
        # Vendor commands
        if user_type == "vendor":
            return await self._handle_vendor_message(message, business_id)
        
        # Customer commands  
        elif user_type == "customer":
            return await self._handle_customer_message(message)
        
        # Help and general
        if any(word in message_lower for word in ["help", "what can you do", "commands"]):
            return await self._call_tool("help_system", {"user_type": user_type})
        
        # Default response
        return "I'm not sure how to help with that. Try saying 'help' to see what I can do, or specify if you're a 'vendor' or 'customer'."
    
    async def _handle_vendor_message(self, message: str, business_id: str) -> str:
        """Handle vendor-specific messages"""
        message_lower = message.lower()
        
        # Product management
        if "add product" in message_lower or "add new product" in message_lower:
            # Extract product details from message (simple parsing)
            words = message.split()
            if len(words) >= 4:
                try:
                    # Look for: "add product [name] [price]"
                    name = words[2] if len(words) > 2 else "New Product"
                    price = 0
                    
                    # Find price in message
                    for word in words:
                        if word.replace(',', '').replace('.', '').isdigit():
                            price = float(word.replace(',', ''))
                            break
                    
                    if price > 0:
                        result = await self._call_tool("add_product", {
                            "business_id": business_id,
                            "name": name,
                            "price": price,
                            "stock": 10,  # Default stock
                            "category": "Electronics"
                        })
                        
                        if isinstance(result, dict) and result.get("success"):
                            return f"✅ {result.get('message', 'Product added successfully!')}"
                        else:
                            return f"❌ {result.get('message', 'Failed to add product')}"
                    
                except Exception as e:
                    return f"❌ Error parsing product details: {str(e)}"
            
            return "❌ Please specify product name and price. Example: 'Add product iPhone 75000'"
        
        elif any(phrase in message_lower for phrase in ["show products", "my products", "list products", "view products"]):
            result = await self._call_tool("show_products", {"business_id": business_id})
            return self._format_vendor_response(result)
        
        elif "update product" in message_lower:
            # Simple update handling - could be enhanced
            return "🔧 Product updates available. Please specify: 'Update product [name/id] price [new_price]' or similar."
        
        elif "delete product" in message_lower:
            # Extract product identifier
            words = message.split()
            if len(words) >= 3:
                product_id = words[2]
                result = await self._call_tool("delete_product", {
                    "business_id": business_id,
                    "product_identifier": product_id
                })
                return self._format_vendor_response(result)
            return "❌ Please specify which product to delete. Example: 'Delete product iPhone' or 'Delete product 1'"
        
        elif any(phrase in message_lower for phrase in ["stock", "inventory", "low stock"]):
            result = await self._call_tool("get_low_stock_products", {"business_id": business_id})
            return self._format_vendor_response(result)
        
        elif any(phrase in message_lower for phrase in ["report", "sales", "stats", "analytics"]):
            result = await self._call_tool("get_business_stats", {"business_id": business_id})
            return self._format_vendor_response(result)
        
        return "🏪 I can help you manage products, check inventory, view reports, or get business stats. What would you like to do?"
    
    async def _handle_customer_message(self, message: str) -> str:
        """Handle customer-specific messages"""
        message_lower = message.lower()
        
        # Product browsing
        if any(phrase in message_lower for phrase in ["show products", "browse products", "what products", "see products"]):
            result = await self._call_tool("browse_products", {})
            return result if isinstance(result, str) else str(result)
        
        elif "search" in message_lower:
            # Extract search term
            search_term = ""
            if "search for" in message_lower:
                search_term = message_lower.split("search for")[1].strip()
            elif "search" in message_lower:
                words = message.split()
                search_idx = next((i for i, word in enumerate(words) if "search" in word.lower()), -1)
                if search_idx >= 0 and search_idx + 1 < len(words):
                    search_term = " ".join(words[search_idx + 1:])
            
            result = await self._call_tool("search_products", {"query": search_term})
            return result if isinstance(result, str) else str(result)
        
        elif any(phrase in message_lower for phrase in ["buy", "order", "purchase"]):
            return "🛒 To place an order, I'll need:\n1. Your name\n2. Phone number\n3. Delivery address\n4. Product ID(s) and quantities\n\nPlease provide these details or browse products first to see what's available."
        
        elif "track" in message_lower or "order status" in message_lower:
            return "📦 To track an order, please provide your order ID (e.g., ORD001) and I'll check the status for you."
        
        return "🛒 I can help you browse products, search for items, place orders, or track deliveries. What are you looking for?"
    
    async def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call a specific tool with parameters"""
        try:
            if tool_name not in self.tools:
                return f"❌ Tool '{tool_name}' not found"
            
            tool = self.tools[tool_name]
            handler = tool.get("handler")
            
            if not handler or not callable(handler):
                return f"❌ Tool '{tool_name}' has no valid handler"
            
            # Call the handler
            result = await handler(**params) if hasattr(handler, '__call__') else handler(params)
            
            return result
            
        except Exception as e:
            return f"❌ Error calling tool '{tool_name}': {str(e)}"
    
    def _format_vendor_response(self, result: Dict[str, Any]) -> str:
        """Format vendor tool responses"""
        if isinstance(result, str):
            return result
            
        if not isinstance(result, dict):
            return str(result)
        
        if not result.get("success", False):
            return f"❌ {result.get('message', 'Operation failed')}"
        
        message = result.get('message', 'Operation completed')
        data = result.get('data')
        
        if not data:
            return f"✅ {message}"
        
        # Format different types of data
        if 'products' in data:
            products = data['products']
            if not products:
                return f"✅ {message}\n\n📦 No products found."
            
            response = f"✅ {message}\n\n"
            response += "📦 **PRODUCTS:**\n"
            
            for product in products[:10]:  # Limit to 10 products
                name = product.get('name', 'Unknown')
                price = product.get('price', 0)
                stock = product.get('stock', 0)
                response += f"• **{name}** - KSh {price:,} (Stock: {stock})\n"
            
            if len(products) > 10:
                response += f"... and {len(products) - 10} more products\n"
            
            return response
        
        return f"✅ {message}"
    
    def get_available_tools(self, user_type: str = None) -> List[str]:
        """Get list of available tools, optionally filtered by user type"""
        if not user_type:
            return list(self.tools.keys())
        
        # Filter tools based on user type (basic filtering)
        vendor_tools = [name for name in self.tools.keys() if any(keyword in name for keyword in ['add_product', 'update_product', 'delete_product', 'show_products', 'business_stats'])]
        customer_tools = [name for name in self.tools.keys() if any(keyword in name for keyword in ['browse_products', 'search_products', 'place_order', 'track_order'])]
        
        if user_type == "vendor":
            return vendor_tools + ["help_system", "switch_user_role"]
        elif user_type == "customer":
            return customer_tools + ["help_system", "switch_user_role"]
        else:
            return ["welcome_message", "set_user_role", "help_system"]