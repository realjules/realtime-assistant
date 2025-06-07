"""
M-Pesa Payment Tools for Sasabot
Handles M-Pesa payment simulation for Kenyan customers
"""

import json
import random
import string
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

# Import database
from utils.simple_db import db


class MPesaSimulator:
    """Simulates M-Pesa payment processing"""
    
    # Realistic M-Pesa settings
    PROCESSING_TIME_MIN = 15  # seconds
    PROCESSING_TIME_MAX = 30  # seconds
    SUCCESS_RATE = 0.9  # 90% success rate
    TIMEOUT_SECONDS = 60
    
    # M-Pesa transaction ID format (10 characters, letters and numbers)
    @staticmethod
    def generate_transaction_id() -> str:
        """Generate realistic M-Pesa transaction ID"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    @staticmethod
    def validate_kenyan_phone(phone: str) -> str:
        """Validate and normalize Kenyan phone number"""
        if not phone:
            raise ValueError("Phone number is required")
        
        # Remove spaces and hyphens
        phone = phone.replace(" ", "").replace("-", "")
        
        # Convert to proper +254 format
        if phone.startswith('07') or phone.startswith('01'):
            return '+254' + phone[1:]
        elif phone.startswith('254'):
            return '+' + phone
        elif phone.startswith('+254'):
            return phone
        else:
            raise ValueError("Invalid Kenyan phone number format")
    
    @staticmethod
    def simulate_payment_outcome() -> bool:
        """Simulate whether payment succeeds or fails"""
        return random.random() < MPesaSimulator.SUCCESS_RATE
    
    @staticmethod
    def get_processing_delay() -> int:
        """Get realistic processing delay in seconds"""
        return random.randint(
            MPesaSimulator.PROCESSING_TIME_MIN, 
            MPesaSimulator.PROCESSING_TIME_MAX
        )


def validate_payment_request(order_id: str, customer_phone: str) -> Dict[str, Any]:
    """
    Validate payment request before processing
    """
    try:
        # Validate order exists
        order = db.get_order_by_id(order_id)
        if not order:
            return {
                "valid": False,
                "error": f"Order {order_id} not found",
                "error_type": "order_not_found"
            }
        
        # Check if order already paid
        if order.get('payment_status') == 'completed':
            return {
                "valid": False,
                "error": f"Order {order_id} is already paid",
                "error_type": "already_paid",
                "existing_payment": order.get('payment_id')
            }
        
        # Validate phone number
        try:
            normalized_phone = MPesaSimulator.validate_kenyan_phone(customer_phone)
        except ValueError as e:
            return {
                "valid": False,
                "error": str(e),
                "error_type": "invalid_phone"
            }
        
        # Check if customer phone matches order (optional security check)
        order_phone = order.get('customer_phone', '')
        if order_phone and order_phone != normalized_phone:
            return {
                "valid": False,
                "error": "Phone number doesn't match order",
                "error_type": "phone_mismatch"
            }
        
        return {
            "valid": True,
            "order": order,
            "normalized_phone": normalized_phone
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation error: {str(e)}",
            "error_type": "system_error"
        }


def initiate_mpesa_payment_handler(order_id: str, customer_phone: str = None) -> Dict[str, Any]:
    """
    Initiate M-Pesa payment for an order
    """
    try:
        # Get customer phone from order if not provided
        if not customer_phone:
            order = db.get_order_by_id(order_id)
            if order:
                customer_phone = order.get('customer_phone')
        
        if not customer_phone:
            return {
                "success": False,
                "message": "❌ Phone number is required for M-Pesa payment",
                "error_type": "missing_phone",
                "data": None
            }
        
        # Validate payment request
        validation = validate_payment_request(order_id, customer_phone)
        if not validation["valid"]:
            if validation["error_type"] == "already_paid":
                return {
                    "success": False,
                    "message": f"✅ Order {order_id} is already paid!\n\n💳 Payment ID: {validation['existing_payment']}\n\n💡 Type 'order status {order_id}' to check delivery status",
                    "error_type": "already_paid",
                    "data": validation
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ {validation['error']}",
                    "error_type": validation["error_type"],
                    "data": None
                }
        
        order = validation["order"]
        normalized_phone = validation["normalized_phone"]
        
        # Generate payment ID
        payments = db.load_json('payments')
        existing_ids = [int(p.get('payment_id', 'PAY000')[3:]) for p in payments if p.get('payment_id', '').startswith('PAY')]
        new_payment_number = max(existing_ids, default=0) + 1
        payment_id = f"PAY{new_payment_number:03d}"
        
        # Create payment record
        payment_record = {
            "payment_id": payment_id,
            "order_id": order_id,
            "customer_phone": normalized_phone,
            "amount": order.get('grand_total', 0),
            "method": "mpesa",
            "status": "pending",
            "transaction_id": None,
            "initiated_at": datetime.now().isoformat(),
            "completed_at": None,
            "mpesa_phone": normalized_phone,
            "merchant_reference": order_id,
            "processing_delay": MPesaSimulator.get_processing_delay()
        }
        
        # Save payment record
        payments.append(payment_record)
        success = db.save_json('payments', payments)
        
        if not success:
            return {
                "success": False,
                "message": "❌ Failed to create payment record. Please try again.",
                "error_type": "database_error",
                "data": None
            }
        
        # Update order with payment initiation
        db.update_order_status(order_id, "payment_pending")
        
        # Get business info for display
        business = db.get_business(order.get('business_id', ''))
        business_name = business.get('name', 'Unknown Business') if business else 'Unknown Business'
        
        # Prepare response message
        message = f"""💳 **M-Pesa Payment Initiated**

