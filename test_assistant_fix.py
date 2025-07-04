#!/usr/bin/env python3
"""
Quick test script to verify the assistant configuration fix.
This script tests that the Arabic assistant now properly enforces language requirements.
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
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory.")
    sys.exit(1)


def test_assistant_config_loading():
    """Test that assistant configuration is loaded from database"""
    
    print("🔧 Testing Assistant Configuration Loading")
    print("=" * 50)
    
    try:
        supabase_client = SupabaseClient()
        
        # Test loading the Arabic assistant configuration
        assistant_id = "5c38e294-2180-4d1e-bb64-e5b93558e6b2"
        result = supabase_client.client.table('conversations').select('assistant_config, assistant_name').eq('assistant_id', assistant_id).order('created_at', desc=True).limit(1).execute()
        
        if result.data:
            config = result.data[0]
            print(f"✅ Successfully loaded config for: {config.get('assistant_name')}")
            
            assistant_config = config.get('assistant_config', {})
            configurable = assistant_config.get('configurable', {})
            
            print(f"   Language: {configurable.get('language')}")
            print(f"   Response Format: {configurable.get('response_format')}")
            print(f"   Has Instructions: {'✅' if configurable.get('instructions') else '❌'}")
            
            if configurable.get('language') == 'arabic':
                print("✅ Arabic language enforcement detected in database")
                return True
            else:
                print("❌ No Arabic language enforcement found")
                return False
        else:
            print("❌ No assistant configuration found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error loading assistant config: {e}")
        return False


async def test_arabic_language_enforcement():
    """Test that Arabic assistant responds in Arabic regardless of input language"""
    
    print("\n🇸🇦 Testing Arabic Language Enforcement")
    print("=" * 50)
    
    try:
        graph = create_enhanced_agent_graph()
        
        # Configuration for Arabic assistant
        arabic_config = {
            "configurable": {
                "assistant_id": "5c38e294-2180-4d1e-bb64-e5b93558e6b2",  # Ayoub Arabic Assistant
                "customer_profile_id": "4c432d3e-0a15-4272-beda-0d327088d5f6",
                "user_id": "test_arabic_fix",
                "thread_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        # Test with English input - should get Arabic output
        test_message = "give me a recipe for falafel"
        
        print(f"📝 Testing with English input: '{test_message}'")
        print("🎯 Expected: Response should be in Arabic")
        print("⏳ Processing...")
        
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": test_message}]},
            config=arabic_config
        )
        
        if result and 'messages' in result:
            response = result['messages'][-1].content
            print(f"\n🤖 Response received ({len(response)} chars)")
            print(f"First 200 chars: {response[:200]}...")
            
            # Check if response contains Arabic text
            arabic_chars = sum(1 for char in response if '\u0600' <= char <= '\u06FF')
            total_chars = len(response)
            arabic_percentage = (arabic_chars / total_chars) * 100 if total_chars > 0 else 0
            
            print(f"\n📊 Analysis:")
            print(f"   Arabic characters: {arabic_chars}/{total_chars} ({arabic_percentage:.1f}%)")
            
            if arabic_percentage > 50:
                print("✅ SUCCESS: Response is primarily in Arabic!")
                print("🎉 Language enforcement is working correctly!")
                return True
            else:
                print("❌ FAILURE: Response is not primarily in Arabic")
                print("🚨 Language enforcement is NOT working")
                return False
                
        else:
            print("❌ No response received from assistant")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Arabic assistant: {e}")
        return False


async def main():
    """Main test function"""
    
    print("🧪 Assistant Configuration Fix - Verification Test")
    print("=" * 60)
    print("This test verifies that the Arabic assistant now enforces language requirements")
    print()
    
    # Test 1: Configuration loading
    config_loaded = test_assistant_config_loading()
    
    if not config_loaded:
        print("\n❌ Configuration loading failed - cannot proceed with language test")
        return
    
    # Test 2: Arabic language enforcement
    language_enforced = await test_arabic_language_enforcement()
    
    # Final results
    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS:")
    print(f"   Configuration Loading: {'✅ PASS' if config_loaded else '❌ FAIL'}")
    print(f"   Language Enforcement: {'✅ PASS' if language_enforced else '❌ FAIL'}")
    
    if config_loaded and language_enforced:
        print("\n🎉 SUCCESS: The assistant configuration fix is working!")
        print("   ✅ Assistant config is loaded from database")
        print("   ✅ Arabic language enforcement is active")
        print("   ✅ English input → Arabic output working correctly")
    else:
        print("\n🚨 FAILURE: The fix is not working correctly")
        print("   Please check the implementation and try again")


if __name__ == "__main__":
    print("🚀 Starting Assistant Configuration Fix Test...")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Please check your environment and try again") 