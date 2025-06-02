"""
Sasabot - Multi-Business E-commerce Assistant
Chainlit version with JSON Database integration
"""

import chainlit as cl
import asyncio
from datetime import datetime
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import database and tools
try:
    from utils.simple_db import db, initialize_database
    from realtime.assistant import SasabotAssistant
    from realtime.vendor_tools import vendor_tools
    from realtime.customer_tools import customer_tools
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all required files are in place.")
    sys.exit(1)


def initialize_app_database():
    """
    Initialize the JSON database at app startup
    Validates files, shows stats, and handles errors
    """
    try:
        print("🔄 Initializing Sasabot database...")
        
        # Initialize database with data directory
        data_dir = "data"
        if not os.path.exists(data_dir):
            print(f"❌ Data directory '{data_dir}' not found!")
            print("Please create the data/ folder with JSON files:")
            print("- data/businesses.json")
            print("- data/products.json") 
            print("- data/orders.json")
            print("- data/customers.json")
            return False
        
        # Initialize database
        database = initialize_database(data_dir)
        
        # Validate data files
        print("📋 Validating data files...")
        validation_results = database.validate_data_files()
        
        # Show validation results
        all_valid = True
        for filename, is_valid in validation_results.items():
            if is_valid:
                print(f"✅ {filename} - Valid")
            else:
                print(f"❌ {filename} - Invalid or missing")
                all_valid = False
        
        if not all_valid:
            print("❌ Some data files are missing or invalid!")
            print("Please check your data/ folder and ensure all JSON files are properly formatted.")
            return False
        
        # Get database statistics
        print("📊 Loading database statistics...")
        stats = database.get_stats()
        
        if 'error' in stats:
            print(f"❌ Database error: {stats['error']}")
            return False
        
        # Display database stats
        print(f"🏪 Businesses: {stats.get('businesses_count', 0)}")
        print(f"📦 Products: {stats.get('products_count', 0)}")
        print(f"📋 Orders: {stats.get('orders_count', 0)}")
        print(f"👥 Customers: {stats.get('customers_count', 0)}")
        print(f"📁 Data directory: {stats.get('data_directory', data_dir)}")
        
        # Create backup at startup
        print("💾 Creating startup backup...")
        backup_location = database.create_full_backup()
        if backup_location:
            print(f"✅ Backup created: {backup_location}")
        else:
            print("⚠️ Could not create backup, but continuing...")
        
        # Test database operations
        print("🧪 Testing database operations...")
        
        # Test loading data
        try:
            businesses = database.get_businesses()
            products = database.get_products()
            orders = database.get_orders()
            
            # Show sample data
            if businesses:
                business_names = list(businesses.keys())[:3]
                print(f"✅ Businesses loaded: {', '.join(business_names)}")
            
            if products:
                product_count = len(products)
                active_products = len([p for p in products if p.get('status') == 'active'])
                print(f"✅ Products loaded: {active_products}/{product_count} active")
            
            if orders:
                recent_orders = len([o for o in orders if o.get('created_at', '').startswith('2024')])
                print(f"✅ Orders loaded: {recent_orders} recent orders")
                
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False
        
        print("🎉 Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("Please check your data files and try again.")
        return False


def get_database_stats():
    """Get current database statistics for display"""
    try:
        stats = db.get_stats()
        if 'error' in stats:
            return f"❌ Database error: {stats['error']}"
        
        return f"""
📊 **Database Statistics**
🏪 Businesses: {stats.get('businesses_count', 0)}
📦 Products: {stats.get('products_count', 0)}
📋 Orders: {stats.get('orders_count', 0)}
👥 Customers: {stats.get('customers_count', 0)}
📁 Data Directory: {stats.get('data_directory', 'data/')}
🕐 Last Updated: {stats.get('last_updated', 'Unknown')}
        """
    except Exception as e:
        return f"❌ Error getting stats: {e}"


def get_recent_activity():
    """Get recent order activity"""
    try:
        orders = db.get_orders()
        if not orders:
            return "📋 No recent orders found."
        
        # Get last 5 orders
        recent_orders = sorted(orders, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        activity = "📋 **Recent Orders:**\n"
        for order in recent_orders:
            order_id = order.get('id', 'Unknown')
            customer = order.get('customer_name', 'Unknown')
            status = order.get('status', 'unknown')
            total = order.get('grand_total', 0)
            activity += f"• {order_id}: {customer} - KSh {total:,} ({status})\n"
        
        return activity
        
    except Exception as e:
        return f"❌ Error getting recent activity: {e}"


# Initialize database at module level
print("🚀 Starting Sasabot application...")
database_initialized = initialize_app_database()

if not database_initialized:
    print("❌ Failed to initialize database. Please fix the issues above and restart.")
    sys.exit(1)

# Initialize assistant
try:
    print("🤖 Initializing Sasabot assistant...")
    assistant = SasabotAssistant()
    print("✅ Sasabot assistant ready!")
except Exception as e:
    print(f"❌ Failed to initialize assistant: {e}")
    sys.exit(1)


@cl.on_chat_start
async def start():
    """
    Called when a new chat session starts
    """
    # Welcome message with database info
    welcome_message = f"""
🤖 **Welcome to Sasabot!**
*Your intelligent assistant for multi-business e-commerce operations*

✅ **System Status:** Online and Ready
🕐 **Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{get_database_stats()}

{get_recent_activity()}

💡 **How to use Sasabot:**

**For Customers:**
• "Show me all available products"
• "Search for phones under 50000"
• "I want to buy a laptop"
• "Place an order for product ID 1"
• "Check status of order ORD001"

**For Vendors:**
• "Add a new product"
• "Update product ID 5 price to 30000"
• "Show my products"
• "Delete product ID 8"
• "Show recent orders"

**Database Commands:**
• "Show database stats"
• "Show recent activity"
• "Create backup"

🚀 **Type your message below to get started!**
    """
    
    await cl.Message(content=welcome_message).send()
    
    # Store initialization timestamp
    cl.user_session.set("start_time", datetime.now())
    cl.user_session.set("message_count", 0)


@cl.on_message
async def main(message: cl.Message):
    """
    Handle incoming messages from users
    """
    try:
        # Update message count
        msg_count = cl.user_session.get("message_count", 0) + 1
        cl.user_session.set("message_count", msg_count)
        
        user_input = message.content.strip()
        
        # Handle special database commands
        if user_input.lower() in ["show database stats", "database stats", "stats"]:
            response = get_database_stats()
            await cl.Message(content=response).send()
            return
            
        if user_input.lower() in ["show recent activity", "recent activity", "recent orders"]:
            response = get_recent_activity()
            await cl.Message(content=response).send()
            return
            
        if user_input.lower() in ["create backup", "backup"]:
            try:
                backup_path = db.create_full_backup()
                if backup_path:
                    response = f"✅ **Backup Created Successfully!**\n📁 Location: {backup_path}"
                else:
                    response = "❌ Backup creation failed. Please try again."
            except Exception as e:
                response = f"❌ Backup error: {e}"
            
            await cl.Message(content=response).send()
            return
            
        if user_input.lower() in ["reload data", "refresh", "reload"]:
            try:
                db.reload_all_data()
                response = "✅ **Data Reloaded Successfully!**\nAll data has been refreshed from JSON files."
            except Exception as e:
                response = f"❌ Data reload error: {e}"
            
            await cl.Message(content=response).send()
            return
        
        # Show typing indicator
        async with cl.Step(name="Processing", type="run") as step:
            step.output = "🤖 Sasabot is thinking..."
            
            # Process message with assistant
            response = await assistant.process_message(user_input)
            
            step.output = "✅ Response ready!"
        
        # Send response
        await cl.Message(content=response).send()
        
        # Add session info for long conversations
        if msg_count > 0 and msg_count % 10 == 0:
            start_time = cl.user_session.get("start_time")
            if start_time:
                session_duration = datetime.now() - start_time
                duration_mins = int(session_duration.total_seconds() / 60)
                
                session_info = f"""
💬 **Session Info:** {msg_count} messages in {duration_mins} minutes
🔄 Type 'stats' for database info or 'backup' to create backup
                """
                await cl.Message(content=session_info).send()
        
    except Exception as e:
        error_message = f"""
❌ **Error Processing Message**

Something went wrong while processing your request:
```
{str(e)}
```

💡 **Try:**
• Rephrasing your request
• Using simpler commands
• Typing 'stats' to check system status
• Restarting the chat if issues persist

🆘 **Need help?** Try asking:
"Show me all products" or "Help me place an order"
        """
        
        await cl.Message(content=error_message).send()


@cl.on_chat_end
async def end():
    """
    Called when chat session ends
    """
    # Get session stats
    start_time = cl.user_session.get("start_time")
    msg_count = cl.user_session.get("message_count", 0)
    
    if start_time:
        session_duration = datetime.now() - start_time
        duration_mins = int(session_duration.total_seconds() / 60)
        
        print(f"📊 Session ended: {msg_count} messages in {duration_mins} minutes")
    
    print("👋 Chat session ended")


if __name__ == "__main__":
    print("🚀 Sasabot is ready to serve!")
    print("💡 Run with: chainlit run app.py")
    print("🌐 Open your browser to start chatting!")