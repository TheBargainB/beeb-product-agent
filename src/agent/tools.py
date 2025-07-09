"""Tools for the product retrieval agent."""

import json
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from .supabase_client import SupabaseClient


# Initialize Supabase client
supabase_client = SupabaseClient()


def format_product_result(product: Dict[str, Any]) -> str:
    """Format a product result for the LLM."""
    # Handle both old format (optimized view) and new format (RPC functions)
    result = f"Product: {product.get('title', product.get('product_title', 'N/A'))}\n"
    result += f"GTIN: {product.get('gtin', 'N/A')}\n"
    result += f"Description: {product.get('description', 'N/A')}\n"
    
    # Brand and category 
    if product.get('brand_name'):
        result += f"Brand: {product.get('brand_name')}\n"
    
    if product.get('category_name'):
        result += f"Category: {product.get('category_name')}\n"
    
    if product.get('subcategory_name'):
        result += f"Subcategory: {product.get('subcategory_name')}\n"
    
    # Pricing information - handle both formats
    pricing_info = []
    
    # Check for optimized view format
    albert_price = product.get('albert_price')
    if albert_price:
        pricing_info.append(f"Albert Heijn: €{albert_price}")
    
    dirk_price = product.get('dirk_price')
    if dirk_price:
        pricing_info.append(f"Dirk: €{dirk_price}")
    
    jumbo_price = product.get('jumbo_price')
    if jumbo_price:
        pricing_info.append(f"Jumbo: €{jumbo_price}")
    
    # Check for RPC function format
    if product.get('price') and product.get('store_name'):
        pricing_info.append(f"{product.get('store_name')}: €{product.get('price')}")
    
    if pricing_info:
        result += f"Prices: {', '.join(pricing_info)}\n"
    
    # Best price if available
    if product.get('best_price') and product.get('best_store'):
        result += f"Best Deal: €{product.get('best_price')} at {product.get('best_store')}\n"
    
    # Similarity score for semantic search results
    if product.get('similarity_score'):
        result += f"Relevance: {product.get('similarity_score'):.2f}\n"
    
    # Availability
    stores_available = []
    if product.get('albert_available'):
        stores_available.append("Albert Heijn")
    if product.get('dirk_available'):
        stores_available.append("Dirk")
    if product.get('jumbo_available'):
        stores_available.append("Jumbo")
    
    if stores_available:
        result += f"Available at: {', '.join(stores_available)}\n"
    
    result += "\n"
    return result


@tool
def smart_grocery_search(query: str, budget: float = None, store_preference: str = None) -> str:
    """
    Advanced semantic search with price optimization. This is the main search function.
    Finds products by meaning (not just keywords) and optimizes for price and budget.
    
    ⚠️ IMPORTANT: Products are primarily in Dutch. If user searches in English, try Dutch equivalents:
    - 'milk' → 'melk', 'dairy' → 'zuivel', 'chocolate' → 'chocolade', 'bread' → 'brood'
    
    Args:
        query: The search query string (natural language, try Dutch terms for better results)
        budget: Optional maximum budget for the search
        store_preference: Optional store preference ('Albert Heijn', 'Dirk', 'Jumbo')
        
    Returns:
        Formatted string containing price-optimized product recommendations
    """
    try:
        # Use the new smart grocery search function
        params = {
            'user_query': query,
            'max_budget': budget,
            'store_preference': store_preference
        }
        
        response = supabase_client.client.rpc('smart_grocery_search', params).execute()
        
        if not response.data:
            return f"No products found for query: {query}"
        
        products = response.data
        result = f"Found {len(products)} price-optimized results for '{query}'"
        
        if budget:
            result += f" (budget: €{budget})"
        if store_preference:
            result += f" (preferred store: {store_preference})"
        
        result += ":\n\n"
        
        for product in products:
            result += format_product_result(product)
        
        return result
        
    except Exception as e:
        # Fallback to basic search if RPC fails
        try:
            products = supabase_client.search_products(query, limit=10)
            if not products:
                return f"No products found for query: {query}"
            
            result = f"Found {len(products)} products for query '{query}' (basic search):\n\n"
            for product in products:
                result += format_product_result(product)
            
            return result
        except Exception as fallback_error:
            return f"Error searching products: {e}. Fallback error: {fallback_error}"


