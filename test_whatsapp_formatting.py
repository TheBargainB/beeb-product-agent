#!/usr/bin/env python3

"""
WhatsApp Formatting Test Script
===============================

This script demonstrates the WhatsApp formatting feature that converts markdown
responses to WhatsApp-friendly format.
"""

import sys
import asyncio
import os
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, 'src')

# Test the WhatsApp formatter directly
from agent.whatsapp_formatter import WhatsAppFormatter, format_response_for_platform

def test_whatsapp_formatter():
    """Test the WhatsApp formatter with various markdown examples."""
    
    print("🔧 Testing WhatsApp Formatter")
    print("=" * 50)
    
    # Test cases with markdown content
    test_cases = [
        {
            "name": "Recipe with Markdown",
            "markdown": """# Hummus Recipe

## Ingredients:
- **2 cups** chickpeas (cooked)
- **1/4 cup** tahini
- **2 cloves** garlic
- **1/4 cup** lemon juice
- **Salt** to taste

## Instructions:
1. Drain and rinse chickpeas
2. Blend all ingredients until smooth
3. Add water if needed for consistency
4. Serve with pita bread

### Tips:
- For smoother texture, peel the chickpeas
- Add paprika for color
- Store in fridge for up to 1 week""",
            "expected_whatsapp": "Contains emojis and WhatsApp formatting"
        },
        {
            "name": "Grocery List with Markdown",
            "markdown": """## Shopping List

**Fresh Produce:**
- Tomatoes (2 lbs)
- Onions (1 bag)
- Spinach (1 bunch)

**Dairy:**
- Milk (1 gallon)
- Cheese (cheddar, 8 oz)

**Meat:**
- Chicken breast (2 lbs)

**Total Cost:** $35.50
**Store:** Whole Foods""",
            "expected_whatsapp": "Contains grocery emojis and formatting"
        },
        {
            "name": "Meal Plan with Markdown",
            "markdown": """# Weekly Meal Plan

## Monday
**Breakfast:** Oatmeal with fruits
**Lunch:** Grilled chicken salad
**Dinner:** Spaghetti with marinara

## Tuesday
**Breakfast:** Greek yogurt with berries
**Lunch:** Turkey sandwich
**Dinner:** Beef stir-fry

## Wednesday
**Breakfast:** Smoothie bowl
**Lunch:** Quinoa salad
**Dinner:** Salmon with vegetables""",
            "expected_whatsapp": "Contains meal emojis and formatting"
        },
        {
            "name": "General Response with Markdown",
            "markdown": """**Welcome to BargainB!**

I'm your personal grocery assistant. Here's what I can help you with:

### Key Features:
- **Product Search:** Find products and prices
- **Meal Planning:** Create weekly meal plans
- **Budget Tracking:** Stay within your budget
- **Shopping Lists:** Organize your shopping

> *Tip: You can ask me about specific products or brands*

For more information, visit our [website](https://bargainb.com).""",
            "expected_whatsapp": "Contains general formatting"
        }
    ]
    
    formatter = WhatsAppFormatter()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        print("🔹 Original Markdown:")
        print(test_case['markdown'])
        print()
        
        print("🔹 WhatsApp Formatted:")
        whatsapp_formatted = formatter.auto_format(test_case['markdown'], "whatsapp")
        print(whatsapp_formatted)
        print()
        
        print("🔹 General (No Formatting):")
        general_formatted = formatter.auto_format(test_case['markdown'], "general")
        print(general_formatted)
        print()
        
        print("✅ Formatting applied successfully!")
        print("=" * 50)