📋 Order: {order_id}
💰 Amount: KSh {order.get('grand_total', 0):,}
🏪 Merchant: {business_name}
📱 Phone: {normalized_phone}

✅ STK Push sent to your phone
📲 **CHECK YOUR PHONE NOW** and enter M-Pesa PIN

⏱️ Processing... Please wait (up to 60 seconds)
❌ Type 'cancel payment {payment_id}' to stop

💡 Don't see the prompt? Dial *334# → Lipa na M-Pesa → Pay Bill → 174379"""

        return {
            "success": True,
            "message": message,
            "payment_id": payment_id,
            "processing_delay": payment_record["processing_delay"],
            "data": {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": order.get('grand_total', 0),
                "phone": normalized_phone,
                "business_name": business_name
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error initiating payment: {str(e)}",
            "error_type": "system_error",
            "data": None
        }


def check_payment_status_handler(payment_id: str) -> Dict[str, Any]:
    """
    Check the current status of a payment
    """
    try:
        payments = db.load_json('payments')
        payment = None
        
        for p in payments:
            if p.get('payment_id') == payment_id:
                payment = p
                break
        
        if not payment:
            return {
                "success": False,
                "message": f"❌ Payment {payment_id} not found",
                "error_type": "payment_not_found",
                "data": None
            }
        
        status = payment.get('status', 'unknown')
        order_id = payment.get('order_id')
        amount = payment.get('amount', 0)
        
        if status == "pending":
            message = f"""⏳ **Payment Status: PENDING**

💳 Payment ID: {payment_id}
📋 Order: {order_id}
💰 Amount: KSh {amount:,}

📱 STK Push sent to {payment.get('mpesa_phone')}
⏱️ Waiting for PIN entry...

💡 Check your phone for M-Pesa prompt"""

        elif status == "processing":
            message = f"""🔄 **Payment Status: PROCESSING**

💳 Payment ID: {payment_id}
📋 Order: {order_id}
💰 Amount: KSh {amount:,}

📱 PIN entered, transaction in progress...
⏱️ Please wait for confirmation"""

        elif status == "completed":
            transaction_id = payment.get('transaction_id', 'Unknown')
            completed_at = payment.get('completed_at', '')
            
            message = f"""✅ **Payment Status: COMPLETED**

💳 Payment ID: {payment_id}
📋 Order: {order_id}
💰 Amount: KSh {amount:,}
📱 M-Pesa Code: {transaction_id}
🕒 Completed: {completed_at[:19] if completed_at else 'Unknown'}

🎉 Payment successful! Your order is confirmed."""

        elif status == "failed":
            message = f"""❌ **Payment Status: FAILED**

💳 Payment ID: {payment_id}
📋 Order: {order_id}
💰 Amount: KSh {amount:,}

🚫 Transaction was not completed
💡 Try again: 'retry payment {order_id}'"""

        elif status == "expired":
            message = f"""⏰ **Payment Status: EXPIRED**

💳 Payment ID: {payment_id}
📋 Order: {order_id}
💰 Amount: KSh {amount:,}

🕐 Payment timed out (60 seconds)
🔄 Try again: 'retry payment {order_id}'"""

        else:
            message = f"""❓ **Payment Status: {status.upper()}**

💳 Payment ID: {payment_id}
📋 Order: {order_id}
💰 Amount: KSh {amount:,}

💬 Contact support if you need help"""

        return {
            "success": True,
            "message": message,
            "status": status,
            "data": payment
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error checking payment status: {str(e)}",
            "error_type": "system_error",
            "data": None
        }


def complete_mpesa_payment_handler(payment_id: str, force_success: bool = None) -> Dict[str, Any]:
    """
    Complete M-Pesa payment simulation (called after processing delay)
    This would typically be called by a background process or timer
    """
    try:
        payments = db.load_json('payments')
        payment_index = None
        payment = None
        
        # Find payment
        for i, p in enumerate(payments):
            if p.get('payment_id') == payment_id:
                payment_index = i
                payment = p
                break
        
        if not payment:
            return {
                "success": False,
                "message": "Payment not found",
                "error_type": "payment_not_found"
            }
        
        # Check if payment is in correct state
        if payment.get('status') not in ['pending', 'processing']:
            return {
                "success": False,
                "message": f"Payment already {payment.get('status')}",
                "error_type": "invalid_state"
            }
        
        # Determine outcome
        if force_success is None:
            success = MPesaSimulator.simulate_payment_outcome()
        else:
            success = force_success
        
        # Update payment record
        if success:
            # Successful payment
            transaction_id = MPesaSimulator.generate_transaction_id()
            payments[payment_index].update({
                "status": "completed",
                "transaction_id": transaction_id,
                "completed_at": datetime.now().isoformat()
            })
            
            # Update order status
            order_id = payment.get('order_id')
            order = db.get_order_by_id(order_id)
            if order:
                db.update_order_status(order_id, "confirmed")
                # Also update order payment fields
                orders = db.get_orders()
                for i, o in enumerate(orders):
                    if o.get('id') == order_id:
                        orders[i].update({
                            "payment_status": "completed",
                            "payment_id": payment_id,
                            "payment_completed_at": datetime.now().isoformat()
                        })
                        db.save_orders(orders)
                        break
            
            message = f"""🎉 **M-PESA PAYMENT SUCCESSFUL!**

✅ Transaction Completed
💰 Amount Paid: KSh {payment.get('amount', 0):,}
📱 M-Pesa Code: {transaction_id}
🕒 Time: {datetime.now().strftime('%d %b %Y, %H:%M')}
📄 Reference: {payment.get('order_id')}

📦 Your order is now CONFIRMED!
🚚 We'll contact you within 2 hours for delivery.

💾 Keep this M-Pesa code for your records"""

        else:
            # Failed payment
            payments[payment_index].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "failure_reason": random.choice([
                    "Transaction cancelled by user",
                    "Insufficient M-Pesa balance", 
                    "Network timeout",
                    "Wrong PIN entered multiple times"
                ])
            })
            
            message = f"""❌ **M-PESA PAYMENT FAILED**

🚫 Transaction was not completed
💡 Common reasons:
   • Wrong PIN entered
   • Insufficient M-Pesa balance  
   • Transaction cancelled
   • Network timeout

🔄 Try again? Type 'retry payment {payment.get('order_id')}'
💬 Need help? Type 'payment help'"""

        # Save updated payments
        db.save_json('payments', payments)
        
        return {
            "success": True,
            "message": message,
            "payment_success": success,
            "transaction_id": transaction_id if success else None,
            "data": payments[payment_index]
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error completing payment: {str(e)}",
            "error_type": "system_error"
        }