@tool
def semantic_product_search(query: str, similarity_threshold: float = 0.3, max_results: int = 10) -> str:
    """
    Pure semantic search that finds products by meaning, not exact text matches.
    Use this for exploratory searches when you want to understand what products exist.
    
    Args:
        query: The search query string (natural language)
        similarity_threshold: Minimum similarity score (0.1-1.0, lower = more results)
        max_results: Maximum number of results to return
        
    Returns:
        Formatted string containing semantically relevant products with similarity scores
    """
    try:
        params = {
            'search_query': query,
            'similarity_threshold': similarity_threshold,
            'max_results': max_results
        }
        
        response = supabase_client.client.rpc('semantic_product_search', params).execute()
        
        if not response.data:
            return f"No semantically similar products found for: {query}"
        
        products = response.data
        result = f"Found {len(products)} semantically relevant products for '{query}':\n\n"
        
        for product in products:
            result += format_product_result(product)
        
        return result
        
    except Exception as e:
        return f"Error in semantic search: {e}"


@tool
def compare_product_prices(gtin: str) -> str:
    """
    Compare prices of a specific product across all available stores.
    Shows where you can find the best deal and how much you can save.
    
    Args:
        gtin: The product GTIN (Global Trade Item Number)
        
    Returns:
        Formatted string with price comparison across stores
    """
    try:
        response = supabase_client.client.rpc('compare_product_prices', {'gtin_input': gtin}).execute()
        
        if not response.data:
            return f"No price comparison available for GTIN: {gtin}"
        
        comparisons = response.data
        if len(comparisons) < 2:
            # Single store result
            if comparisons:
                product = comparisons[0]
                return f"Product: {product.get('product_title', 'N/A')}\nPrice: €{product.get('price')} at {product.get('store_name')}\n(Only available at one store)"
            else:
                return f"Product with GTIN {gtin} not found in any store"
        
        # Multiple stores - show comparison
        product_title = comparisons[0].get('product_title', 'Product')
        result = f"Price comparison for {product_title}:\n\n"
        
        prices = []
        for comparison in comparisons:
            store = comparison.get('store_name')
            price = comparison.get('price')
            result += f"• {store}: €{price}\n"
            prices.append(float(price))
        
        if len(prices) > 1:
            savings = max(prices) - min(prices)
            cheapest_store = next(c['store_name'] for c in comparisons if float(c['price']) == min(prices))
            result += f"\n💰 Save €{savings:.2f} by shopping at {cheapest_store}!"
        
        return result
        
    except Exception as e:
        # Fallback to basic GTIN lookup
        try:
            product = supabase_client.get_product_by_gtin(gtin)
            if product:
                return format_product_result(product)
            else:
                return f"No product found with GTIN: {gtin}"
        except Exception as fallback_error:
            return f"Error comparing prices: {e}. Fallback error: {fallback_error}"


