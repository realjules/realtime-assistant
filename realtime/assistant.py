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
    delete_product_handler, get_business_stats, get_low_stock_products,
    get_enhanced_business_stats, get_sales_analytics 
)
from .customer_tools import (
    browse_products_handler, search_products_handler, 
    place_order_handler, get_order_status_handler,
)

from .payment_tools import (
    initiate_mpesa_payment_handler, check_payment_status_handler, 
    cancel_payment_handler, get_payment_help_handler, 
    retry_payment_handler, complete_mpesa_payment_handler
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

PRODUCT REFERENCE RESOLUTION:
- When product operations fail, you will receive rich context in the response
- The context will include available_products, business info, and user search terms
- Use your intelligence to match user intent to available products from the context
- When products aren't found, analyze the available_products list and suggest the closest logical match
- Always show actual Product IDs prominently: "I found iPhone 13 (ID: 4), did you mean that?"
- If multiple options exist, present them clearly with IDs, names, and prices
- When suggesting alternatives, explain why: "You searched for 'iphone14' but we have iPhone 13 available"
- Make Product IDs easy to reference: "To update this product, use ID: 4 or say 'iPhone 13'"

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

ERROR HANDLING WITH CONTEXT:
- When functions return error_type: "product_not_found", use the context.available_products
- Show users what products ARE available, not just what's missing
- Present alternatives intelligently: "I didn't find that exact product, but here are similar options..."
- Always include actual Product IDs in suggestions
- Use context.suggestion_prompt to understand what the user was trying to do

ENHANCED USER EXPERIENCE:
- When showing products, always highlight Product IDs prominently
- Provide quick reference guides: "To update product, use: 'update [ID]' or 'update [name]'"
- When operations fail, immediately suggest correct alternatives
- Make it easy for users to reference products correctly

CAPABILITIES:
You can help with:
- Business inventory management (vendors)
- Product browsing and ordering (customers) 
- Real-time data from JSON database
- M-Pesa payments and delivery coordination
- Business analytics and reporting
- M-Pesa payment processing for orders
- Payment status tracking and troubleshooting
- Payment retry and cancellation options

IMPORTANT GUIDELINES:
1. Always check user's role (vendor/customer) before suggesting actions
2. Use function calls to interact with the JSON database
3. Provide specific, actionable responses with actual product references
4. When users seem unsure, offer to help them choose vendor or customer mode
5. Format prices in Kenyan Shillings (KSh) with proper comma formatting
6. Be proactive in suggesting next steps with correct product IDs


## Business Analytics Capabilities

You have access to powerful business analytics tools:

1. **get_business_stats(business_id)** - Comprehensive business overview
   - Revenue trends (last 30 days)
   - Top selling products
   - Customer metrics (retention, new customers)
   - Order performance
   - Stock alerts with sales velocity

2. **get_sales_analytics(business_id, period)** - Detailed sales analysis
   - Best/worst performing products
   - Category performance comparison
   - Daily sales patterns
   - Payment method breakdown

## When to Use Analytics

- User asks: "business stats", "how's my business", "sales report"
- User requests: "revenue trends", "top products", "customer metrics"
- User inquires: "product performance", "sales analysis", "analytics"
- Automatically for weekly/monthly business reviews

## How to Format Analytics Responses

### For WhatsApp Format (Primary):
- Use emojis for visual hierarchy: 🏪💰📊👥📦⚠️💡🎯
- Format currency as "KSh X,XXX" with commas
- Show trends with arrows: 📈📉➡️
- Use traffic lights: 🔴🟡🟢 for priority/status
- Keep sections concise and scannable
- Include actionable insights and next steps

### Structure:
```
🏪 [BUSINESS NAME]
📊 [Report Type] - [Period]

💰 [KEY METRICS SECTION]
[Revenue, growth, etc.]

🔥 [TOP PRODUCTS SECTION]
[Numbered list of top performers]

👥 [CUSTOMER INSIGHTS]
[Customer metrics and patterns]

📦 [OPERATIONAL METRICS]
[Orders, fulfillment, etc.]

⚠️ [ALERTS & PRIORITIES]
[Stock alerts, urgent actions]

💡 [KEY INSIGHTS]
[Main takeaways]

🎯 [NEXT ACTIONS]
[Specific recommendations]
```

### Example Response Format:
```
🏪 MAMA JANE'S ELECTRONICS
📊 Business Dashboard - January 2025

💰 REVENUE TRENDS (30 days)
Week 1: KSh 45,000 📈
Week 2: KSh 52,000 📈
Week 3: KSh 48,000 📉
Week 4: KSh 61,000 📈
Growth: +12.5% vs last month ✅

🔥 TOP 5 SELLING PRODUCTS
1. iPhone 13 - 8 sold, KSh 600k
2. Samsung A54 - 12 sold, KSh 420k
3. AirPods Pro - 15 sold, KSh 225k

👥 CUSTOMER INSIGHTS
Total: 47 customers (8 new)
Retention: 32% (15 repeat customers) ✅
Top Location: Westlands

📦 ORDER PERFORMANCE
Completion: 94% (47/50 orders) ✅
Avg Processing: 18 hours ⚡

⚠️ STOCK ALERTS
🔴 iPhone 13: 2 left - RESTOCK NOW
🟡 Samsung A54: 5 left - Restock soon

💡 KEY INSIGHT: iPhone demand high but low stock

🎯 NEXT ACTIONS:
1. Restock iPhone 13 immediately
2. Follow up with new customers
```

## Important Guidelines:

1. **Always call analytics functions** when users request business performance data
2. **Format responses in WhatsApp-friendly style** with emojis and clear sections
3. **Include actionable insights**, not just raw numbers
4. **Prioritize urgent alerts** (stock issues, declining trends)
5. **Use Kenyan context** (KSh currency, local business patterns)
6. **Keep insights relevant** to SME needs (cash flow, inventory, customers)
7. **Provide specific next steps** the user can act on immediately

Remember: Transform data into business intelligence that busy Kenyan entrepreneurs can quickly understand and act upon.

CONTEXT AWARENESS:
- Remember what the user is trying to accomplish
- Offer relevant follow-up actions with specific product references
- Explain the impact of changes (e.g., "This will update your JSON database")
- When products aren't found, use available context to suggest alternatives

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
            },
            {
                "name": "get_enhanced_business_stats",
                "description": "Get comprehensive business statistics including revenue trends, top products, customer metrics, and stock alerts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string", "description": "Business ID to analyze"}
                    },
                    "required": ["business_id"]
                }
            },
            {
                "name": "get_sales_analytics", 
                "description": "Get detailed sales analytics including product performance, category analysis, and sales patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string", "description": "Business ID to analyze"},
                        "period": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly", "quarterly", "all"],
                            "description": "Analysis period",
                            "default": "monthly"
                        }
                    },
                    "required": ["business_id"]
                }
            },
            {
                "name": "initiate_mpesa_payment",
                "description": "Start M-Pesa payment process for a customer order",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to pay for (e.g., ORD001)"
                        },
                        "customer_phone": {
                            "type": "string",
                            "description": "Customer's M-Pesa phone number (optional, will use order phone)"
                        }
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "check_payment_status", 
                "description": "Check the current status of a payment transaction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payment_id": {
                            "type": "string",
                            "description": "Payment ID to check (e.g., PAY001)"
                        }
                    },
                    "required": ["payment_id"]
                }
            },
            {
                "name": "cancel_payment",
                "description": "Cancel a pending M-Pesa payment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payment_id": {
                            "type": "string",
                            "description": "Payment ID to cancel (e.g., PAY001)"
                        }
                    },
                    "required": ["payment_id"]
                }
            },
            {
                "name": "get_payment_help",
                "description": "Get help and troubleshooting information for M-Pesa payments",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "retry_payment",
                "description": "Retry payment for an order after previous failure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to retry payment for"
                        },
                        "customer_phone": {
                            "type": "string",
                            "description": "Customer phone number (optional)"
                        }
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "complete_mpesa_payment",
                "description": "Complete payment simulation (for demo/testing purposes only)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payment_id": {
                            "type": "string",
                            "description": "Payment ID to complete"
                        },
                        "force_success": {
                            "type": "boolean",
                            "description": "Force success or failure (optional)"
                        }
                    },
                    "required": ["payment_id"]
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
    async def _get_enhanced_business_stats(self, **kwargs) -> Dict:
        """Get enhanced business statistics"""
        if "business_id" not in kwargs:
            kwargs["business_id"] = cl.user_session.get("business_id")
        
        try:
            result = get_enhanced_business_stats(kwargs["business_id"])
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting enhanced business stats: {str(e)}",
                "error_type": "system_error"
            }

    async def _get_sales_analytics(self, **kwargs) -> Dict:
        """Get detailed sales analytics"""
        if "business_id" not in kwargs:
            kwargs["business_id"] = cl.user_session.get("business_id")
        
        # Set default period if not provided
        if "period" not in kwargs:
            kwargs["period"] = "monthly"
        
        try:
            result = get_sales_analytics(kwargs["business_id"], kwargs["period"])
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting sales analytics: {str(e)}",
                "error_type": "system_error"
            }

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
                "get_database_stats": self._get_database_stats,
                "get_enhanced_business_stats": self._get_enhanced_business_stats,
                "get_sales_analytics": self._get_sales_analytics,
                "initiate_mpesa_payment": self._initiate_mpesa_payment,
                "check_payment_status": self._check_payment_status,
                "cancel_payment": self._cancel_payment,
                "get_payment_help": self._get_payment_help,
                "retry_payment": self._retry_payment,
                "complete_mpesa_payment": self._complete_mpesa_payment
            }
            
            if function_name in function_map:
                return await function_map[function_name](**function_args)
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": f"Function execution error: {str(e)}"}

    async def _get_natural_response(self, user_message: str, function_call, function_result) -> str:
        """Get natural language response based on function result with enhanced context processing"""
        try:
            # Enhanced processing for product-related errors
            if isinstance(function_result, dict):
                error_type = function_result.get("error_type")
                context = function_result.get("context", {})
                
                # Special handling for product not found errors
                if error_type == "product_not_found" and context:
                    follow_up_messages = [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": "", "function_call": {
                            "name": function_call.name,
                            "arguments": function_call.arguments
                        }},
                        {"role": "function", "name": function_call.name, "content": json.dumps(function_result)},
                        {"role": "system", "content": f"""
    The user's operation failed because the product wasn't found. You have been given rich context to help resolve this:

    CONTEXT PROVIDED:
    - User searched for: '{context.get('user_input', 'unknown')}'
    - Available products: {len(context.get('available_products', []))} products available
    - Business: {context.get('business_name', 'Unknown')}
    - Suggestion prompt: {context.get('suggestion_prompt', '')}

    INSTRUCTIONS:
    1. Acknowledge that the specific product wasn't found
    2. Analyze the available_products list to find the closest match to what the user wanted
    3. Present 2-3 best alternatives with their exact Product IDs prominently displayed
    4. Format as: "I found iPhone 13 (🆔 ID: 4) - KSh 75,000. Did you mean this product?"
    5. If no close matches, show the available products and ask for clarification
    6. Always show actual Product IDs so users know how to reference them correctly
    7. Be helpful and guide them to the right product

    Remember: Your job is to help users find the right product using your intelligence and the available data.
                        """}
                    ]
                
                # Special handling for validation errors
                elif error_type == "validation_error":
                    follow_up_messages = [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": "", "function_call": {
                            "name": function_call.name,
                            "arguments": function_call.arguments
                        }},
                        {"role": "function", "name": function_call.name, "content": json.dumps(function_result)},
                        {"role": "system", "content": f"""
    The user's request has validation errors. Help them fix these issues:

    VALIDATION ERRORS: {function_result.get('validation_errors', [])}

    INSTRUCTIONS:
    1. Clearly explain what went wrong
    2. Provide specific guidance on how to fix each error
    3. Give examples of correct format
    4. Be encouraging and helpful
    5. If working with an existing product, show its current details for reference
                        """}
                    ]
                
                # Enhanced context processing for search results
                elif context and context.get("available_products"):
                    follow_up_messages = [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": "", "function_call": {
                            "name": function_call.name,
                            "arguments": function_call.arguments
                        }},
                        {"role": "function", "name": function_call.name, "content": json.dumps(function_result)},
                        {"role": "system", "content": f"""
    Process the function result and present the information clearly to the user. 

    SPECIAL INSTRUCTIONS:
    - If showing products, always make Product IDs prominent and easy to reference
    - Format products consistently: "🆔 ID: X | Product Name | Price | Stock"
    - Provide helpful guidance on next steps
    - If there are suggestions in the context, present them intelligently
    - Make it easy for users to reference products correctly in future operations

    CONTEXT: {json.dumps(context, indent=2)}
                        """}
                    ]
                
                else:
                    # Standard processing for other cases
                    follow_up_messages = [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": "", "function_call": {
                            "name": function_call.name,
                            "arguments": function_call.arguments
                        }},
                        {"role": "function", "name": function_call.name, "content": json.dumps(function_result)},
                        {"role": "system", "content": "Based on the function result above, provide a helpful, natural response to the user. Format any data nicely and suggest relevant next steps. Always make Product IDs prominent when displaying products."}
                    ]
            else:
                # Fallback for non-dict results
                follow_up_messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": "", "function_call": {
                        "name": function_call.name,
                        "arguments": function_call.arguments
                    }},
                    {"role": "function", "name": function_call.name, "content": json.dumps(function_result)},
                    {"role": "system", "content": "Based on the function result above, provide a helpful, natural response to the user. Format any data nicely and suggest relevant next steps."}
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
            # Enhanced fallback with context awareness
            if isinstance(function_result, dict):
                if function_result.get("success"):
                    return f"✅ {function_result.get('message', 'Operation completed successfully!')}"
                else:
                    error_msg = f"❌ {function_result.get('message', 'Operation failed.')}"
                    
                    # Add helpful context if available
                    context = function_result.get('context', {})
                    if context.get('available_products'):
                        error_msg += f"\n\n💡 Try checking these available products and their IDs for reference."
                    
                    return error_msg
            
            return f"Operation completed. Result: {json.dumps(function_result, indent=2)}"


    def _build_conversation_history(self, user_message: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build conversation history for OpenAI with enhanced context"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Enhanced context message
        context_msg = f"""CURRENT USER CONTEXT:
    - User Type: {context['user_type']}
    - Business ID: {context['business_id']} (if vendor)
    - Messages in session: {context['conversation_count']}

    DATABASE STATUS: ✅ JSON database is connected and operational

    CRITICAL REMINDER: 
    - NEVER assume or make up product details
    - Always ask for complete information before adding products
    - When products aren't found, use available context to suggest alternatives
    - Always show Product IDs prominently for easy reference
    - Help users find the right products using available data"""
        
        messages.append({"role": "system", "content": context_msg})
        
        # Get recent conversation history
        history = cl.user_session.get("conversation_history", [])
        for exchange in history[-5:]:  # Last 5 exchanges
            messages.append({"role": "user", "content": exchange.get("user_message", "")})
            messages.append({"role": "assistant", "content": exchange.get("ai_response", "")})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        return messages

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
    
    async def _initiate_mpesa_payment(self, **kwargs) -> Dict:
        """Initiate M-Pesa payment"""
        return initiate_mpesa_payment_handler(**kwargs)

    async def _check_payment_status(self, **kwargs) -> Dict:
        """Check payment status"""
        return check_payment_status_handler(**kwargs)

    async def _cancel_payment(self, **kwargs) -> Dict:
        """Cancel payment"""
        return cancel_payment_handler(**kwargs)

    async def _get_payment_help(self, **kwargs) -> Dict:
        """Get payment help"""
        return get_payment_help_handler(**kwargs)

    async def _retry_payment(self, **kwargs) -> Dict:
        """Retry payment"""
        return retry_payment_handler(**kwargs)

    async def _complete_mpesa_payment(self, **kwargs) -> Dict:
        """Complete payment simulation"""
        return complete_mpesa_payment_handler(**kwargs)
