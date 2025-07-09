# AI Grocery Agent Database Integration Guide

## Overview

This document provides the LangGraph AI agent development team with everything needed to integrate the semantic search layer and price intelligence functions built in Supabase. The system combines semantic understanding with price optimization to create an intelligent grocery shopping assistant.

## Architecture Overview

```
User Query → LangGraph Agent → Supabase Functions → Price-Optimized Results
    ↓              ↓                 ↓                    ↓
"healthy breakfast" → Intent Analysis → Semantic Search → Budget-Aware Results
```

## Database Functions Available

### 🔍 **Semantic Search Functions**

#### `semantic_product_search(search_query, similarity_threshold, max_results)`
- **Purpose**: Find products by meaning, not exact keywords
- **Input**: Natural language query (e.g., "healthy breakfast options")
- **Output**: Relevant products with similarity scores
- **Use Case**: Initial product discovery based on user intent

```sql
-- Example usage
SELECT * FROM semantic_product_search('healthy breakfast cereal', 0.3, 10);
```

#### `smart_grocery_search(user_query, max_budget, store_preference)`
- **Purpose**: Combines semantic search with price optimization
- **Input**: Natural language + budget constraints + store preference
- **Output**: Price-optimized product recommendations
- **Use Case**: Main search function for the AI agent

```sql
-- Example usage
SELECT * FROM smart_grocery_search('bread under 5 euros', 5.00, 'Albert Heijn');
```

### 💰 **Price Intelligence Functions**

#### `compare_product_prices(product_gtin)`
- **Purpose**: Compare same product across Albert Heijn and Jumbo
- **Input**: GTIN (product barcode)
- **Output**: Price comparison with savings information
- **Use Case**: When user asks "where is X cheaper?"

#### `build_grocery_list(product_ids, target_budget)`
- **Purpose**: Optimize grocery list within budget
- **Input**: Array of product UUIDs + budget limit
- **Output**: Store-optimized shopping list
- **Use Case**: Shopping cart optimization

#### `suggest_store_split(product_ids)`
- **Purpose**: Analyze if shopping at multiple stores saves money
- **Input**: Array of product UUIDs
- **Output**: Multi-store shopping strategy
- **Use Case**: Advanced cost optimization

#### `get_price_alternatives(product_id, max_price)`
- **Purpose**: Find similar products within price range
- **Input**: Product UUID + maximum price
- **Output**: Budget-friendly alternatives
- **Use Case**: Budget substitution suggestions

### 📊 **Analytics Functions**

#### `get_price_trends(product_gtin, days_back)`
- **Purpose**: Get price history and trends
- **Input**: GTIN + time period
- **Output**: Price trend analysis
- **Use Case**: "Has this gotten more expensive?"

#### `get_budget_meal_options(budget_per_meal, dietary_restrictions)`
- **Purpose**: Find complete meals within budget
- **Input**: Budget limit + dietary preferences array
- **Output**: Complete meal suggestions with costs
- **Use Case**: Meal planning within constraints

## Integration Patterns for LangGraph Agent

### 1. **Intent-Based Function Routing**

```python
def route_user_query(user_input: str, budget: float = None, store_pref: str = None):
    """Route user queries to appropriate Supabase functions"""
    
    intent = analyze_intent(user_input)
    
    if intent == "product_search":
        return supabase.rpc('smart_grocery_search', {
            'user_query': user_input,
            'max_budget': budget,
            'store_preference': store_pref
        })
    
    elif intent == "price_comparison":
        gtin = extract_gtin(user_input)
        return supabase.rpc('compare_product_prices', {
            'product_gtin': gtin
        })
    
    elif intent == "meal_planning":
        return supabase.rpc('get_budget_meal_options', {
            'budget_per_meal': budget or 15.00,
            'dietary_restrictions': extract_dietary_prefs(user_input)
        })
    
    elif intent == "shopping_optimization":
        product_ids = extract_product_ids_from_context()
        return supabase.rpc('suggest_store_split', {
            'product_ids': product_ids
        })
```

### 2. **Conversation Flow Integration**

```python
class GroceryAgentState(TypedDict):
    user_query: str
    budget: Optional[float]
    store_preference: Optional[str]
    shopping_cart: List[str]  # Product IDs
    conversation_history: List[Dict]
    current_intent: str

def process_grocery_query(state: GroceryAgentState):
    """Main processing node for grocery queries"""
    
    # Step 1: Semantic search for product discovery
    search_results = supabase.rpc('smart_grocery_search', {
        'user_query': state['user_query'],
        'max_budget': state['budget'],
        'store_preference': state['store_preference']
    })
    
    # Step 2: If user has items in cart, optimize store selection
    if state['shopping_cart']:
        optimization = supabase.rpc('suggest_store_split', {
            'product_ids': state['shopping_cart']
        })
        
        return {
            **state,
            'search_results': search_results.data,
            'store_optimization': optimization.data,
            'suggestion': generate_smart_suggestion(search_results.data, optimization.data)
        }
    
    return {
        **state,
        'search_results': search_results.data,
        'suggestion': generate_suggestion(search_results.data)
    }
```

