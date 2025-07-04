#!/usr/bin/env python3
"""
Simple test to verify the prompt-based WhatsApp formatting approach works correctly.
"""

import os
import sys
sys.path.append('src')

from src.agent.nodes import generate_answer, get_platform_formatting_instructions
from src.agent.memory_tools import ConversationState
from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

def test_whatsapp_formatting():
    """Test that WhatsApp formatting is handled correctly through prompts."""
    
    # Test the platform formatting instructions
    whatsapp_instructions = get_platform_formatting_instructions("whatsapp")
    print("📱 WhatsApp formatting instructions:")
    print(whatsapp_instructions)
    print("\n" + "="*50 + "\n")
    
    # Test with a recipe request
    config = RunnableConfig({
        "configurable": {
            "user_id": "test-user",
            "customer_name": "Test Customer",
            "instance_name": "Recipe Assistant",
            "source": "whatsapp",  # This should trigger WhatsApp formatting
            "max_response_length": 1000
        }
    })
    
    state = ConversationState({
        "messages": [HumanMessage(content="Can you give me a simple hummus recipe?")],
        "tool_calls": [],
        "last_response": "",
        "conversation_complete": False
    })
    
    print("🧪 Testing WhatsApp recipe response...")
    try:
        result = generate_answer(state, config)
        response = result["last_response"]
        print("Response:")
        print(response)
        print("\n" + "="*50 + "\n")
        
        # Check if the response follows WhatsApp formatting rules
        issues = []
        if "**" in response:
            issues.append("❌ Found **bold** markdown (should be *bold*)")
        if "# " in response:
            issues.append("❌ Found # headers (should use 🔥 emoji)")
        if "## " in response:
            issues.append("❌ Found ## subheaders (should use 📌 emoji)")
        if "- " in response and "• " not in response:
            issues.append("❌ Found - bullets (should use • bullets)")
        
        if issues:
            print("🚨 WhatsApp formatting issues found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("✅ WhatsApp formatting looks good!")
            
    except Exception as e:
        print(f"❌ Error testing WhatsApp formatting: {e}")

def test_general_formatting():
    """Test that general formatting allows markdown."""
    
    # Test with general source (should allow markdown)
    config = RunnableConfig({
        "configurable": {
            "user_id": "test-user",
            "customer_name": "Test Customer",
            "instance_name": "Recipe Assistant",
            "source": "general",  # This should allow markdown
            "max_response_length": 1000
        }
    })
    
    state = ConversationState({
        "messages": [HumanMessage(content="Can you give me a simple hummus recipe?")],
        "tool_calls": [],
        "last_response": "",
        "conversation_complete": False
    })
    
    print("🧪 Testing general formatting (markdown allowed)...")
    try:
        result = generate_answer(state, config)
        response = result["last_response"]
        print("Response:")
        print(response)
        print("\n" + "="*50 + "\n")
        
        # For general formatting, markdown is fine
        print("✅ General formatting allows markdown - no restrictions")
        
    except Exception as e:
        print(f"❌ Error testing general formatting: {e}")

if __name__ == "__main__":
    print("🎯 Testing Simplified WhatsApp Formatting (Prompt-Based Approach)")
    print("=" * 70)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test platform formatting instructions
    test_whatsapp_formatting()
    test_general_formatting()
    
    print("\n🎉 Testing complete!")
    print("\n💡 Key Benefits of This Approach:")
    print("  • ✅ Simpler codebase - no complex post-processing")
    print("  • ✅ AI understands context better")
    print("  • ✅ Fewer moving parts to maintain")
    print("  • ✅ More flexible and intelligent formatting")
    print("  • ✅ Reduced performance overhead") 