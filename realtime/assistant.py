"""
Sasabot Assistant - LLM-Powered with JSON Database
Intelligent AI assistant using OpenAI function calling with persistent JSON data
"""

import openai
import json
import chainlit as cl
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

# Import database and tools
from utils.simple_db import db
from .vendor_tools import (
    add_product_handler, show_products_handler, update_product_handler, 
    delete_product_handler, get_business_stats, get_low_stock_products
)
from .customer_tools import (
    browse_products_handler, search_products_handler, 
    place_order_handler, get_order_status_handler
)


class SasabotAssistant:
    """LLM-powered assistant with intelligent conversation and tool calling"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # UPDATED: Enhanced system prompt to prevent hallucination
        self.system_prompt = """You are Sasabot, an intelligent AI assistant for Kenyan e-commerce businesses and their customers.

CORE PERSONALITY:
- Friendly, helpful, and professional
- Use "Karibu" (welcome) naturally in conversations
- Understand both English and basic Swahili terms
- Adapt your tone based on whether user is a vendor or customer
- ALWAYS introduce yourself as 'Sasabot, an AI assistant' in your first interaction
- Add to conversation context that bot should remind users it's AI if asked about human-like behaviors

CRITICAL ANTI-HALLUCINATION RULES:
1. NEVER assume or make up product details like price, category, description, brand, warranty, etc.
2. ALWAYS ask for missing information rather than guessing or filling in defaults
3. When adding products, you MUST collect ALL required information from the user before calling functions
4. If a user says "add a phone" - ask for: price, specific model name, stock quantity, brand, category, description
5. DO NOT call add_product function until you have complete information
6. If user provides partial info, respond with: "I need more details to add this product properly"

PRODUCT INFORMATION REQUIREMENTS:
Before adding any product, you MUST have:
- Exact product name (not just "phone" but "iPhone 13 Pro Max 256GB")
- Specific price in KSh
- Stock quantity
- Category (Electronics, Accessories, etc.)
- Brand name
- Basic description
- Warranty period

INFORMATION GATHERING APPROACH:
- Ask follow-up questions to get complete details
- Be specific: "What's the exact model and specifications?"
- Always confirm details before proceeding: "Let me confirm: [list all details]"
- If user seems uncertain, help them think through the details

CAPABILITIES:
You can help with:
- Business inventory management (vendors)
- Product browsing and ordering (customers) 
- Real-time data from JSON database
- M-Pesa payments and delivery coordination
- Business analytics and reporting

IMPORTANT GUIDELINES:
1. Always check user's role (vendor/customer) before suggesting actions
2. Use function calls to interact with the JSON database
3. Provide specific, actionable responses
4. When users seem unsure, offer to help them choose vendor or customer mode
5. Format prices in Kenyan Shillings (KSh) with proper comma formatting
6. Be proactive in suggesting next steps

CONTEXT AWARENESS:
- Remember what the user is trying to accomplish
- Offer relevant follow-up actions
- Explain the impact of changes (e.g., "This will update your JSON database")