### 3. **Edge Function Integration**

For real-time processing, use the deployed Edge Function:

```python
import httpx

async def call_ai_grocery_agent(query: str, budget: float = None, store_pref: str = None):
    """Call the deployed Supabase Edge Function"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/functions/v1/ai-grocery-agent",
            headers={
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "budget": budget,
                "store_preference": store_pref
            }
        )
        
        return response.json()
```

## LangGraph Node Examples

### **Product Discovery Node**

```python
def product_discovery_node(state: GroceryAgentState):
    """Discover products using semantic search"""
    
    results = supabase.rpc('semantic_product_search', {
        'search_query': state['user_query'],
        'similarity_threshold': 0.3,
        'max_results': 20
    })
    
    return {
        **state,
        'discovered_products': results.data,
        'next_action': 'price_optimization' if results.data else 'clarify_query'
    }
```

### **Price Optimization Node**

```python
def price_optimization_node(state: GroceryAgentState):
    """Optimize prices for discovered products"""
    
    if not state.get('discovered_products'):
        return state
    
    # Get price-optimized results
    optimized_results = supabase.rpc('smart_grocery_search', {
        'user_query': state['user_query'],
        'max_budget': state.get('budget'),
        'store_preference': state.get('store_preference')
    })
    
    return {
        **state,
        'optimized_results': optimized_results.data,
        'next_action': 'present_results'
    }
```

### **Shopping Cart Optimization Node**

```python
def cart_optimization_node(state: GroceryAgentState):
    """Optimize entire shopping cart"""
    
    if not state.get('shopping_cart'):
        return state
    
    # Build optimized grocery list
    grocery_list = supabase.rpc('build_grocery_list', {
        'product_ids': state['shopping_cart'],
        'target_budget': state.get('budget', 100.00)
    })
    
    # Check if multi-store shopping saves money
    store_split = supabase.rpc('suggest_store_split', {
        'product_ids': state['shopping_cart']
    })
    
    return {
        **state,
        'optimized_cart': grocery_list.data,
        'store_strategy': store_split.data,
        'next_action': 'present_shopping_plan'
    }
```

## Response Generation Examples

### **Product Search Response**

```python
def generate_product_response(results: List[Dict]) -> str:
    """Generate natural language response for product search"""
    
    if not results:
        return "I couldn't find any products matching your criteria. Could you try different terms?"
    
    best_option = min(results, key=lambda x: float(x['price']))
    
    response = f"I found {len(results)} options for you! "
    response += f"The best price is €{best_option['price']} for {best_option['product_title']} "
    response += f"at {best_option['store_name']}. "
    
    if len(results) > 1:
        response += f"I also found {len(results)-1} other options. Would you like to see them all?"
    
    return response
```

### **Price Comparison Response**

```python
def generate_price_comparison_response(comparison: List[Dict]) -> str:
    """Generate response for price comparison"""
    
    if len(comparison) < 2:
        return "This product is only available at one store in our database."
    
    cheapest = min(comparison, key=lambda x: float(x['price']))
    most_expensive = max(comparison, key=lambda x: float(x['price']))
    
    savings = float(most_expensive['price']) - float(cheapest['price'])
    
    response = f"Price comparison for {cheapest['product_title']}:\n"
    for item in comparison:
        response += f"• {item['store_name']}: €{item['price']}\n"
    
    if savings > 0:
        response += f"\nYou can save €{savings:.2f} by shopping at {cheapest['store_name']}!"
    
    return response
```

## Environment Setup

### **Required Environment Variables**

```env
# Supabase Configuration
SUPABASE_URL=your_project_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional: OpenAI for real embeddings
OPENAI_API_KEY=your_openai_key
```

### **Python Dependencies**

```bash
pip install supabase-py httpx
```

### **Supabase Client Setup**

```python
from supabase import create_client, Client

supabase: Client = create_client(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_ANON_KEY")
)
```

## Error Handling

### **Database Function Errors**

```python
def safe_supabase_call(function_name: str, params: Dict):
    """Safely call Supabase functions with error handling"""
    
    try:
        result = supabase.rpc(function_name, params)
        
        if result.data is None:
            return {
                'success': False,
                'error': 'No data returned',
                'fallback': 'try_alternative_search'
            }
        
        return {
            'success': True,
            'data': result.data
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'fallback': 'use_basic_search'
        }
```

### **Graceful Degradation**

```python
def search_with_fallback(query: str, budget: float = None):
    """Search with fallback to simpler methods if advanced search fails"""
    
    # Try semantic search first
    result = safe_supabase_call('smart_grocery_search', {
        'user_query': query,
        'max_budget': budget
    })
    
    if result['success']:
        return result['data']
    
    # Fallback to basic search
    fallback_result = safe_supabase_call('search_cheapest_products', {
        'query': query,
        'max_price': budget or 999
    })
    
    return fallback_result.get('data', [])
```

## Testing Examples

### **Unit Tests**

