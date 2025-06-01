import os
import asyncio
from openai import AsyncOpenAI

import chainlit as cl
from uuid import uuid4
from chainlit.logger import logger

from realtime import RealtimeClient

# Direct imports to avoid circular dependency issues
from realtime.tools.user_management import user_tools
from realtime.tools.vendor_tools import vendor_tools
from realtime.tools.customer_tools import customer_tools
from realtime.tools.conversation_flow import conversation_tools
from realtime.tools.demo_data import demo_tools

client = AsyncOpenAI()

# Combine tools
def get_tools_for_user_type(user_type: str):
    """Get appropriate tools based on user type"""
    if user_type == "vendor":
        return user_tools + vendor_tools + conversation_tools + demo_tools
    elif user_type == "customer":
        return user_tools + customer_tools + conversation_tools + demo_tools
    elif user_type == "unknown":
        return user_tools + conversation_tools + demo_tools
    else:
        return user_tools + vendor_tools + customer_tools + conversation_tools + demo_tools

def get_tool_info():
    """Get tool registry information"""
    all_tools = get_tools_for_user_type("all")
    return {
        "total_tools": len(all_tools),
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

async def setup_openai_realtime():
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient(api_key=os.getenv("OPENAI_API_KEY"))
    cl.user_session.set("track_id", str(uuid4()))

    async def handle_conversation_updated(event):
        item = event.get("item")
        delta = event.get("delta")
        """Currently used to stream audio back to the client."""
        if delta:
            # Only one of the following will be populated for any given event
            if "audio" in delta:
                audio = delta["audio"]  # Int16Array, audio added
                await cl.context.emitter.send_audio_chunk(
                    cl.OutputAudioChunk(
                        mimeType="pcm16",
                        data=audio,
                        track=cl.user_session.get("track_id"),
                    )
                )
            if "transcript" in delta:
                transcript = delta["transcript"]  # string, transcript added
                pass
            if "arguments" in delta:
                arguments = delta["arguments"]  # string, function arguments added
                pass

    async def handle_item_completed(item):
        """Used to populate the chat context with transcription once an item is completed."""
        # Update conversation context
        await update_conversation_context(item)

    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        await cl.context.emitter.send_audio_interrupt()

    async def handle_error(event):
        logger.error(f"OpenAI Realtime Error: {event}")

    openai_realtime.on("conversation.updated", handle_conversation_updated)
    openai_realtime.on("conversation.item.completed", handle_item_completed)
    openai_realtime.on("conversation.interrupted", handle_conversation_interrupt)
    openai_realtime.on("error", handle_error)

    cl.user_session.set("openai_realtime", openai_realtime)
    
    # Get appropriate tools based on user type
    user_type = cl.user_session.get("user_type", "unknown")
    user_tools_list = get_tools_for_user_type(user_type)
    
    logger.info(f"Loading {len(user_tools_list)} tools for user type: {user_type}")
    
    coros = [
        openai_realtime.add_tool(tool_def, tool_handler)
        for tool_def, tool_handler in user_tools_list
    ]
    await asyncio.gather(*coros)
    
    # Update system prompt based on user type
    await update_system_prompt(openai_realtime)


async def update_system_prompt(openai_realtime):
    """Update system prompt based on user type"""
    user_type = cl.user_session.get("user_type", "unknown")
    business_name = "your business"
    
    # Get business name for vendors
    if user_type == "vendor":
        business_id = cl.user_session.get("business_id", "mama_jane_electronics")
        from realtime.tools.demo_data import DEMO_BUSINESSES
        if business_id in DEMO_BUSINESSES:
            business_name = DEMO_BUSINESSES[business_id]["name"]
    
    if user_type == "vendor":
        system_prompt = f"""You are Sasabot, an intelligent AI business assistant for Kenyan entrepreneurs managing {business_name}.

CORE CAPABILITIES:
- Product & inventory management through natural conversation
- Business reports and analytics generation
- Smart alerts and notifications
- Revenue tracking and insights
- Customer behavior analysis

PERSONALITY & STYLE:
- Professional yet friendly and approachable
- Proactive in offering business insights
- Use Kenyan context (KSh currency, local terms)
- Concise but thorough responses
- Always confirm actions before executing

COMMUNICATION GUIDELINES:
- Use emojis for visual appeal and clarity
- Structure responses with clear headings
- Provide actionable insights and recommendations
- Ask clarifying questions when needed
- Celebrate business achievements

KEY BEHAVIORS:
- When showing products, highlight low stock items
- In reports, provide insights and recommendations
- For inventory, suggest reorder points
- Always format currency as "KSh X,XXX"
- Use natural language - no rigid commands needed

Remember: You're helping grow Kenyan businesses through intelligent conversation. Be the AI business partner they need!"""

    elif user_type == "customer":
        system_prompt = """You are Sasabot, a friendly and helpful shopping assistant for Kenyan customers.

CORE CAPABILITIES:
- Product browsing and recommendation
- Shopping cart and order management
- Price comparison and deal finding
- Order tracking and customer support
- Payment assistance (M-Pesa integration)

PERSONALITY & STYLE:
- Warm, welcoming, and patient
- Enthusiastic about helping customers find what they need
- Use common Kenyan greetings ("Karibu", "Asante")
- Celebratory when customers make purchases
- Empathetic when handling complaints

COMMUNICATION GUIDELINES:
- Use friendly emojis throughout conversations
- Provide clear product descriptions with prices
- Guide customers step-by-step through processes
- Always confirm before processing payments
- Offer alternatives when products unavailable

SHOPPING EXPERIENCE:
- Show product availability clearly
- Highlight deals and promotions
- Suggest complementary products
- Make ordering process simple and clear
- Provide tracking information proactively

KENYAN CONTEXT:
- All prices in KSh (Kenyan Shillings)
- M-Pesa payment references
- Local delivery options and timeframes
- Understand local shopping preferences

Remember: Create an amazing shopping experience that feels personal, helpful, and trustworthy!"""

    else:
        system_prompt = """You are Sasabot, an AI assistant built specifically for Kenyan businesses and their customers.

PURPOSE:
Help users understand and experience how Sasabot works as a business automation platform on WhatsApp.

DEMO CONTEXT:
- This is a demonstration of the real WhatsApp system
- Users can experience both vendor and customer modes
- Show the power of AI-driven business automation
- Explain real-world benefits and implementation

KEY FEATURES TO HIGHLIGHT:
- Natural language business management
- M-Pesa payment integration
- Real-time inventory tracking
- Comprehensive business analytics
- 24/7 customer service automation

GUIDANCE APPROACH:
- Help users choose between vendor or customer experience
- Explain how each mode works in real WhatsApp implementation
- Showcase the benefits for Kenyan SMEs
- Be encouraging about AI adoption

KENYAN MARKET FOCUS:
- Built for Kenyan business workflows
- Leverages WhatsApp's 90%+ penetration
- Integrates with M-Pesa payment system
- Supports Swahili and English languages
- Affordable for small and medium businesses

Remember: You're demonstrating the future of business automation in Kenya. Show users why Sasabot is revolutionary!"""

    try:
        await openai_realtime.update_session(instructions=system_prompt)
        logger.info(f"System prompt updated for user type: {user_type}")
    except Exception as e:
        logger.error(f"Failed to update system prompt: {e}")


async def update_conversation_context(item):
    """Update conversation context with completed items"""
    try:
        from realtime.tools.conversation_flow import maintain_context_handler
        
        # Extract relevant information from the item
        item_content = item.get("content", [])
        if item_content:
            content_text = ""
            for content in item_content:
                if content.get("type") == "text":
                    content_text += content.get("text", "")
            
            if content_text:
                await maintain_context_handler(
                    user_message="", 
                    ai_response=content_text,
                    intent=""
                )
    except Exception as e:
        logger.error(f"Failed to update conversation context: {e}")


@cl.on_chat_start
async def start():
    """Initialize Sasabot and start the conversation"""
    try:
        # Initialize demo data
        from realtime.tools.demo_data import load_demo_data_handler
        demo_result = await load_demo_data_handler()
        logger.info("Demo data loaded successfully")
        
        # Initialize user session
        cl.user_session.set("user_type", "unknown")
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("message_count", 0)
        
        # Send Sasabot welcome message
        from realtime.tools.conversation_flow import welcome_message_handler
        welcome_response = await welcome_message_handler("unknown")
        
        await cl.Message(content=welcome_response["message"]).send()
        
        # Setup OpenAI realtime with initial tools
        await setup_openai_realtime()
        
        # Log successful startup
        tool_info = get_tool_info()
        logger.info(f"Sasabot started successfully with {tool_info['total_tools']} tools available")
        
    except Exception as e:
        logger.error(f"Failed to start Sasabot: {e}")
        await cl.ErrorMessage(
            content="😔 Sorry, there was an error starting Sasabot. Please refresh the page and try again."
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming text messages"""
    try:
        # Get current user type
        user_type = cl.user_session.get("user_type", "unknown")
        
        # Handle role selection for unknown users
        if user_type == "unknown":
            await handle_role_selection(message)
            return
        
        # Update message count
        message_count = cl.user_session.get("message_count", 0) + 1
        cl.user_session.set("message_count", message_count)
        
        # Try to use realtime client first
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        if openai_realtime and openai_realtime.is_connected():
            await openai_realtime.send_user_message_content(
                [{"type": "input_text", "text": message.content}]
            )
        else:
            # Fallback to direct tool usage if realtime not connected
            await handle_message_with_tools(message)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await cl.ErrorMessage(
            content="😔 Sorry, I encountered an error. Please try again or type 'help' for assistance."
        ).send()


async def handle_role_selection(message: cl.Message):
    """Handle user role selection during onboarding"""
    message_lower = message.content.lower()
    
    try:
        if any(word in message_lower for word in ["vendor", "business", "owner", "manage", "sell"]):
            # Set vendor role
            from realtime.tools.user_management import set_user_role_handler
            await set_user_role_handler("vendor")
            
            # Reload realtime client with vendor tools
            await setup_openai_realtime()
            
            # Show vendor menu
            from realtime.tools.vendor_tools import vendor_menu_handler
            response = await vendor_menu_handler()
            await cl.Message(content=response["menu"]).send()
            
            logger.info("User selected vendor role")
            
        elif any(word in message_lower for word in ["customer", "shop", "buy", "purchase", "browse"]):
            # Set customer role
            from realtime.tools.user_management import set_user_role_handler
            await set_user_role_handler("customer")
            
            # Reload realtime client with customer tools
            await setup_openai_realtime()
            
            # Show customer menu
            from realtime.tools.customer_tools import customer_menu_handler
            response = await customer_menu_handler()
            await cl.Message(content=response["menu"]).send()
            
            logger.info("User selected customer role")
            
        else:
            # User didn't clearly select a role, provide guidance
            guidance_message = """🤔 **Let me help you choose:**

**Say one of these:**
👨‍💼 **"vendor"** or **"business owner"** - Manage your business
👥 **"customer"** or **"shopper"** - Browse and buy products

**Or describe what you want to do:**
• "I want to manage my inventory"
• "I'm looking to buy a phone"
• "Show me the business dashboard"
• "I want to shop for electronics"

**What brings you to Sasabot today?**"""
            
            await cl.Message(content=guidance_message).send()
            
    except Exception as e:
        logger.error(f"Error handling role selection: {e}")
        await cl.ErrorMessage(
            content="😔 Sorry, there was an error setting up your account. Please try again."
        ).send()


async def handle_message_with_tools(message: cl.Message):
    """Fallback message handling using tools directly when realtime is unavailable"""
    user_type = cl.user_session.get("user_type", "unknown")
    
    try:
        # Parse user intent
        from realtime.tools.conversation_flow import parse_user_intent_handler
        intent_result = await parse_user_intent_handler(message.content, user_type)
        
        intent = intent_result["intent"]
        params = intent_result.get("parameters", {})
        confidence = intent_result.get("confidence", 0.5)
        
        logger.info(f"Parsed intent: {intent} (confidence: {confidence}) for user type: {user_type}")
        
        # Route to appropriate tool based on intent
        response_message = await route_intent_to_tool(intent, params, user_type, message.content)
        
        # Send response
        await cl.Message(content=response_message).send()
        
        # Update conversation context
        from realtime.tools.conversation_flow import maintain_context_handler
        await maintain_context_handler(message.content, response_message, intent)
        
    except Exception as e:
        logger.error(f"Error in fallback message handling: {e}")
        await cl.Message(
            content="🤔 I didn't quite understand that. Could you try rephrasing, or type 'help' for available commands?"
        ).send()


async def route_intent_to_tool(intent: str, params: dict, user_type: str, original_message: str) -> str:
    """Route user intent to appropriate tool and return response"""
    
    try:
        # Help requests
        if intent == "help_request":
            from realtime.tools.conversation_flow import help_system_handler
            response = await help_system_handler(user_type)
            return response["message"]
        
        # Role switching
        if intent == "switch_role":
            target_role = params.get("target_role", "customer" if user_type == "vendor" else "vendor")
            from realtime.tools.user_management import switch_user_role_handler
            response = await switch_user_role_handler(target_role)
            
            # Reload tools for new role
            await setup_openai_realtime()
            return response["message"]
        
        # Vendor-specific intents
        if user_type == "vendor":
            if intent == "add_product":
                from realtime.tools.vendor_tools import add_product_handler
                product_name = params.get("product_name", "")
                price = params.get("price", 0)
                
                if not product_name or price <= 0:
                    return "🤔 To add a product, please specify: 'Add product [name] [price]'\n\nExample: 'Add product iPhone 75000'"
                
                response = await add_product_handler(product_name, price)
                return response["message"]
            
            elif intent == "show_products":
                from realtime.tools.vendor_tools import show_products_handler
                response = await show_products_handler()
                return response["message"]
            
            elif intent == "generate_report":
                period = params.get("period", "daily")
                from realtime.tools.vendor_tools import generate_report_handler
                response = await generate_report_handler(period)
                return response["message"]
            
            elif intent == "check_stock":
                from realtime.tools.vendor_tools import check_stock_handler
                response = await check_stock_handler()
                return response["message"]
            
            elif intent == "show_vendor_menu":
                from realtime.tools.vendor_tools import vendor_menu_handler
                response = await vendor_menu_handler()
                return response["menu"]
        
        # Customer-specific intents
        elif user_type == "customer":
            if intent == "browse_products":
                from realtime.tools.customer_tools import browse_products_handler
                category = params.get("category", "all")
                max_price = params.get("max_price")
                response = await browse_products_handler(category, max_price)
                return response["message"]
            
            elif intent == "search_products":
                search_term = params.get("search_term", "").strip()
                if not search_term:
                    return "🔍 What product are you looking for? Try: 'Search for phones' or 'Find laptops'"
                
                from realtime.tools.customer_tools import search_products_handler
                response = await search_products_handler(search_term)
                return response["message"]
            
            elif intent == "buy_product" or intent == "place_order":
                product_name = params.get("product_name", "").strip()
                if not product_name:
                    return "🛒 Which product would you like to buy? Try: 'Buy Samsung phone' or browse products first."
                
                from realtime.tools.customer_tools import place_order_handler
                response = await place_order_handler(product_name=product_name, use_cart=False)
                return response["message"]
            
            elif intent == "view_cart":
                from realtime.tools.customer_tools import view_cart_handler
                response = await view_cart_handler()
                return response["message"]
            
            elif intent == "track_order":
                from realtime.tools.customer_tools import track_order_handler
                response = await track_order_handler()
                return response["message"]
            
            elif intent == "show_customer_menu":
                from realtime.tools.customer_tools import customer_menu_handler
                response = await customer_menu_handler()
                return response["menu"]
        
        # General conversation fallback
        if intent == "general_conversation":
            if user_type == "vendor":
                return "🏪 I'm here to help manage your business! Try:\n• 'Show my products'\n• 'Add product [name] [price]'\n• 'Daily report'\n• 'Help' for more options"
            elif user_type == "customer":
                return "🛒 I'm here to help you shop! Try:\n• 'Show products'\n• 'Search for [item]'\n• 'What's under 30k?'\n• 'Help' for more options"
            else:
                return "🤖 Please choose your role first:\n• Say 'vendor' for business management\n• Say 'customer' for shopping"
        
        # Default fallback
        return f"🤔 I understand you want to {intent.replace('_', ' ')}, but I need more information. Try being more specific or type 'help' for available commands."
        
    except Exception as e:
        logger.error(f"Error routing intent {intent}: {e}")
        return "😔 Sorry, I encountered an error processing that request. Please try again or type 'help'."


@cl.on_audio_start
async def on_audio_start():
    """Handle voice conversation start"""
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        await openai_realtime.connect()
        logger.info("Connected to OpenAI realtime for voice")
        
        # Send audio-specific welcome if needed
        user_type = cl.user_session.get("user_type", "unknown")
        if user_type != "unknown":
            voice_welcome = "🎤 Voice mode activated! You can now speak naturally to manage your business." if user_type == "vendor" else "🎤 Voice mode activated! You can now speak to browse and shop."
            await cl.Message(content=voice_welcome).send()
        
        return True
    except Exception as e:
        logger.error(f"Failed to connect to OpenAI realtime: {e}")
        await cl.ErrorMessage(
            content=f"😔 Voice mode failed to activate: {str(e)}\nYou can still use text chat!"
        ).send()
        return False


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """Handle incoming audio chunks"""
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.append_input_audio(chunk.data)
    else:
        logger.warning("RealtimeClient is not connected - audio chunk ignored")


@cl.on_audio_end
@cl.on_chat_end
@cl.on_stop
async def on_end():
    """Clean up when conversation ends"""
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        if openai_realtime and openai_realtime.is_connected():
            await openai_realtime.disconnect()
            logger.info("Disconnected from OpenAI realtime")
        
        # Log session statistics
        message_count = cl.user_session.get("message_count", 0)
        user_type = cl.user_session.get("user_type", "unknown")
        logger.info(f"Session ended - User type: {user_type}, Messages: {message_count}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    # This allows the app to be run directly for testing
    logger.info("Starting Sasabot application...")