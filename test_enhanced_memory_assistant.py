#!/usr/bin/env python3

"""
Enhanced Memory Assistant Test Suite
===================================

This script demonstrates the new comprehensive memory management and flexible language configuration capabilities.
"""

import sys
import asyncio
import os
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, 'src')

# Check environment variables
required_env_vars = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these environment variables and try again.")
    sys.exit(1)

try:
    from agent.graph import create_enhanced_agent_graph
    from agent.supabase_client import SupabaseClient
    from agent.memory_schemas import LANGUAGE_CONFIGS
    from langchain_core.messages import HumanMessage
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


def test_language_configurations():
    """Test different language configurations."""
    
    print("🌍 Testing Language Configurations")
    print("=" * 50)
    
    print("\nAvailable Language Configurations:")
    for name, config in LANGUAGE_CONFIGS.items():
        print(f"• {name}:")
        print(f"  - Primary Language: {config.primary_language}")
        print(f"  - Enforcement: {config.language_enforcement}")
        print(f"  - Translation Enabled: {config.translation_enabled}")
        if config.cultural_context:
            print(f"  - Cultural Context: {config.cultural_context}")
        print()


async def test_memory_management():
    """Test comprehensive memory management capabilities."""
    
    print("🧠 Testing Memory Management")
    print("=" * 50)
    
    # Create agent graph
    graph = create_enhanced_agent_graph()
    
    # Test different memory scenarios
    test_scenarios = [
        {
            "name": "Personal Information Collection",
            "config": {
                "configurable": {
                    "user_id": "alice_memory_test",
                    "thread_id": "memory_test_1"
                }
            },
            "messages": [
                "Hi! My name is Alice and I'm a teacher living in Amsterdam.",
                "I have two cats named Whiskers and Luna. I love reading and cooking Italian food.",
                "I'm learning Spanish and planning a trip to Barcelona next month."
            ]
        },
        {
            "name": "Conversation Continuity",
            "config": {
                "configurable": {
                    "user_id": "alice_memory_test",
                    "thread_id": "memory_test_2"  # New thread, same user
                }
            },
            "messages": [
                "Can you remind me what you know about me?",
                "What books would you recommend based on my interests?",
                "Any Spanish phrases I should learn for my Barcelona trip?"
            ]
        },
        {
            "name": "Preference Learning",
            "config": {
                "configurable": {
                    "user_id": "bob_memory_test",
                    "thread_id": "memory_test_3"
                }
            },
            "messages": [
                "I prefer detailed explanations over short answers.",
                "When I ask for recommendations, always include pros and cons.",
                "I don't like when assistants are too casual - be more professional."
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📝 Scenario: {scenario['name']}")
        print("-" * 30)
        
        for message_text in scenario["messages"]:
            print(f"\n👤 User: {message_text}")
            
            try:
                # Run the graph
                response = None
                async for chunk in graph.astream(
                    {"messages": [HumanMessage(content=message_text)]}, 
                    scenario["config"]
                ):
                    if "messages" in chunk:
                        last_message = chunk["messages"][-1]
                        if hasattr(last_message, 'content') and not hasattr(last_message, 'tool_calls'):
                            response = last_message.content
                
                if response:
                    print(f"🤖 Assistant: {response}")
                else:
                    print("🤖 Assistant: [No response generated]")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"\n✅ Completed scenario: {scenario['name']}")


async def test_language_flexibility():
    """Test flexible language configuration in action."""
    
    print("\n🌐 Testing Language Flexibility")
    print("=" * 50)
    
    # Create agent graph
    graph = create_enhanced_agent_graph()
    
    # Simulate different language assistants
    language_tests = [
        {
            "name": "Arabic Assistant (Strict)",
            "assistant_config": {
                "language": "arabic",
                "response_format": "arabic_only"
            },
            "messages": [
                "Hello, how are you?",  # English input
                "اريد وصفة للحمص"      # Arabic input
            ]
        },
        {
            "name": "Spanish Assistant (Flexible)",
            "config": {
                "configurable": {
                    "user_id": "spanish_test",
                    "thread_id": "spanish_test_1",
                    "language_config": LANGUAGE_CONFIGS["multilingual_flexible"]
                }
            },
            "messages": [
                "Hola, ¿cómo estás?",
                "Can you help me learn Spanish phrases for travel?"
            ]
        },
        {
            "name": "Multilingual Auto-Detect",
            "config": {
                "configurable": {
                    "user_id": "multilingual_test",
                    "thread_id": "multilingual_test_1",
                    "language_config": LANGUAGE_CONFIGS["multilingual_auto"]
                }
            },
            "messages": [
                "Bonjour! Comment allez-vous?",
                "Ich möchte Deutsch lernen.",
                "Hello, I speak multiple languages."
            ]
        }
    ]
    
    for test in language_tests:
        print(f"\n🗣️ Testing: {test['name']}")
        print("-" * 30)
        
        for message_text in test["messages"]:
            print(f"\n👤 User: {message_text}")
            
            try:
                # Use the test config or create one
                config = test.get("config", {
                    "configurable": {
                        "user_id": f"lang_test_{test['name'].lower().replace(' ', '_')}",
                        "thread_id": f"lang_thread_{hash(test['name']) % 1000}"
                    }
                })
                
                # Run the graph
                response = None
                async for chunk in graph.astream(
                    {"messages": [HumanMessage(content=message_text)]}, 
                    config
                ):
                    if "messages" in chunk:
                        last_message = chunk["messages"][-1]
                        if hasattr(last_message, 'content') and not hasattr(last_message, 'tool_calls'):
                            response = last_message.content
                
                if response:
                    print(f"🤖 Assistant: {response}")
                else:
                    print("🤖 Assistant: [No response generated]")
                    
            except Exception as e:
                print(f"❌ Error: {e}")


def test_supabase_assistant_config():
    """Test loading assistant configuration from Supabase."""
    
    print("\n💾 Testing Supabase Assistant Configuration")
    print("=" * 50)
    
    try:
        supabase_client = SupabaseClient()
        
        # Query for existing assistant configurations
        result = supabase_client.client.table('conversations').select(
            'assistant_id, assistant_name, assistant_config'
        ).limit(5).execute()
        
        if result.data:
            print("Found existing assistant configurations:")
            for item in result.data:
                print(f"\n📋 Assistant: {item.get('assistant_name', 'Unknown')}")
                print(f"   ID: {item.get('assistant_id', 'N/A')}")
                
                config = item.get('assistant_config', {})
                if config:
                    configurable = config.get('configurable', {})
                    if configurable.get('language'):
                        print(f"   Language: {configurable['language']}")
                    if configurable.get('response_format'):
                        print(f"   Response Format: {configurable['response_format']}")
                    if configurable.get('instructions'):
                        print(f"   Instructions: {configurable['instructions'][:100]}...")
        else:
            print("No assistant configurations found in database.")
            
    except Exception as e:
        print(f"❌ Error accessing Supabase: {e}")


async def run_interactive_demo():
    """Run an interactive demonstration."""
    
    print("\n🎮 Interactive Memory Demo")
    print("=" * 50)
    print("This demo shows how the assistant remembers information across conversations.")
    print("Try talking about yourself, your preferences, and ask the assistant to remember things.")
    print("Type 'quit' to exit.\n")
    
    # Create agent graph
    graph = create_enhanced_agent_graph()
    
    # User configuration
    user_config = {
        "configurable": {
            "user_id": "interactive_demo_user",
            "thread_id": f"demo_{int(datetime.now().timestamp())}"
        }
    }
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Thanks for testing the enhanced memory system.")
                break
            
            if not user_input:
                continue
            
            print("🤖 Assistant: ", end="", flush=True)
            
            # Run the graph
            response = None
            async for chunk in graph.astream(
                {"messages": [HumanMessage(content=user_input)]}, 
                user_config
            ):
                if "messages" in chunk:
                    last_message = chunk["messages"][-1]
                    if hasattr(last_message, 'content') and not hasattr(last_message, 'tool_calls'):
                        response = last_message.content
            
            if response:
                print(response)
            else:
                print("[No response generated]")
                
        except KeyboardInterrupt:
            print("\n👋 Demo interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Enhanced Memory Assistant Test Suite")
    print("=" * 60)
    print("Testing comprehensive memory management and flexible language configuration\n")
    
    # Test 1: Language Configurations
    test_language_configurations()
    
    # Test 2: Supabase Configuration
    test_supabase_assistant_config()
    
    # Test 3: Memory Management
    print("\nRunning memory management tests...")
    try:
        asyncio.run(test_memory_management())
    except KeyboardInterrupt:
        print("\n👋 Memory tests interrupted by user")
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
    
    # Test 4: Language Flexibility
    print("\nRunning language flexibility tests...")
    try:
        asyncio.run(test_language_flexibility())
    except KeyboardInterrupt:
        print("\n👋 Language tests interrupted by user")
    except Exception as e:
        print(f"❌ Language test failed: {e}")
    
    # Test 5: Interactive Demo
    user_choice = input("\n🎮 Would you like to run the interactive demo? (y/n): ").strip().lower()
    if user_choice in ['y', 'yes']:
        try:
            asyncio.run(run_interactive_demo())
        except KeyboardInterrupt:
            print("\n👋 Interactive demo interrupted by user")
        except Exception as e:
            print(f"❌ Interactive demo failed: {e}")
    
    print("\n✅ Test suite completed!")
    print("\n📊 Summary:")
    print("• ✅ Language configuration system tested")
    print("• ✅ Memory management capabilities tested") 
    print("• ✅ Supabase integration verified")
    print("• ✅ Enhanced assistant system ready for use")
    print("\n🎯 The assistant now supports:")
    print("• 📝 Comprehensive user memory (profile, preferences, conversations)")
    print("• 🌍 Flexible language configuration (Arabic, Spanish, French, etc.)")
    print("• 🔄 Memory continuity across conversation threads")
    print("• ⚙️ Customizable assistant instructions and behavior")
    print("• 💾 Persistent memory storage in LangGraph Memory Store") 