@tool
def get_budget_meal_options(budget_per_meal: float, dietary_preferences: List[str] = None) -> str:
    """
    Find complete meal options within a specified budget.
    
    Args:
        budget_per_meal: Maximum budget per meal in euros
        dietary_preferences: Optional list of dietary preferences 
                            (e.g., ['vegetarian', 'low-carb', 'high-protein', 'healthy'])
        
    Returns:
        Formatted string with meal suggestions within budget
    """
    try:
        # Map common dietary preferences to available database tags
        preference_mapping = {
            'low-carb': ['healthy'],
            'high-protein': ['healthy'],
            'protein': ['healthy'],
            'low carb': ['healthy'],
            'high protein': ['healthy'],
            'keto': ['healthy'],
            'paleo': ['healthy'],
            'clean eating': ['healthy'],
            'nutritious': ['healthy'],
            'diet': ['healthy'],
            'weight loss': ['healthy'],
            'fitness': ['healthy'],
            'vegan': ['vegetarian'],
            'plant-based': ['vegetarian'],
            'plant based': ['vegetarian'],
            'meatless': ['vegetarian'],
            'gluten-free': ['healthy'],
            'gluten free': ['healthy'],
            'dairy-free': ['healthy'],
            'dairy free': ['healthy'],
            'quick': ['quick'],
            'fast': ['quick'],
            'easy': ['quick'],
            'simple': ['quick'],
            'lunch': ['lunch'],
            'dinner': [],
            'breakfast': [],
            'comfort': ['comfort'],
            'warming': ['warm'],
            'warm': ['warm'],
            'hot': ['warm'],
            'fresh': ['fresh'],
            'light': ['fresh'],
            'crisp': ['fresh'],
            'salad': ['fresh', 'healthy']
        }
        
        # Convert user preferences to database-supported tags
        mapped_preferences = []
        if dietary_preferences:
            for pref in dietary_preferences:
                pref_lower = pref.lower().strip()
                if pref_lower in preference_mapping:
                    mapped_preferences.extend(preference_mapping[pref_lower])
                elif pref_lower in ['vegetarian', 'healthy', 'fresh', 'quick', 'lunch', 'comfort', 'warm']:
                    # Direct matches for supported tags
                    mapped_preferences.append(pref_lower)
        
        # Remove duplicates and empty values
        mapped_preferences = list(set([p for p in mapped_preferences if p]))
        
        # If no preferences mapped, try without filtering
        if dietary_preferences and not mapped_preferences:
            mapped_preferences = None
        
        params = {
            'budget_per_meal': budget_per_meal,
            'dietary_preferences': mapped_preferences
        }
        
        response = supabase_client.client.rpc('get_budget_meal_options', params).execute()
        
        if not response.data:
            # Try again without dietary preferences if none found
            if mapped_preferences:
                params = {
                    'budget_per_meal': budget_per_meal,
                    'dietary_preferences': None
                }
                response = supabase_client.client.rpc('get_budget_meal_options', params).execute()
                
                if response.data:
                    result = f"No meals found matching your dietary preferences within €{budget_per_meal}, but here are general options:\n\n"
                else:
                    return f"No meal options found within €{budget_per_meal} budget"
            else:
                return f"No meal options found within €{budget_per_meal} budget"
        
        meals = response.data
        if not meals:
            return f"No meal options found within €{budget_per_meal} budget"
        
        if 'No meals found matching' not in locals().get('result', ''):
            result = f"Found {len(meals)} meal options within €{budget_per_meal} budget"
            
            if dietary_preferences:
                original_prefs = ', '.join(dietary_preferences)
                if mapped_preferences:
                    mapped_prefs = ', '.join(mapped_preferences)
                    result += f" (preferences: {original_prefs} → mapped to: {mapped_prefs})"
                else:
                    result += f" (preferences: {original_prefs})"
            
            result += ":\n\n"
        
        for meal in meals:
            meal_name = meal.get('meal_concept', meal.get('meal_name', 'Unknown Meal'))
            total_cost = meal.get('total_cost', 'N/A')
            ingredient_count = meal.get('ingredient_count', meal.get('item_count', 'N/A'))
            dietary_tags = meal.get('dietary_tags', [])
            cost_per_serving = meal.get('cost_per_serving', 'N/A')
            
            result += f"🍽️ **{meal_name}**\n"
            result += f"   Total Cost: €{total_cost}\n"
            result += f"   Ingredients: {ingredient_count} items\n"
            if cost_per_serving != 'N/A':
                result += f"   Cost per serving: €{cost_per_serving}\n"
            
            if dietary_tags:
                result += f"   Tags: {', '.join(dietary_tags)}\n"
            
            # Show main ingredients if available
            main_ingredients = meal.get('main_ingredients', meal.get('ingredients_detail', []))
            if main_ingredients and isinstance(main_ingredients, list):
                result += f"   Key ingredients:\n"
                for ingredient in main_ingredients[:3]:  # Show top 3 ingredients
                    if isinstance(ingredient, dict):
                        ing_name = ingredient.get('ingredient', 'Unknown')
                        ing_price = ingredient.get('price', 'N/A')
                        ing_store = ingredient.get('store', 'Unknown Store')
                        result += f"     • {ing_name} - €{ing_price} at {ing_store}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error finding meal options: {e}"


