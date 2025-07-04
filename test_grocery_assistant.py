#!/usr/bin/env python3
"""
Test script for the Personal Grocery Assistant with customer configuration.

This script demonstrates how to use the grocery assistant with customer preferences
loaded from the database at runtime.
"""

import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, 'src')

from agent.graph import create_enhanced_agent_graph
from agent.config import get_config


async def test_grocery_assistant():
    """Test the grocery assistant with customer configuration"""
    
    print("🛒 Testing Personal Grocery Assistant")
    print("=" * 50)
    
    # Get the agent graph
    graph = create_enhanced_agent_graph()
    
    # Customer configuration - this is how you'd configure it from your admin panel
    customer_config = {
        "configurable": {
            "customer_profile_id": "4c432d3e-0a15-4272-beda-0d327088d5f6",  # Sarah Johnson
            "user_id": "sarah_test_session",
            "thread_id": "grocery_session_001"
        }
    }
    
    print("👤 Customer Configuration:")
    print(f"   Profile ID: {customer_config['configurable']['customer_profile_id']}")
    print(f"   User ID: {customer_config['configurable']['user_id']}")
    print()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Check Customer Profile Loading",
            "message": "Hi! I'm looking for some healthy breakfast options. What do you recommend?",
            "expected": "Should load Sarah's profile (gluten-free, lactose-intolerant, health-focused)"
        },
        {
            "name": "Dietary Restriction Awareness",
            "message": "I want to make pancakes for breakfast. Can you suggest ingredients?",
            "expected": "Should recommend gluten-free flour and lactose-free milk"
        },
        {
            "name": "Store Preference Recognition",
            "message": "Where should I shop for organic vegetables?",
            "expected": "Should recommend Albert Heijn or Jumbo (Sarah's preferred stores)"
        },
        {
            "name": "Budget Awareness",
            "message": "I need to plan my weekly grocery shopping with a budget of €100",
            "expected": "Should respect the €80-120 budget range from profile"
        },
        {
            "name": "Shopping Persona Application",
            "message": "What snacks would you recommend for me?",
            "expected": "Should suggest healthy options (healthHero persona)"
        }
    ]
    
    print("🧪 Running Test Scenarios:")
    print()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}: {scenario['name']}")
        print(f"Message: {scenario['message']}")
        print(f"Expected: {scenario['expected']}")
        print("-" * 40)
        
        try:
            # Run the assistant
            result = await graph.ainvoke(
                {"messages": [{"role": "user", "content": scenario['message']}]},
                config=customer_config
            )
            
            # Extract the response
            if result and 'messages' in result:
                last_message = result['messages'][-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                
                print("🤖 Assistant Response:")
                print(f"   {response_content[:200]}...")
                print()
                
            else:
                print("❌ No response received")
                print()
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
    
    print("✅ Test completed!")


def test_customer_profile_loading():
    """Test loading customer profiles from the database"""
    
    print("📊 Testing Customer Profile Loading")
    print("=" * 50)
    
    from agent.supabase_client import SupabaseClient
    from agent.memory_tools import SupabaseMemoryManager
    from langchain_openai import ChatOpenAI
    
    # Initialize components
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    supabase_client = SupabaseClient()
    
    # Test with customer profile ID
    customer_profile_id = "4c432d3e-0a15-4272-beda-0d327088d5f6"
    memory_manager = SupabaseMemoryManager(model, supabase_client, customer_profile_id)
    
    print(f"👤 Loading profile for: {customer_profile_id}")
    print()
    
    # Test profile loading
    profile = memory_manager.get_user_profile()
    if profile:
        print("✅ Profile loaded successfully:")
        print(f"   Name: {profile.get('preferred_name', 'N/A')}")
        print(f"   Stores: {', '.join(profile.get('preferred_stores', []))}")
        print(f"   Dietary: {', '.join(profile.get('dietary_restrictions', []))}")
        print(f"   Persona: {profile.get('shopping_persona', 'N/A')}")
        print(f"   Budget: {profile.get('budget_range', 'N/A')}")
        print()
    else:
        print("❌ Failed to load profile")
        print()
    
    # Test grocery assistant context
    print("🛒 Grocery Assistant Context:")
    print("-" * 30)
    context = memory_manager.get_grocery_assistant_context()
    print(context)
    print()
    
    # Test formatted user context
    print("📝 Full User Context:")
    print("-" * 30)
    full_context = memory_manager.format_user_context()
    print(full_context)
    print()


def demonstrate_multi_customer_usage():
    """Demonstrate how the same codebase serves multiple customers"""
    
    print("🏢 Multi-Customer Usage Demonstration")
    print("=" * 50)
    
    # Example of how different customers would be configured
    customers = [
        {
            "name": "Sarah Johnson",
            "profile_id": "4c432d3e-0a15-4272-beda-0d327088d5f6",
            "description": "Health-focused, gluten-free, shops at Albert Heijn"
        },
        {
            "name": "Budget-Conscious Customer",
            "profile_id": "example-uuid-2",
            "description": "Price-sensitive, family shopping, prefers deals"
        },
        {
            "name": "Eco-Friendly Customer", 
            "profile_id": "example-uuid-3",
            "description": "Environmentally conscious, organic foods only"
        }
    ]
    
    print("💡 Runtime Configuration Examples:")
    print()
    
    for customer in customers:
        print(f"Customer: {customer['name']}")
        print(f"Profile: {customer['description']}")
        
        config_example = {
            "configurable": {
                "customer_profile_id": customer["profile_id"],
                "user_id": f"user_{customer['name'].lower().replace(' ', '_')}",
                "thread_id": f"session_{customer['profile_id'][:8]}"
            }
        }
        
        print("Configuration:")
        print(json.dumps(config_example, indent=2))
        print()
    
    print("🔑 Key Benefits:")
    print("• Single codebase serves multiple customers")
    print("• Personalized responses based on customer profile")
    print("• Runtime configuration from admin panel")
    print("• No customer data hardcoded in application")
    print("• Scalable architecture for many customers")
    print()


if __name__ == "__main__":
    print("🛒 Personal Grocery Assistant - Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Customer profile loading
    test_customer_profile_loading()
    
    # Test 2: Multi-customer demonstration
    demonstrate_multi_customer_usage()
    
    # Test 3: Interactive assistant (async)
    print("🤖 Running Interactive Assistant Test...")
    print("Note: This requires OpenAI API key to be set")
    print()
    
    try:
        asyncio.run(test_grocery_assistant())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure all environment variables are set:")
        print("- OPENAI_API_KEY")
        print("- SUPABASE_URL") 
        print("- SUPABASE_ANON_KEY") 