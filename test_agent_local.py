#!/usr/bin/env python3
"""
Local testing script for the overhauled BargainB Agent with Supabase integration.

This script allows you to test the agent locally with various scenarios:
1. Configuration validation
2. Database connectivity
3. Memory management
4. Product search
5. Customer profile management

Usage:
    python test_agent_local.py
"""

import os
import sys
from datetime import datetime, date

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from agent.config import get_config, reload_config
from agent.graph import run_agent_locally, create_local_test_graph
from agent.supabase_client import SupabaseClient
from agent.memory_tools import SupabaseMemoryManager


def check_environment():
    """Check if environment variables are properly set."""
    print("🔍 Checking environment variables...")
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API access",
        "SUPABASE_URL": "Supabase project URL", 
        "SUPABASE_ANON_KEY": "Supabase anonymous key"
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  ❌ {var} - {description}")
        else:
            print(f"  ✅ {var} - Found")
    
    if missing:
        print("\n⚠️  Missing environment variables:")
        print("\n".join(missing))
        print("\n🔧 Please set these in your .env file or shell environment")
        return False
    
    print("✅ All environment variables found!")
    return True


def test_configuration():
    """Test the configuration system."""
    print("\n📋 Testing configuration...")
    
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")
        
        # Test validation
        validation = config.validate_configuration()
        print(f"✅ Configuration validation: {validation}")
        
        # Print summary
        print("\n" + "="*60)
        print(config.get_config_summary())
        print("="*60)
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_database_connection():
    """Test Supabase database connection."""
    print("\n🗄️  Testing database connection...")
    
    try:
        supabase = SupabaseClient()
        print("✅ Supabase client created")
        
        # Test basic query
        result = supabase.client.table('crm_profiles').select('id').limit(1).execute()
        print(f"✅ Database query successful - found {len(result.data)} profiles")
        
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def test_memory_manager():
    """Test the memory management system."""
    print("\n🧠 Testing memory manager...")
    
    try:
        from langchain_openai import ChatOpenAI
        
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        supabase = SupabaseClient()
        memory_manager = SupabaseMemoryManager(model, supabase)
        
        print("✅ Memory manager created")
        
        # Test profile retrieval
        profile = memory_manager.get_user_profile()
        print(f"✅ Profile retrieval: {profile is not None}")
        
        # Test context formatting
        context = memory_manager.format_user_context()
        print(f"✅ Context formatting: {len(context)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Memory manager error: {e}")
        return False


def test_agent_queries():
    """Test the agent with various queries."""
    print("\n🤖 Testing agent queries...")
    
    test_queries = [
        "Hello! I'm looking for some bread options from Albert Heijn.",
        "I need help planning meals for this week. I'm vegetarian.",
        "What's my current grocery list?",
        "Can you help me find organic apples with good prices?",
        "I want to set a budget of €100 per week for groceries."
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test Query {i}: {query[:50]}...")
        
        try:
            response = run_agent_locally(query, user_id="test-user", verbose=False)
            
            if response and "error" not in response.lower():
                print(f"✅ Success - Response length: {len(response)} chars")
                results.append(True)
            else:
                print(f"⚠️  Warning - Response: {response[:100]}...")
                results.append(False)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Agent Test Results: {success_rate:.0f}% success rate ({sum(results)}/{len(results)} passed)")
    
    return success_rate >= 80  # 80% success rate threshold


def run_interactive_session():
    """Run an interactive session with the agent."""
    print("\n💬 Interactive Session")
    print("="*50)
    print("Type 'quit' to exit, 'config' to show configuration, 'help' for commands")
    print("="*50)
    
    while True:
        try:
            question = input("\n🙋 You: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif question.lower() == 'config':
                config = get_config()
                print(config.get_config_summary())
                continue
            elif question.lower() == 'help':
                print("""
Available commands:
- 'config' - Show current configuration
- 'quit'/'exit'/'q' - Exit the session
- Any other text - Send to the agent

Example queries:
- "Find me some healthy breakfast options"
- "I need ingredients for pasta carbonara"
- "What's in my grocery list?"
- "Set a budget of €80 per week"
- "Plan meals for next 3 days"
""")
                continue
            elif not question:
                continue
            
            print("🤖 Agent: ", end="", flush=True)
            response = run_agent_locally(question, user_id="interactive-user", verbose=False)
            print(response)
            
        except KeyboardInterrupt:
            print("\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main test function."""
    print("🎯 BargainB Agent - Local Testing Suite")
    print("="*60)
    
    # Run all tests
    tests = [
        ("Environment Check", check_environment),
        ("Configuration Test", test_configuration),
        ("Database Connection", test_database_connection),
        ("Memory Manager", test_memory_manager),
        ("Agent Queries", test_agent_queries)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n🎯 Test Summary")
    print("="*60)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} - {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The agent is ready to use.")
        
        # Ask if user wants interactive session
        if input("\n🤔 Would you like to start an interactive session? (y/n): ").lower().startswith('y'):
            run_interactive_session()
    else:
        print("⚠️  Some tests failed. Please check the configuration and environment.")
        
        if input("\n🤔 Would you like to try the interactive session anyway? (y/n): ").lower().startswith('y'):
            run_interactive_session()


if __name__ == "__main__":
    main() 