```python
import pytest

def test_product_discovery():
    """Test product discovery functionality"""
    
    result = supabase.rpc('semantic_product_search', {
        'search_query': 'bread',
        'similarity_threshold': 0.1,
        'max_results': 5
    })
    
    assert result.data is not None
    assert len(result.data) > 0
    assert 'product_id' in result.data[0]

def test_price_optimization():
    """Test price optimization"""
    
    result = supabase.rpc('smart_grocery_search', {
        'user_query': 'milk',
        'max_budget': 5.00
    })
    
    assert result.data is not None
    for item in result.data:
        assert float(item['price']) <= 5.00
```

### **Integration Tests**

```python
def test_full_grocery_workflow():
    """Test complete grocery shopping workflow"""
    
    # Step 1: Search for products
    search_results = supabase.rpc('smart_grocery_search', {
        'user_query': 'breakfast items',
        'max_budget': 20.00
    })
    
    assert len(search_results.data) > 0
    
    # Step 2: Build shopping list
    product_ids = [item['product_id'] for item in search_results.data[:3]]
    
    grocery_list = supabase.rpc('build_grocery_list', {
        'product_ids': product_ids,
        'target_budget': 15.00
    })
    
    assert grocery_list.data is not None
    
    # Step 3: Optimize store selection
    store_optimization = supabase.rpc('suggest_store_split', {
        'product_ids': product_ids
    })
    
    assert store_optimization.data is not None
```

## Performance Considerations

### **Caching Strategy**

```python
import functools
import time

@functools.lru_cache(maxsize=100)
def cached_product_search(query: str, budget: float):
    """Cache frequently requested searches"""
    
    return supabase.rpc('smart_grocery_search', {
        'user_query': query,
        'max_budget': budget
    }).data

# Cache invalidation for price data (prices change frequently)
PRICE_CACHE_TTL = 3600  # 1 hour

price_cache = {}

def get_cached_prices(gtin: str):
    """Get prices with time-based cache"""
    
    now = time.time()
    
    if gtin in price_cache:
        cached_data, timestamp = price_cache[gtin]
        if now - timestamp < PRICE_CACHE_TTL:
            return cached_data
    
    # Fetch fresh data
    fresh_data = supabase.rpc('compare_product_prices', {
        'product_gtin': gtin
    }).data
    
    price_cache[gtin] = (fresh_data, now)
    return fresh_data
```

### **Batch Processing**

```python
def batch_price_comparisons(gtins: List[str]) -> Dict[str, List]:
    """Process multiple price comparisons efficiently"""
    
    results = {}
    
    for gtin in gtins:
        try:
            result = supabase.rpc('compare_product_prices', {
                'product_gtin': gtin
            })
            results[gtin] = result.data
        except Exception as e:
            results[gtin] = {'error': str(e)}
    
    return results
```

## Monitoring and Logging

### **Function Performance Monitoring**

```python
import logging
import time

def monitor_function_performance(func_name: str, params: Dict):
    """Monitor Supabase function performance"""
    
    start_time = time.time()
    
    try:
        result = supabase.rpc(func_name, params)
        execution_time = time.time() - start_time
        
        logging.info(f"Function {func_name} executed in {execution_time:.2f}s")
        
        if execution_time > 2.0:  # Log slow queries
            logging.warning(f"Slow query: {func_name} took {execution_time:.2f}s")
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logging.error(f"Function {func_name} failed after {execution_time:.2f}s: {e}")
        raise
```

## Advanced Features

### **Real Embeddings Upgrade**

When ready for production with OpenAI embeddings:

```python
def upgrade_to_real_embeddings():
    """Upgrade to OpenAI embeddings for better semantic understanding"""
    
    # This requires OPENAI_API_KEY in Supabase
    result = supabase.rpc('upgrade_to_real_embeddings')
    return result.data
```

### **Personalization Support**

```python
def personalized_search(query: str, user_preferences: Dict):
    """Add personalization layer to search"""
    
    # Modify query based on user preferences
    enhanced_query = enhance_query_with_preferences(query, user_preferences)
    
    return supabase.rpc('smart_grocery_search', {
        'user_query': enhanced_query,
        'max_budget': user_preferences.get('budget'),
        'store_preference': user_preferences.get('preferred_store')
    })

def enhance_query_with_preferences(query: str, prefs: Dict) -> str:
    """Enhance query with user dietary preferences"""
    
    dietary_tags = []
    
    if prefs.get('vegetarian'):
        dietary_tags.append('vegetarian')
    if prefs.get('organic'):
        dietary_tags.append('organic biological')
    if prefs.get('low_sodium'):
        dietary_tags.append('low salt')
    
    if dietary_tags:
        return f"{query} {' '.join(dietary_tags)}"
    
    return query
```

## Summary

The AI grocery agent now has access to:

1. **Semantic Understanding**: Find products by meaning, not just keywords
2. **Price Intelligence**: Always return budget-optimized results
3. **Store Optimization**: Suggest the best shopping strategy
4. **Meal Planning**: Complete meal suggestions within budget
5. **Price Trends**: Historical price analysis for smart shopping

All functions are production-ready and scale automatically with Supabase infrastructure. The semantic layer enhances your existing price intelligence without replacing it, creating a truly intelligent grocery shopping assistant. 