@tool
def get_price_alternatives(product_id: str, max_price: float) -> str:
    """
    Find similar products within a specified price range.
    Use this to suggest budget-friendly alternatives.
    
    Args:
        product_id: The UUID of the original product
        max_price: Maximum price for alternatives
        
    Returns:
        Formatted string with budget-friendly alternatives
    """
    try:
        params = {
            'target_product_id': product_id,
            'max_price': max_price
        }
        
        response = supabase_client.client.rpc('get_price_alternatives', params).execute()
        
        if not response.data:
            return f"No alternatives found under €{max_price}"
        
        alternatives = response.data
        result = f"Found {len(alternatives)} budget-friendly alternatives under €{max_price}:\n\n"
        
        for alt in alternatives:
            result += format_product_result(alt)
        
        return result
        
    except Exception as e:
        return f"Error finding price alternatives: {e}"


@tool
def build_grocery_list(product_ids: List[str], target_budget: float) -> str:
    """
    Optimize a grocery list within a target budget.
    Suggests the best combination of stores to minimize cost.
    
    Args:
        product_ids: List of product UUIDs to include in the shopping list
        target_budget: Maximum budget for the entire shopping list
        
    Returns:
        Formatted string with optimized shopping list and store recommendations
    """
    try:
        params = {
            'product_ids': product_ids,
            'budget': target_budget
        }
        
        response = supabase_client.client.rpc('build_grocery_list', params).execute()
        
        if not response.data:
            return f"Cannot build grocery list within €{target_budget} budget"
        
        grocery_list = response.data
        result = f"Optimized grocery list within €{target_budget} budget:\n\n"
        
        if isinstance(grocery_list, list):
            total_cost = 0
            for item in grocery_list:
                result += f"• {item.get('product_title', 'N/A')} - €{item.get('price')} at {item.get('store_name')}\n"
                if item.get('price'):
                    total_cost += float(item.get('price', 0))
            
            result += f"\nTotal Cost: €{total_cost:.2f}"
            savings = target_budget - total_cost
            if savings > 0:
                result += f"\nYou're under budget by €{savings:.2f}!"
        else:
            # Handle single summary object
            result += f"Total Cost: €{grocery_list.get('total_cost', 'N/A')}\n"
            result += f"Items: {grocery_list.get('item_count', 'N/A')}\n"
            if grocery_list.get('stores_needed'):
                result += f"Stores to visit: {', '.join(grocery_list.get('stores_needed'))}\n"
        
        return result
        
    except Exception as e:
        return f"Error building grocery list: {e}"


@tool
def suggest_store_split(product_ids: List[str]) -> str:
    """
    Analyze if shopping at multiple stores would save money.
    Provides a multi-store shopping strategy with potential savings.
    
    Args:
        product_ids: List of product UUIDs to analyze
        
    Returns:
        Formatted string with multi-store shopping strategy and savings analysis
    """
    try:
        params = {
            'product_ids': product_ids
        }
        
        response = supabase_client.client.rpc('suggest_store_split', params).execute()
        
        if not response.data:
            return "No store split analysis available for these products"
        
        analysis = response.data
        result = "Multi-store shopping analysis:\n\n"
        
        if isinstance(analysis, list):
            for strategy in analysis:
                result += f"Strategy: {strategy.get('strategy_name', 'N/A')}\n"
                result += f"Total Cost: €{strategy.get('total_cost', 'N/A')}\n"
                result += f"Stores: {strategy.get('stores_required', 'N/A')}\n"
                if strategy.get('savings'):
                    result += f"Potential Savings: €{strategy.get('savings')}\n"
                result += "\n"
        else:
            # Handle single analysis object
            single_store_cost = analysis.get('single_store_cost')
            multi_store_cost = analysis.get('multi_store_cost')
            savings = analysis.get('potential_savings')
            
            result += f"Single store shopping: €{single_store_cost}\n"
            result += f"Multi-store shopping: €{multi_store_cost}\n"
            
            if savings and float(savings) > 0:
                result += f"💰 You can save €{savings} by shopping at multiple stores!\n"
                result += f"Recommended stores: {analysis.get('recommended_stores', 'N/A')}\n"
            else:
                result += "Single store shopping is more cost-effective for these items.\n"
        
        return result
        
    except Exception as e:
        return f"Error analyzing store split: {e}"