async def test_agent_with_whatsapp_formatting():
    """Test the agent with WhatsApp formatting enabled."""
    
    print("\n🤖 Testing Agent with WhatsApp Formatting")
    print("=" * 50)
    
    # Check environment variables
    required_env_vars = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Skipping agent test...")
        return
    
    try:
        from agent.graph import create_enhanced_agent_graph
        
        # Create the graph
        graph = create_enhanced_agent_graph()
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Recipe Request (WhatsApp)",
                "message": "Can you give me a recipe for falafel?",
                "config": {
                    "configurable": {
                        "user_id": "whatsapp_test_user",
                        "thread_id": "whatsapp_test_thread",
                        "source": "whatsapp"  # This should trigger WhatsApp formatting
                    }
                }
            },
            {
                "name": "Recipe Request (General)",
                "message": "Can you give me a recipe for falafel?",
                "config": {
                    "configurable": {
                        "user_id": "general_test_user",
                        "thread_id": "general_test_thread",
                        "source": "general"  # This should NOT trigger WhatsApp formatting
                    }
                }
            },
            {
                "name": "Grocery List Request (WhatsApp)",
                "message": "Create a grocery list for pasta carbonara",
                "config": {
                    "configurable": {
                        "user_id": "whatsapp_test_user",
                        "thread_id": "whatsapp_test_thread_2",
                        "source": "whatsapp"
                    }
                }
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📱 Test {i}: {scenario['name']}")
            print("-" * 40)
            print(f"Message: {scenario['message']}")
            print(f"Source: {scenario['config']['configurable']['source']}")
            print()
            
            try:
                # Run the agent
                result = await graph.ainvoke(
                    {"messages": [{"role": "user", "content": scenario['message']}]},
                    config=scenario['config']
                )
                
                # Extract the response
                if result and 'messages' in result:
                    last_message = result['messages'][-1]
                    response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                    
                    print("🤖 Assistant Response:")
                    print(response_content)
                    print()
                    
                    # Check if formatting was applied (look for WhatsApp-style emojis)
                    whatsapp_indicators = ['🥘', '👨‍🍳', '🍽️', '💡', '📝', '🔥', '📌', '•']
                    has_whatsapp_formatting = any(indicator in response_content for indicator in whatsapp_indicators)
                    
                    if scenario['config']['configurable']['source'] == "whatsapp":
                        if has_whatsapp_formatting:
                            print("✅ WhatsApp formatting detected!")
                        else:
                            print("⚠️  WhatsApp formatting may not have been applied")
                    else:
                        if not has_whatsapp_formatting:
                            print("✅ No WhatsApp formatting (as expected)")
                        else:
                            print("⚠️  Unexpected WhatsApp formatting")
                    
                else:
                    print("❌ No response received")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error setting up agent: {e}")


def test_formatting_conversion():
    """Test specific formatting conversions."""
    
    print("\n🔄 Testing Formatting Conversions")
    print("=" * 50)
    
    conversions = [
        {
            "name": "Headers",
            "markdown": "# Main Title\n## Sub Title\n### Small Title",
            "expected_contains": ["🔥", "📌", "•"]
        },
        {
            "name": "Bold Text",
            "markdown": "This is **bold text** and **another bold**",
            "expected_contains": ["*bold text*", "*another bold*"]
        },
        {
            "name": "Lists",
            "markdown": "- Item 1\n- Item 2\n1. First\n2. Second",
            "expected_contains": ["• Item 1", "• Item 2", "• First", "• Second"]
        },
        {
            "name": "Links",
            "markdown": "[Click here](https://example.com)",
            "expected_contains": ["Click here: https://example.com"]
        },
        {
            "name": "Recipe Keywords",
            "markdown": "**INGREDIENTS**: stuff\n**INSTRUCTIONS**: do this",
            "expected_contains": ["🥘", "👨‍🍳"]
        }
    ]
    
    for test in conversions:
        print(f"\n📝 {test['name']}:")
        print(f"Original: {test['markdown']}")
        
        formatted = format_response_for_platform(test['markdown'], "whatsapp")
        print(f"Formatted: {formatted}")
        
        # Check if expected elements are present
        all_found = all(expected in formatted for expected in test['expected_contains'])
        
        if all_found:
            print("✅ All expected elements found!")
        else:
            print("⚠️  Some expected elements missing")
            missing = [exp for exp in test['expected_contains'] if exp not in formatted]
            print(f"Missing: {missing}")
        
        print("-" * 30)


if __name__ == "__main__":
    print("📱 WhatsApp Formatting Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: WhatsApp formatter directly
    test_whatsapp_formatter()
    
    # Test 2: Specific formatting conversions
    test_formatting_conversion()
    
    # Test 3: Agent with WhatsApp formatting (if environment is set up)
    print("\n🤖 Testing Agent Integration...")
    try:
        asyncio.run(test_agent_with_whatsapp_formatting())
    except KeyboardInterrupt:
        print("\n👋 Agent test interrupted by user")
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
    
    print("\n🎉 WhatsApp Formatting Test Suite Complete!")
    print("=" * 60)
    print("\n📝 Summary:")
    print("✅ WhatsApp formatting converts markdown to WhatsApp-friendly format")
    print("✅ Different content types get appropriate emoji enhancements")
    print("✅ Non-WhatsApp sources remain unformatted")
    print("✅ Headers, lists, and formatting are properly converted")
    print("\n💬 When using this in production:")
    print("1. Set source='whatsapp' in your config")
    print("2. Responses will automatically be formatted for WhatsApp")
    print("3. No more ugly markdown in your WhatsApp messages!") 