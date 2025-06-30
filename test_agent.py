#!/usr/bin/env python3
"""Test script for the product retrieval agent."""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.supabase_client import SupabaseClient
from agent.graph import run_agent


def test_database_connection():
    """Test the database connection and basic functionality."""
    print("🔍 Testing database connection...")
    
    try:
        client = SupabaseClient()
        success = client.test_connection()
        
        if success:
            print("✅ Database connection test passed")
            return True
        else:
            print("❌ Database connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def test_database_operations():
    """Test individual database operations."""
    print("\n🔍 Testing database operations...")
    
    try:
        client = SupabaseClient()
        
        # Test product search
        print("\n1. Testing product search...")
        products = client.search_products("milk", limit=3)
        if products:
            print(f"   ✅ Found {len(products)} products")
            for product in products[:2]:  # Show first 2 results
                print(f"   - {product.get('title', 'No title')} (GTIN: {product.get('gtin', 'No GTIN')})")
        else:
            print("   ⚠️  No products found for 'milk'")
        
        # Test category search
        print("\n2. Testing category search...")
        category_products = client.search_by_category("dairy", limit=3)
        if category_products:
            print(f"   ✅ Found {len(category_products)} products in dairy category")
            for product in category_products[:2]:
                print(f"   - {product.get('title', 'No title')}")
        else:
            print("   ⚠️  No products found in 'dairy' category")
            
        # Test brand search
        print("\n3. Testing brand search...")
        brand_products = client.search_by_brand("coca", limit=3)
        if brand_products:
            print(f"   ✅ Found {len(brand_products)} products for brand search")
            for product in brand_products[:2]:
                print(f"   - {product.get('title', 'No title')}")
        else:
            print("   ⚠️  No products found for brand 'coca'")
            
        return True
        
    except Exception as e:
        print(f"❌ Database operations error: {e}")
        return False


def test_agent_queries():
    """Test the agent with various types of queries."""
    print("\n🤖 Testing agent queries...")
    
    test_queries = [
        "Find me some milk products",
        "What dairy products are available?", 
        "Show me Coca Cola products",
        "Do you have any chocolate?",
        "Tell me about product with GTIN 1234567890123"  # This will likely not exist
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'-'*60}")
        print(f"Query {i}: {query}")
        print(f"{'-'*60}")
        
        try:
            response = run_agent(query, verbose=True)
            
            if response:
                # Extract content whether it's a message object or dict
                if hasattr(response, 'content'):
                    content = response.content
                elif isinstance(response, dict) and 'content' in response:
                    content = response['content']
                else:
                    content = str(response)
                
                print(f"\n✅ Query {i} completed")
                print(f"Response: {content[:200]}{'...' if len(content) > 200 else ''}")
                results.append(True)
            else:
                print(f"\n❌ Query {i} failed - no response")
                results.append(False)
                
        except Exception as e:
            print(f"\n❌ Query {i} failed with error: {e}")
            results.append(False)
    
    successful_queries = sum(results)
    total_queries = len(results)
    
    print(f"\n{'='*60}")
    print(f"Agent Test Results: {successful_queries}/{total_queries} queries successful")
    print(f"{'='*60}")
    
    return successful_queries == total_queries


def main():
    """Run all tests."""
    print("🚀 Starting Product Retrieval Agent Tests")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY", "SUPABASE_ANON_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please check your .env file")
        return False
    
    print("✅ Environment variables loaded")
    
    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Operations", test_database_operations), 
        ("Agent Queries", test_agent_queries)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running {test_name} Test")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{test_name} Test: {status}")
        except Exception as e:
            print(f"\n❌ {test_name} Test: FAILED with error: {e}")
            results.append(False)
    
    # Final summary
    passed_tests = sum(results)
    total_tests = len(results)
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The agent is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 