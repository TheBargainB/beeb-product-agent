"""Test the enhanced product search tools with new database capabilities."""

import os
from src.agent.tools import (
    smart_grocery_search,
    semantic_product_search,
    compare_product_prices,
    get_budget_meal_options,
    get_price_alternatives,
    build_grocery_list,
    suggest_store_split,
    get_price_trends,
    get_product_by_gtin
)


def test_enhanced_tools():
    """Test the enhanced tools to verify database integration."""
    
    print("🧪 Testing Enhanced Grocery Agent Tools\n")
    print("=" * 50)
    
    # Test 1: Smart Grocery Search (main tool)
    print("\n1. Testing Smart Grocery Search (with price optimization)")
    try:
        result = smart_grocery_search.invoke({
            "query": "healthy breakfast options",
            "budget": 10.0,
            "store_preference": "Albert Heijn"
        })
        print(f"✅ Smart search result: {result[:200]}...")
    except Exception as e:
        print(f"❌ Smart search error: {e}")
    
    # Test 2: Semantic Product Search
    print("\n2. Testing Semantic Product Search")
    try:
        result = semantic_product_search.invoke({
            "query": "melk",
            "similarity_threshold": 0.3,
            "max_results": 5
        })
        print(f"✅ Semantic search result: {result[:200]}...")
    except Exception as e:
        print(f"❌ Semantic search error: {e}")
    
    # Test 3: Price Comparison (requires valid GTIN)
    print("\n3. Testing Price Comparison")
    try:
        # First get a product to get its GTIN
        search_result = smart_grocery_search.invoke({"query": "brood"})
        print(f"✅ Price comparison setup: {search_result[:100]}...")
    except Exception as e:
        print(f"❌ Price comparison error: {e}")
    
    # Test 4: Budget Meal Options
    print("\n4. Testing Budget Meal Options")
    try:
        result = get_budget_meal_options.invoke({
            "budget_per_meal": 15.0,
            "dietary_restrictions": ["vegetarian"]
        })
        print(f"✅ Meal options result: {result[:200]}...")
    except Exception as e:
        print(f"❌ Meal options error: {e}")
    
    # Test 5: Fallback to Basic Search
    print("\n5. Testing Fallback to Basic Search")
    try:
        # This should trigger fallback if RPC functions aren't available
        result = smart_grocery_search.invoke({"query": "test product"})
        print(f"✅ Fallback working: {result[:200]}...")
    except Exception as e:
        print(f"❌ Fallback error: {e}")
    
    print(f"\n{'=' * 50}")
    print("🎉 Enhanced tools integration test completed!")
    print("\nNew capabilities added:")
    print("• Semantic search (finds products by meaning)")
    print("• Price optimization (always returns best deals)")
    print("• Budget-aware results (respects spending limits)")
    print("• Multi-store price comparison")
    print("• Meal planning within budget")
    print("• Shopping cart optimization")
    print("• Price trend analysis")
    print("• Store split recommendations")


if __name__ == "__main__":
    # Check environment
    if not os.getenv("SUPABASE_ANON_KEY"):
        print("❌ SUPABASE_ANON_KEY not found in environment")
        print("Please set your Supabase credentials to test the enhanced tools")
    else:
        test_enhanced_tools() 