@tool
def get_price_trends(gtin: str, days_back: int = 30) -> str:
    """
    Get price history and trends for a specific product.
    Shows if prices are going up, down, or staying stable.
    
    Args:
        gtin: The product GTIN (Global Trade Item Number)
        days_back: Number of days to look back for price history (default: 30)
        
    Returns:
        Formatted string with price trend analysis
    """
    try:
        params = {
            'product_gtin': gtin,
            'days_back': days_back
        }
        
        response = supabase_client.client.rpc('get_price_trends', params).execute()
        
        if not response.data:
            return f"No price trend data available for GTIN: {gtin}"
        
        trends = response.data
        result = f"Price trend analysis for GTIN {gtin} (last {days_back} days):\n\n"
        
        if isinstance(trends, list):
            for trend in trends:
                store = trend.get('store_name', 'Unknown Store')
                current_price = trend.get('current_price')
                avg_price = trend.get('average_price')
                trend_direction = trend.get('trend_direction', 'stable')
                
                result += f"{store}:\n"
                result += f"  Current Price: €{current_price}\n"
                result += f"  Average Price: €{avg_price}\n"
                result += f"  Trend: {trend_direction}\n"
                
                if trend.get('price_change'):
                    change = trend.get('price_change')
                    if float(change) > 0:
                        result += f"  📈 Price increased by €{change}\n"
                    elif float(change) < 0:
                        result += f"  📉 Price decreased by €{abs(float(change))}\n"
                    else:
                        result += f"  ➡️ Price stable\n"
                
                result += "\n"
        else:
            # Handle single trend object
            result += f"Current Price: €{trends.get('current_price', 'N/A')}\n"
            result += f"Trend: {trends.get('trend_direction', 'N/A')}\n"
            if trends.get('recommendation'):
                result += f"Recommendation: {trends.get('recommendation')}\n"
        
        return result
        
    except Exception as e:
        return f"Error getting price trends: {e}"


@tool
def get_product_by_gtin(gtin: str) -> str:
    """
    Get detailed information about a specific product by its GTIN.
    
    Args:
        gtin: The product GTIN (Global Trade Item Number)
        
    Returns:
        Formatted string containing detailed product information
    """
    try:
        product = supabase_client.get_product_by_gtin(gtin)
        
        if not product:
            return f"No product found with GTIN: {gtin}"
        
        return format_product_result(product)
        
    except Exception as e:
        return f"Error fetching product by GTIN: {e}"


@tool
def search_products_by_category(category: str) -> str:
    """
    Search for products within a specific category.
    
    ⚠️ IMPORTANT: Categories are in Dutch. Common translations:
    - 'dairy' → 'zuivel', 'beverages' → 'dranken', 'meat' → 'vlees', 'bakery' → 'bakkerij'
    
    Args:
        category: The category name to search within (use Dutch category names)
        
    Returns:
        Formatted string containing products in the category
    """
    try:
        products = supabase_client.search_by_category(category, limit=10)
        
        if not products:
            return f"No products found in category: {category}"
        
        result = f"Found {len(products)} products in category '{category}':\n\n"
        for product in products:
            result += format_product_result(product)
        
        return result
        
    except Exception as e:
        return f"Error searching by category: {e}"


@tool
def search_products_by_brand(brand: str) -> str:
    """
    Search for products from a specific brand.
    
    Args:
        brand: The brand name to search for
        
    Returns:
        Formatted string containing products from the brand
    """
    try:
        products = supabase_client.search_by_brand(brand, limit=10)
        
        if not products:
            return f"No products found for brand: {brand}"
        
        result = f"Found {len(products)} products from brand '{brand}':\n\n"
        for product in products:
            result += format_product_result(product)
        
        return result
        
    except Exception as e:
        return f"Error searching by brand: {e}"


# List of all available tools - prioritize semantic and smart search
AVAILABLE_TOOLS = [
    smart_grocery_search,  # Main search tool with price optimization
    semantic_product_search,  # Pure semantic search for discovery
    compare_product_prices,  # Price comparison across stores
    get_budget_meal_options,  # Meal planning within budget
    get_price_alternatives,  # Budget-friendly alternatives
    build_grocery_list,  # Shopping cart optimization
    suggest_store_split,  # Multi-store shopping strategy
    get_price_trends,  # Price history and trends
    get_product_by_gtin,  # Specific product lookup
    search_products_by_category,  # Category search
    search_products_by_brand,  # Brand search
] 