def cancel_payment_handler(payment_id: str) -> Dict[str, Any]:
    """
    Cancel a pending payment
    """
    try:
        payments = db.load_json('payments')
        payment_index = None
        payment = None
        
        # Find payment
        for i, p in enumerate(payments):
            if p.get('payment_id') == payment_id:
                payment_index = i
                payment = p
                break
        
        if not payment:
            return {
                "success": False,
                "message": f"❌ Payment {payment_id} not found",
                "error_type": "payment_not_found"
            }
        
        # Check if payment can be cancelled
        status = payment.get('status')
        if status not in ['pending', 'processing']:
            return {
                "success": False,
                "message": f"❌ Cannot cancel payment - status is {status}",
                "error_type": "cannot_cancel"
            }
        
        # Cancel payment
        payments[payment_index].update({
            "status": "cancelled",
            "completed_at": datetime.now().isoformat(),
            "failure_reason": "Cancelled by user"
        })
        
        # Save updated payments
        db.save_json('payments', payments)
        
        message = f"""❌ **Payment Cancelled**

💳 Payment ID: {payment_id}
📋 Order: {payment.get('order_id')}
💰 Amount: KSh {payment.get('amount', 0):,}

🔄 To pay for this order later:
Type 'pay for order {payment.get('order_id')}'"""

        return {
            "success": True,
            "message": message,
            "data": payments[payment_index]
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error cancelling payment: {str(e)}",
            "error_type": "system_error"
        }


