#!/usr/bin/env python3
"""Test enhanced WhatsApp formatting instructions."""

import asyncio
from langchain_core.messages import HumanMessage
from src.agent.graph import create_graph
from src.agent.nodes import get_platform_formatting_instructions


def test_formatting_instructions():
    """Test the WhatsApp formatting instructions content."""
    print("🧪 Testing WhatsApp formatting instructions...")
    print("=" * 50)
    
    # Get WhatsApp formatting instructions
    whatsapp_instructions = get_platform_formatting_instructions("whatsapp")
    print("📱 WhatsApp Formatting Instructions:")
    print(whatsapp_instructions)
    print("=" * 50)
    
    # Check for key components
    critical_elements = [
        "CRITICAL WHATSAPP FORMATTING",
        "ABSOLUTELY FORBIDDEN",
        "## Headers",
        "**Double asterisk bold**",
        "REQUIRED WHATSAPP FORMAT",
        "*single asterisk bold*",
        "• bullet points",
        "EXACT EXAMPLES",
        "MANDATORY - NO EXCEPTIONS"
    ]
    
    found_elements = []
    for element in critical_elements:
        if element in whatsapp_instructions:
            found_elements.append(element)
    
    print(f"✅ Found {len(found_elements)}/{len(critical_elements)} critical elements")
    
    if len(found_elements) == len(critical_elements):
        print("🎉 SUCCESS: All critical formatting elements present!")
    else:
        missing = [e for e in critical_elements if e not in found_elements]
        print(f"⚠️  Missing elements: {missing}")
    
    return len(found_elements) == len(critical_elements)


async def test_whatsapp_formatting():
    """Test that WhatsApp formatting instructions are properly enforced."""
    
    # First test the formatting instructions
    instructions_ok = test_formatting_instructions()
    if not instructions_ok:
        print("❌ Formatting instructions test failed, skipping graph test")
        return
    
    # Create the graph
    graph = create_graph()
    
    # Configuration with WhatsApp source
    config = {
        "configurable": {
            "source": "whatsapp",
            "customer_name": "Test Customer",
            "instance_name": "Grocery Assistant",
            "user_id": "test_user_123",
            "max_response_length": 1000,
            "primary_language": "english",
            "language_enforcement": "flexible",
            "fallback_language": "english",
            "thread_id": "test_thread_123"
        }
    }
    
    # Test message that should trigger formatting
    message = HumanMessage(
        content="Can you give me a recipe for pasta with tomato sauce? Include ingredients and instructions."
    )
    
    # Create initial state
    initial_state = {
        "messages": [message],
        "tool_calls": [],
        "last_response": "",
        "conversation_complete": False
    }
    
    print("🧪 Testing WhatsApp formatting with recipe request...")
    print("=" * 50)
    
    # Run the graph
    try:
        result = await graph.ainvoke(initial_state, config)
        
        # Get the final response
        final_response = result["messages"][-1].content if result["messages"] else result.get("last_response", "")
        
        print("📱 WhatsApp Response:")
        print(final_response)
        print("=" * 50)
        
        # Check for forbidden markdown patterns
        forbidden_patterns = [
            "## ",
            "### ",
            "**",
            "__",
            "`",
            "[",
            "]",
            "---"
        ]
        
        required_patterns = [
            "🍝",  # Recipe emoji
            "🥘",  # Ingredients emoji
            "👨‍🍳",  # Instructions emoji
            "•",   # Bullet points
            "*"    # Single asterisk bold
        ]
        
        print("🔍 Formatting Analysis:")
        print("-" * 30)
        
        # Check for forbidden patterns
        violations = []
        for pattern in forbidden_patterns:
            if pattern in final_response:
                violations.append(pattern)
        
        if violations:
            print(f"❌ FORMATTING VIOLATIONS FOUND: {violations}")
            print("   The response contains forbidden markdown!")
        else:
            print("✅ No forbidden markdown patterns detected")
        
        # Check for required patterns
        found_patterns = []
        for pattern in required_patterns:
            if pattern in final_response:
                found_patterns.append(pattern)
        
        print(f"✅ Required WhatsApp patterns found: {found_patterns}")
        
        # Overall assessment
        if not violations and len(found_patterns) >= 3:
            print("🎉 SUCCESS: WhatsApp formatting looks good!")
        else:
            print("⚠️  WARNING: Formatting needs improvement")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_whatsapp_formatting()) 