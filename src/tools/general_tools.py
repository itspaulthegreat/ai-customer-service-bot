# src/tools/general_tools.py
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

class GeneralTools:
    """Tools for general customer service tasks"""
    
    def __init__(self):
        self.store_info = {
            "name": "Fashion Store",
            "hours": "Mon-Fri: 9AM-8PM, Sat-Sun: 10AM-6PM",
            "support_email": "support@fashionstore.com",
            "phone": "1-800-FASHION",
            "return_policy": "30 days with tags and receipt",
            "shipping_policy": "Free shipping on orders over $50",
            "size_guide": "Available on each product page"
        }
    
    async def handle_greeting(self, greeting_type: str = "general", **kwargs) -> Dict[str, Any]:
        """Handle various types of greetings"""
        greetings = {
            "general": "Hi there! 👋 I'm Sarah, your personal shopping assistant. I'm here to help you find amazing products, check on your orders, or answer any questions about our store. What can I help you with today?",
            "welcome": "Welcome to our store! 🛍️ I'm excited to help you discover our latest fashion finds. Whether you're looking for something specific or just browsing, I'm here to make your shopping experience great!",
            "return": "Welcome back! 😊 It's great to see you again. How can I assist you today?",
            "late": "Good evening! Even though it's late, I'm here and ready to help with whatever you need. What can I do for you?"
        }
        
        response = greetings.get(greeting_type, greetings["general"])
        
        return {
            "success": True,
            "type": "greeting",
            "response": response,
            "suggested_actions": [
                "Show me new arrivals",
                "Check my order status", 
                "Browse men's clothing",
                "Browse women's clothing"
            ]
        }
    
    async def provide_store_info(self, info_type: str = "general", **kwargs) -> Dict[str, Any]:
        """Provide store information"""
        try:
            if info_type == "hours":
                return {
                    "success": True,
                    "type": "store_hours",
                    "info": self.store_info["hours"],
                    "message": f"Our store hours are: {self.store_info['hours']}"
                }
            elif info_type == "contact":
                return {
                    "success": True,
                    "type": "contact_info",
                    "info": {
                        "email": self.store_info["support_email"],
                        "phone": self.store_info["phone"]
                    },
                    "message": f"You can reach us at {self.store_info['support_email']} or call {self.store_info['phone']}"
                }
            elif info_type == "shipping":
                return {
                    "success": True,
                    "type": "shipping_policy",
                    "info": self.store_info["shipping_policy"],
                    "message": f"📦 Shipping info: {self.store_info['shipping_policy']}. Most orders arrive within 3-5 business days!"
                }
            elif info_type == "returns":
                return {
                    "success": True,
                    "type": "return_policy",
                    "info": self.store_info["return_policy"],
                    "message": f"🔄 Return policy: {self.store_info['return_policy']}. We make returns easy and hassle-free!"
                }
            else:
                return {
                    "success": True,
                    "type": "general_info",
                    "info": self.store_info,
                    "message": "Here's everything you need to know about our store! What specific information were you looking for?"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get store info: {str(e)}",
                "type": "info_error"
            }
    
    async def handle_complaint(self, complaint_type: str = "general", severity: str = "medium", **kwargs) -> Dict[str, Any]:
        """Handle customer complaints with empathy"""
        try:
            responses = {
                "delivery": "I'm really sorry to hear about the delivery issue! 😔 I know how frustrating that must be when you're expecting your order. Let me help you track down exactly what happened and get this resolved right away.",
                "product": "I sincerely apologize that the product didn't meet your expectations! That's definitely not the experience we want for you. Let's work together to make this right - whether that's an exchange, return, or finding something that's a better fit.",
                "service": "I'm truly sorry about your service experience. Your feedback is incredibly valuable to us, and I want to make sure we address this properly. Let me personally ensure you get the help you deserve.",
                "website": "I apologize for any trouble with our website! I know how annoying technical issues can be when you're trying to shop. Let me help you with whatever you were trying to do, and I'll make sure our tech team knows about this issue.",
                "general": "I'm really sorry you've had a frustrating experience! That's not at all what we want for our customers. Let me do everything I can to help resolve this and make things right for you."
            }
            
            base_response = responses.get(complaint_type, responses["general"])
            
            if severity == "high":
                base_response += " I'm treating this as a priority and will personally follow up to ensure you're completely satisfied."
            
            return {
                "success": True,
                "type": "complaint_handled",
                "complaint_type": complaint_type,
                "severity": severity,
                "response": base_response,
                "next_steps": [
                    "Let me gather some details to help resolve this",
                    "I'll make sure this gets the attention it deserves",
                    "Is there anything specific I can do right now to help?"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to handle complaint: {str(e)}",
                "type": "complaint_error"
            }
    
    async def provide_help(self, help_topic: str = "general", **kwargs) -> Dict[str, Any]:
        """Provide contextual help"""
        try:
            help_responses = {
                "sizing": "👗 Need help with sizing? I'd recommend checking our size guide on each product page - it's super detailed! You can also read customer reviews for fit insights. If you're between sizes, many customers find our size chat helpful, or I can help you find similar items with better size info.",
                "account": "👤 Having account issues? I can help with password resets, order history, or updating your info. What specifically do you need help with regarding your account?",
                "payment": "💳 For payment questions, I can help explain our accepted payment methods, security measures, or troubleshoot checkout issues. What payment question can I help with?",
                "navigation": "🧭 Need help finding something on our site? I'm like your personal shopping GPS! Tell me what you're looking for and I'll guide you right to it, or I can search our products for you right here in chat.",
                "general": "🤗 I'm here to help with anything you need! Whether it's finding products, checking orders, understanding policies, or just chatting about fashion - what can I do for you today?"
            }
            
            response = help_responses.get(help_topic, help_responses["general"])
            
            return {
                "success": True,
                "type": "help_provided",
                "help_topic": help_topic,
                "response": response,
                "additional_resources": [
                    "Browse our FAQ section",
                    "Contact customer service directly",
                    "Check our size guide",
                    "Read customer reviews"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to provide help: {str(e)}",
                "type": "help_error"
            }
    
    async def handle_chitchat(self, message: str, **kwargs) -> Dict[str, Any]:
        """Handle casual conversation and weird/random messages"""
        try:
            message_lower = message.lower()
            
            # Detect different types of casual conversation
            if any(word in message_lower for word in ["weather", "how are you", "what's up", "sup"]):
                response = "I'm doing great, thanks for asking! 😊 I'm having a wonderful time helping customers find amazing fashion pieces today. Speaking of which, is there anything style-related I can help you discover?"
                
            elif any(word in message_lower for word in ["funny", "joke", "haha", "lol"]):
                response = "Haha, I love a good laugh! 😄 You know what's funny? How good our new arrivals look - they're seriously stylish! Want to see some pieces that might make you smile?"
                
            elif any(word in message_lower for word in ["weird", "random", "strange", "what", "huh"]):
                response = "I know I might seem a bit enthusiastic about fashion, but that's just because I genuinely love helping people find things they'll look amazing in! 😊 Is there something specific you're shopping for, or would you like me to show you what's trending?"
                
            elif any(word in message_lower for word in ["test", "testing", "hello test"]):
                response = "Test successful! 🧪 I'm working perfectly and ready to help you with all your fashion needs. What would you like to explore first?"
                
            elif len(message.split()) <= 2 and message_lower in ["hi", "hey", "hello", "yo", "sup"]:
                response = "Hey there! 👋 I'm Sarah, your fashion assistant! I'm super excited to help you find something amazing today. What kind of style are you in the mood for?"
                
            else:
                # For truly random/weird messages, respond naturally but redirect
                response = "You know, I love how unique every conversation is! 😊 Everyone has their own style - including how they chat! Since I'm your fashion-focused assistant, I'm wondering... are you looking for something specific today, or would you like me to show you what's new and exciting in our store?"
            
            return {
                "success": True,
                "type": "chitchat",
                "response": response,
                "conversation_type": "casual",
                "redirect_to_shopping": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to handle conversation: {str(e)}",
                "type": "chitchat_error"
            }
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run diagnostics on general tools"""
        try:
            # Test basic functionality
            test_greeting = await self.handle_greeting()
            test_help = await self.provide_help()
            
            return {
                "healthy": True,
                "test_greeting": test_greeting.get("success", False),
                "test_help": test_help.get("success", False),
                "store_info_loaded": bool(self.store_info),
                "available_methods": [
                    "handle_greeting",
                    "provide_store_info",
                    "handle_complaint", 
                    "provide_help",
                    "handle_chitchat"
                ]
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def is_healthy(self) -> bool:
        """Check if general tools are healthy"""
        return hasattr(self, 'store_info') and bool(self.store_info)