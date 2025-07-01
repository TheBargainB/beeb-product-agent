#!/usr/bin/env python3
"""Test script for Supabase-integrated memory system"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore

def test_memory_integration():
    """Test the Supabase memory integration"""
    print("🧪 Testing Supabase Memory Integration...")
    
    # Import from our agent
    from agent.supabase_client import SupabaseClient
    from agent.memory_tools import MemoryManager
    from agent.graph import create_agent_graph
    from langchain_openai import ChatOpenAI
    
    # Test 1: Database connection
    print("\n1️⃣ Testing database connection...")
    try:
        supabase_client = SupabaseClient()
        result = supabase_client.client.table('crm_profiles').select('count', count='exact').execute()
        print(f"✅ Connected to Supabase - {result.count} profiles in database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 2: Memory Manager initialization
    print("\n2️⃣ Testing MemoryManager with Supabase...")
    try:
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        memory_manager = MemoryManager(model, supabase_client)
        store = InMemoryStore()  # For cross-thread memory
        print("✅ MemoryManager initialized successfully")
    except Exception as e:
        print(f"❌ MemoryManager initialization failed: {e}")
        return False
    
    # Test 3: Profile operations
    print("\n3️⃣ Testing user profile operations...")
    try:
        test_user_id = "test_user_001"
        
        # Test profile creation/retrieval
        profile = memory_manager.get_user_profile(store, test_user_id)
        print(f"✅ Profile retrieved: {profile}")
        
        # Test context formatting
        context = memory_manager.format_user_context(store, test_user_id)
        print(f"✅ Context formatted: {len(context)} characters")
        
    except Exception as e:
        print(f"❌ Profile operations failed: {e}")
        return False
    
    # Test 4: Grocery lists
    print("\n4️⃣ Testing grocery list operations...")
    try:
        grocery_lists = memory_manager.get_grocery_lists(store, test_user_id)
        print(f"✅ Grocery lists retrieved: {len(grocery_lists)} lists")
        
        meal_plans = memory_manager.get_meal_plans(store, test_user_id)
        print(f"✅ Meal plans retrieved: {len(meal_plans)} plans")
        
        budgets = memory_manager.get_budgets(store, test_user_id)
        print(f"✅ Budgets retrieved: {len(budgets)} budgets")
        
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
        return False
    
    # Test 5: Graph creation
    print("\n5️⃣ Testing enhanced graph creation...")
    try:
        graph = create_agent_graph()
        print("✅ Enhanced graph created successfully")
        
        # Test compilation
        compiled_graph = graph.compile(
            checkpointer=InMemoryStore(),
            store=InMemoryStore()
        )
        print("✅ Graph compiled successfully")
        
    except Exception as e:
        print(f"❌ Graph creation failed: {e}")
        return False
    
    # Test 6: Sample conversation with memory
    print("\n6️⃣ Testing sample conversation...")
    try:
        config = {
            "configurable": {
                "user_id": test_user_id,
                "thread_id": "test_thread_001"
            }
        }
        
        # Simple query
        result = compiled_graph.invoke(
            {"messages": [HumanMessage(content="Hi! I'm Sarah from Amsterdam. I'm vegetarian and my budget is €75 per week.")]},
            config
        )
        
        print(f"✅ Conversation test passed - {len(result['messages'])} messages")
        print(f"   Last message preview: {result['messages'][-1].content[:100]}...")
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Supabase memory integration is working correctly.")
    return True

def test_database_schema():
    """Test that our database schema is working correctly"""
    print("\n📊 Testing database schema...")
    
    from agent.supabase_client import SupabaseClient
    
    try:
        supabase = SupabaseClient()
        
        # Test products_optimized view
        products = supabase.search_products("melk", limit=3)
        print(f"✅ Product search: Found {len(products)} products")
        
        # Test recipe functionality
        recipe_result = supabase.client.table('recipes').select('*').limit(1).execute()
        print(f"✅ Recipes table: {len(recipe_result.data)} recipes")
        
        # Test meal plans
        meal_result = supabase.client.table('meal_plans').select('*').limit(1).execute()
        print(f"✅ Meal plans table: {len(meal_result.data)} plans")
        
        # Test budget periods
        budget_result = supabase.client.table('budget_periods').select('*').limit(1).execute()
        print(f"✅ Budget periods table: {len(budget_result.data)} periods")
        
        print("✅ Database schema validation complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Supabase Memory Integration Tests")
    print("=" * 50)
    
    # Check environment
    required_vars = ["OPENAI_API_KEY", "SUPABASE_ANON_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please set these in your .env file or environment")
        sys.exit(1)
    
    # Run tests
    schema_ok = test_database_schema()
    memory_ok = test_memory_integration()
    
    if schema_ok and memory_ok:
        print("\n🎉 SUCCESS: All systems working!")
        print("✅ Database schema is correct")
        print("✅ Memory integration is functional") 
        print("✅ Ready for deployment")
    else:
        print("\n❌ FAILURE: Some tests failed")
        sys.exit(1) 