The system works with real JSON files that persist data between sessions."""

        # UPDATED: Modified function definitions to be more strict
        self.functions = [
            {
                "name": "validate_product_info",
                "description": "Validate that all required product information is complete before adding",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Complete product name with specifications"},
                        "price": {"type": "number", "description": "Product price in KSh"},
                        "stock": {"type": "integer", "description": "Stock quantity"},
                        "category": {"type": "string", "description": "Product category"},
                        "brand": {"type": "string", "description": "Product brand"},
                        "description": {"type": "string", "description": "Product description"},
                        "warranty": {"type": "string", "description": "Warranty period"}
                    },
                    "required": ["name", "price", "stock", "category", "brand", "description", "warranty"]
                }
            },
            {
                "name": "request_missing_product_info",
                "description": "Request missing product information from user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "missing_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of missing required fields"
                        },
                        "provided_info": {
                            "type": "object",
                            "description": "Information already provided by user"
                        }
                    },
                    "required": ["missing_fields"]
                }
            },
            {
                "name": "set_user_role",
                "description": "Set the user's role as vendor or customer",
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
            },
            {
                "name": "get_user_context",
                "description": "Get current user context and session information",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_product",
                "description": "Add a new product to business inventory (vendors only) - ONLY call this when ALL required information is provided",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "name": {"type": "string", "description": "Complete product name with specifications"},
                        "price": {"type": "number", "description": "Product price in KSh"},
                        "stock": {"type": "integer", "description": "Stock quantity"},
                        "category": {"type": "string", "description": "Product category"},
                        "description": {"type": "string", "description": "Product description"},
                        "brand": {"type": "string", "description": "Product brand"},
                        "warranty": {"type": "string", "description": "Warranty period"}
                    },
                    "required": ["business_id", "name", "price", "stock", "category", "description", "brand", "warranty"]
                }
            },
            # ... rest of the functions remain the same
            {
                "name": "show_products",
                "description": "Display products for a business (vendors) or browse all products",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "category": {"type": "string"},
                        "search_term": {"type": "string"}
                    },
                    "required": []
                }
            },
            {
                "name": "update_product",
                "description": "Update an existing product (vendors only)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "product_identifier": {"type": "string"},
                        "name": {"type": "string"},
                        "price": {"type": "number"},
                        "stock": {"type": "integer"},
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                        "brand": {"type": "string"},
                        "warranty": {"type": "string"}
                    },
                    "required": ["business_id", "product_identifier"]
                }
            },
            {
                "name": "delete_product",
                "description": "Delete a product from inventory (vendors only)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "product_identifier": {"type": "string"}
                    },
                    "required": ["business_id", "product_identifier"]
                }
            },
            {
                "name": "get_business_stats",
                "description": "Get comprehensive business statistics and analytics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"}
                    },
                    "required": ["business_id"]
                }
            },
            {
                "name": "get_low_stock_products",
                "description": "Get products with low stock levels",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "threshold": {"type": "integer", "default": 5}
                    },
                    "required": ["business_id"]
                }
            },
            {
                "name": "browse_products",
                "description": "Browse all available products (customers)",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "search_products",
                "description": "Search for products by name, category, or price",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_price": {"type": "number"},
                        "category": {"type": "string"},
                        "business_id": {"type": "string"}
                    },
                    "required": []
                }
            },
            {
                "name": "place_order",
                "description": "Place an order for products (customers)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_name": {"type": "string"},
                        "customer_phone": {"type": "string"},
                        "customer_email": {"type": "string"},
                        "delivery_address": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_id": {"type": "string"},
                                    "quantity": {"type": "integer"}
                                }
                            }
                        },
                        "payment_method": {"type": "string", "default": "mpesa"},
                        "delivery_instructions": {"type": "string"}
                    },
                    "required": ["customer_name", "customer_phone", "delivery_address", "items"]
                }
            },
            {
                "name": "get_order_status",
                "description": "Check the status of an existing order",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "customer_phone": {"type": "string"}
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "get_database_stats",
                "description": "Get current database statistics",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    async def process_message(self, user_message: str) -> str:
        """Process user message with LLM intelligence"""
        try:
            # Get user context
            user_context = self._get_user_context()
            
            # Build conversation history
            conversation_history = self._build_conversation_history(user_message, user_context)
            
            # Call OpenAI with function calling
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=conversation_history,
                functions=self.functions,
                function_call="auto",
                temperature=0.7,
                max_tokens=1500
            )
            
            # Handle the response
            return await self._handle_response(response, user_message)
            
        except Exception as e:
            return f"❌ I encountered an error: {str(e)}\n\nPlease try rephrasing your request or contact support."

    def _get_user_context(self) -> Dict[str, Any]:
        """Get current user session context"""
        return {
            "user_type": cl.user_session.get("user_type", "unknown"),
            "business_id": cl.user_session.get("business_id", "mama_jane_electronics"),
            "conversation_count": cl.user_session.get("message_count", 0)
        }

    def _build_conversation_history(self, user_message: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build conversation history for OpenAI"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add context
        context_msg = f"""CURRENT USER CONTEXT:
- User Type: {context['user_type']}
- Business ID: {context['business_id']} (if vendor)
- Messages in session: {context['conversation_count']}

DATABASE STATUS: ✅ JSON database is connected and operational