def get_payment_help_handler() -> Dict[str, Any]:
    """
    Provide M-Pesa payment help and troubleshooting
    """
    message = """🆘 **M-Pesa Payment Help**

❓ **Common Issues:**

📱 **No STK Prompt?**
   • Dial *334# → Lipa na M-Pesa → Pay Bill
   • Business Number: 174379
   • Account: [Your Order ID]
   • Amount: [Order Amount]

🔐 **Wrong PIN?** 
   • Wait 5 minutes and retry
   • Ensure you have enough M-Pesa balance

⏱️ **Taking Too Long?**
   • Payment timeout is 60 seconds
   • Check network connection
   • Try again if it times out

💰 **Low Balance?**
   • Top up via *165# or M-Pesa agent
   • Minimum required: Order amount + KSh 1

📞 **Alternative Payment:**
   • Paybill: 174379
   • Account: [Your Order ID]
   • Send M-Pesa code after payment

🆘 **Still Need Help?**
   • WhatsApp: 0700123456
   • Email: support@sasabot.co.ke
   • Available: 8AM - 8PM daily

💡 **Tips for Success:**
   • Use phone number registered with order
   • Don't close M-Pesa app during payment
   • Ensure good network connection"""

    return {
        "success": True,
        "message": message,
        "data": {
            "help_type": "mpesa_payment",
            "support_contact": "0700123456"
        }
    }


def retry_payment_handler(order_id: str, customer_phone: str = None) -> Dict[str, Any]:
    """
    Retry payment for a failed/cancelled payment
    """
    try:
        # Check if there are any failed/cancelled payments for this order
        payments = db.load_json('payments')
        previous_payments = [p for p in payments if p.get('order_id') == order_id and p.get('status') in ['failed', 'cancelled', 'expired']]
        
        if previous_payments:
            # Get phone from previous payment if not provided
            if not customer_phone:
                customer_phone = previous_payments[-1].get('customer_phone')
        
        # Initiate new payment
        result = initiate_mpesa_payment_handler(order_id, customer_phone)
        
        if result["success"]:
            retry_count = len(previous_payments)
            result["message"] = f"🔄 **Payment Retry #{retry_count + 1}**\n\n" + result["message"]
            
            if retry_count > 0:
                result["message"] += f"\n\n💡 Previous attempts: {retry_count}"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error retrying payment: {str(e)}",
            "error_type": "system_error"
        }


# =============================================================================
# PAYMENT TOOLS REGISTRY
# =============================================================================

payment_tools = [
    {
        "name": "initiate_mpesa_payment",
        "description": "Start M-Pesa payment process for an order",
        "handler": initiate_mpesa_payment_handler,
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
        "description": "Check the current status of a payment",
        "handler": check_payment_status_handler,
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
        "handler": cancel_payment_handler,
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
        "description": "Get help and troubleshooting for M-Pesa payments",
        "handler": get_payment_help_handler,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "retry_payment",
        "description": "Retry payment for an order after previous failure",
        "handler": retry_payment_handler,
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
        "description": "Internal function to complete payment simulation (for demo purposes)",
        "handler": complete_mpesa_payment_handler,
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {
                    "type": "string",
                    "description": "Payment ID to complete"
                },
                "force_success": {
                    "type": "boolean",
                    "description": "Force success or failure (optional, defaults to random)"
                }
            },
            "required": ["payment_id"]
        }
    }
]