CRITICAL REMINDER: NEVER assume or make up product details. Always ask for complete information before adding products."""
        
        messages.append({"role": "system", "content": context_msg})
        
        # Get recent conversation history
        history = cl.user_session.get("conversation_history", [])
        for exchange in history[-5:]:  # Last 5 exchanges
            messages.append({"role": "user", "content": exchange.get("user_message", "")})
            messages.append({"role": "assistant", "content": exchange.get("ai_response", "")})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        return messages

    async def _handle_response(self, response, user_message: str) -> str:
        """Handle OpenAI response with potential function calls"""
        try:
            message = response.choices[0].message
            
            # Check if LLM wants to call a function
            if message.function_call:
                # Execute the function call
                function_result = await self._execute_function_call(message.function_call)
                
                # Get LLM to formulate a natural response based on function result
                return await self._get_natural_response(user_message, message.function_call, function_result)
            
            else:
                # Direct response from LLM
                response_text = message.content
                
                # Store conversation
                self._store_conversation(user_message, response_text)
                
                return response_text
                
        except Exception as e:
            return f"❌ Error processing response: {str(e)}"

    async def _execute_function_call(self, function_call) -> Any:
        """Execute the function call requested by LLM"""
        try:
            function_name = function_call.name
            function_args = json.loads(function_call.arguments)
            
            # Map function names to handlers
            function_map = {
                "validate_product_info": self._validate_product_info,
                "request_missing_product_info": self._request_missing_product_info,
                "set_user_role": self._set_user_role,
                "get_user_context": self._get_user_context_detailed,
                "add_product": self._add_product,
                "show_products": self._show_products,
                "update_product": self._update_product,
                "delete_product": self._delete_product,
                "get_business_stats": self._get_business_stats,
                "get_low_stock_products": self._get_low_stock_products,
                "browse_products": self._browse_products,
                "search_products": self._search_products,
                "place_order": self._place_order,
                "get_order_status": self._get_order_status,
                "get_database_stats": self._get_database_stats
            }
            
            if function_name in function_map:
                return await function_map[function_name](**function_args)
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": f"Function execution error: {str(e)}"}

    async def _get_natural_response(self, user_message: str, function_call, function_result) -> str:
        """Get natural language response based on function result"""
        try:
            # Create a follow-up prompt for natural response
            follow_up_messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": "", "function_call": {
                    "name": function_call.name,
                    "arguments": function_call.arguments
                }},
                {"role": "function", "name": function_call.name, "content": json.dumps(function_result)},
                {"role": "system", "content": "Based on the function result above, provide a helpful, natural response to the user. Format any data nicely and suggest relevant next steps. Remember to never make up product information."}
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=follow_up_messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            natural_response = response.choices[0].message.content
            
            # Store conversation
            self._store_conversation(user_message, natural_response)
            
            return natural_response
            
        except Exception as e:
            # Fallback to basic response
            if isinstance(function_result, dict) and "success" in function_result:
                if function_result["success"]:
                    return f"✅ {function_result.get('message', 'Operation completed successfully!')}"
                else:
                    return f"❌ {function_result.get('message', 'Operation failed.')}"
            
            return f"Operation completed. Result: {json.dumps(function_result, indent=2)}"

    def _store_conversation(self, user_message: str, ai_response: str):
        """Store conversation in session"""
        history = cl.user_session.get("conversation_history", [])
        history.append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "ai_response": ai_response
        })
        
        # Keep last 20 exchanges
        if len(history) > 20:
            history = history[-20:]
        
        cl.user_session.set("conversation_history", history)
        
        # Update message count
        count = cl.user_session.get("message_count", 0) + 1
        cl.user_session.set("message_count", count)

    # =============================================================================
    # NEW VALIDATION FUNCTIONS
    # =============================================================================

    async def _validate_product_info(self, **kwargs) -> Dict:
        """Validate that all required product information is complete"""
        required_fields = ["name", "price", "stock", "category", "brand", "description", "warranty"]
        missing_fields = []
        
        for field in required_fields:
            if field not in kwargs or not kwargs[field] or kwargs[field] == "":
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "complete": False,
                "missing_fields": missing_fields,
                "message": f"Missing required information: {', '.join(missing_fields)}"
            }
        
        # Validate data types and values
        try:
            price = float(kwargs["price"])
            stock = int(kwargs["stock"])
            
            if price <= 0:
                return {"complete": False, "message": "Price must be greater than 0"}
            if stock < 0:
                return {"complete": False, "message": "Stock cannot be negative"}
                
        except (ValueError, TypeError):
            return {"complete": False, "message": "Invalid price or stock format"}
        
        return {
            "complete": True,
            "message": "All required information provided",
            "validated_data": kwargs
        }

    async def _request_missing_product_info(self, missing_fields: List[str], provided_info: Dict = None) -> Dict:
        """Request missing product information from user"""
        field_prompts = {
            "name": "What is the exact product name and model? (e.g., 'iPhone 13 Pro Max 256GB Blue')",
            "price": "What is the price in Kenyan Shillings (KSh)?",
            "stock": "How many units do you have in stock?",
            "category": "What category does this product belong to? (Electronics, Accessories, etc.)",
            "brand": "What is the brand name?",
            "description": "Please provide a brief description of the product",
            "warranty": "What is the warranty period? (e.g., '12 months', '6 months')"
        }
        
        questions = []
        for field in missing_fields:
            if field in field_prompts:
                questions.append(f"• {field_prompts[field]}")
        
        provided_summary = ""
        if provided_info:
            provided_summary = "\n\n**Information you've already provided:**\n"
            for key, value in provided_info.items():
                if value:
                    provided_summary += f"• {key.title()}: {value}\n"
        
        return {
            "message": f"I need some additional information to add this product properly:\n\n" + 
                      "\n".join(questions) + provided_summary +
                      "\n\nPlease provide the missing details so I can add your product correctly.",
            "missing_fields": missing_fields,
            "requires_input": True
        }

    # =============================================================================
    # UPDATED FUNCTION IMPLEMENTATIONS
    # =============================================================================

    async def _set_user_role(self, role: str, business_id: str = "mama_jane_electronics") -> Dict:
        """Set user role"""
        cl.user_session.set("user_type", role)
        if role == "vendor":
            cl.user_session.set("business_id", business_id)
        
        return {
            "success": True,
            "message": f"Role set to {role}",
            "role": role,
            "business_id": business_id if role == "vendor" else None
        }

    async def _get_user_context_detailed(self) -> Dict:
        """Get detailed user context"""
        return {
            "user_type": cl.user_session.get("user_type", "unknown"),
            "business_id": cl.user_session.get("business_id"),
            "message_count": cl.user_session.get("message_count", 0),
            "session_active": True
        }

    async def _add_product(self, **kwargs) -> Dict:
        """Add product via vendor tools - with enhanced validation"""
        # First validate all information is complete
        validation = await self._validate_product_info(**kwargs)
        
        if not validation.get("complete", False):
            return {
                "success": False,
                "message": validation.get("message", "Incomplete product information"),
                "validation_error": True
            }
        
        # If validation passes, proceed with adding product
        return add_product_handler(**kwargs)

    async def _show_products(self, **kwargs) -> Dict:
        """Show products via vendor tools"""
        if "business_id" not in kwargs:
            kwargs["business_id"] = cl.user_session.get("business_id", "mama_jane_electronics")
        return show_products_handler(**kwargs)

    async def _update_product(self, **kwargs) -> Dict:
        """Update product via vendor tools"""
        return update_product_handler(**kwargs)

    async def _delete_product(self, **kwargs) -> Dict:
        """Delete product via vendor tools"""
        return delete_product_handler(**kwargs)

    async def _get_business_stats(self, **kwargs) -> Dict:
        """Get business stats"""
        if "business_id" not in kwargs:
            kwargs["business_id"] = cl.user_session.get("business_id", "mama_jane_electronics")
        return get_business_stats(**kwargs)

    async def _get_low_stock_products(self, **kwargs) -> Dict:
        """Get low stock products"""
        if "business_id" not in kwargs:
            kwargs["business_id"] = cl.user_session.get("business_id", "mama_jane_electronics")
        return get_low_stock_products(**kwargs)

    async def _browse_products(self, **kwargs) -> str:
        """Browse products for customers"""
        return browse_products_handler(kwargs)

    async def _search_products(self, **kwargs) -> str:
        """Search products for customers"""
        return search_products_handler(kwargs)

    async def _place_order(self, **kwargs) -> str:
        """Place order for customers"""
        return place_order_handler(kwargs)

    async def _get_order_status(self, **kwargs) -> str:
        """Get order status"""
        return get_order_status_handler(kwargs)

    async def _get_database_stats(self) -> Dict:
        """Get database statistics"""
        return db.get_stats()