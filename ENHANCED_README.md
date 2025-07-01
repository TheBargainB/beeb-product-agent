# Enhanced Product Retrieval Agent with Memory

## 🎯 Overview

This enhanced grocery and meal planning agent combines **product search capabilities** with **persistent memory** to provide personalized assistance for:

- 🛒 **Smart Product Search** - Find Dutch grocery products with prices from Albert Heijn, Jumbo, and Dirk
- 👤 **User Profile Management** - Remember dietary preferences, allergies, and shopping habits
- 📝 **Grocery List Management** - Create and maintain intelligent shopping lists
- 🍽️ **Meal Planning** - Plan meals based on preferences and dietary restrictions
- 💰 **Budget Tracking** - Set and monitor grocery budgets
- 🧠 **Persistent Memory** - Remember user context across conversations

## 🌟 Key Features

### Memory Capabilities
- **User Profiles**: Stores name, location, household size, dietary preferences, allergies, preferred stores
- **Grocery Lists**: Intelligent shopping lists with categories, quantities, estimated prices
- **Meal Plans**: Weekly meal planning with ingredient suggestions
- **Budget Tracking**: Monitor spending against weekly/monthly budgets
- **Shopping History**: Track purchases and spending patterns (framework ready)

### Product Search
- **18,849+ Products** from Dutch grocery database
- **Multi-store Pricing** from Albert Heijn, Dirk, and Jumbo
- **Bilingual Support** with English → Dutch translation hints
- **Smart Search** with retry logic and fallback responses

### Personalization
- **Dietary Restrictions** - Vegetarian, vegan, gluten-free, etc.
- **Allergy Awareness** - Avoid products with allergens
- **Store Preferences** - Prioritize preferred grocery stores
- **Budget Consciousness** - Recommendations within budget constraints

## 🏗️ Architecture

### Memory Store
```
User Memory Structure:
├── profile/
│   └── user_profile (UserProfile schema)
├── grocery_lists/
│   ├── list_id_1 (GroceryItem schema)
│   └── list_id_2 (GroceryItem schema)
├── meal_plans/
│   ├── plan_id_1 (MealPlan schema)
│   └── plan_id_2 (MealPlan schema)
├── budgets/
│   ├── budget_id_1 (Budget schema)
│   └── budget_id_2 (Budget schema)
└── shopping_history/
    ├── history_id_1 (ShoppingHistory schema)
    └── history_id_2 (ShoppingHistory schema)
```

### Enhanced Graph Flow
```
User Input
    ↓
Enhanced Query Generation (with memory context)
    ↓
Route Decision (product search | memory update | direct response)
    ↓
┌─ Product Search ─ Grade Documents ─ Generate Answer
├─ Memory Update ─ Profile/Lists/Plans/Budget
└─ Direct Response ─ Personalized Response
    ↓
Final Response (with updated context)
```

## 🚀 Quick Start

### Installation
```bash
# Install dependencies
pip install trustcall langgraph langchain-openai supabase

# Set environment variables
export OPENAI_API_KEY="your-openai-key"
export SUPABASE_ANON_KEY="your-supabase-key"
export LANGSMITH_API_KEY="your-langsmith-key"  # optional
```

### Basic Usage
```python
from src.agent.graph import create_agent_graph

# Create the enhanced agent
graph = create_agent_graph()

# Configure with user and thread IDs
config = {
    "configurable": {
        "user_id": "user_123",
        "thread_id": "conversation_1"
    }
}

# Use the agent
result = graph.invoke({
    "messages": [{"role": "user", "content": "I'm vegetarian and need meal ideas"}]
}, config)

print(result["messages"][-1].content)
```

## 🧪 Testing

Run comprehensive tests:
```bash
python test_memory_agent.py
```

This tests:
- Memory schema validation
- User profile creation and retrieval
- Grocery list management
- Meal planning functionality
- Budget tracking
- Cross-thread memory persistence
- Product search integration

## 📊 Memory Schemas

### UserProfile
```python
{
    "name": "Sarah",
    "location": "Amsterdam", 
    "household_size": 4,
    "dietary_preferences": ["vegetarian"],
    "allergies": ["nuts"],
    "preferred_stores": ["Albert Heijn", "Jumbo"],
    "cooking_skill_level": "intermediate",
    "favorite_cuisines": ["Italian", "Mediterranean"]
}
```

### GroceryItem
```python
{
    "item_name": "Spinach",
    "quantity": 1,
    "unit": "bag",
    "category": "vegetables",
    "estimated_price": 2.50,
    "store": "Albert Heijn",
    "priority": "high",
    "purchased": false
}
```

### MealPlan
```python
{
    "meal_name": "Vegetarian Pasta",
    "meal_type": "dinner",
    "meal_date": "2024-01-15",
    "servings": 4,
    "prep_time": 20,
    "ingredients": ["pasta", "tomatoes", "basil"],
    "cost_estimate": 8.50
}
```

### Budget
```python
{
    "category": "groceries",
    "amount": 100.0,
    "period": "weekly",
    "spent": 65.0,
    "remaining": 35.0,
    "alert_threshold": 0.8
}
```

## 🎨 Example Conversations

### Setting Up Profile
```
User: "Hi! I'm Sarah, I live in Amsterdam with my family of 4. I'm vegetarian and allergic to nuts."
Agent: "Hi Sarah! Thanks for sharing your details. If you need any vegetarian recipes, meal ideas, or tips for dining out in Amsterdam that accommodate your nut allergy, feel free to ask!"
```

### Grocery Planning
```
User: "I need to buy vegetables for this week - spinach, carrots, and potatoes. Also need some oat milk."
Agent: "Great choices! I'll add these to your grocery list. You can find fresh spinach, carrots, and potatoes at Albert Heijn or Jumbo. For oat milk, most supermarkets carry brands like Oatly or Alpro."
```

### Budget Tracking
```
User: "I want to set a weekly grocery budget of €100 for my family."
Agent: "Your weekly grocery budget of €100 is noted! I'll help you plan meals and shopping lists that fit within this budget."
```

### Meal Planning
```
User: "I want to plan vegetarian pasta for dinner tomorrow and need to buy ingredients."
Agent: "Here's a shopping list for your vegetarian pasta dinner: pasta, olive oil, garlic, bell peppers, zucchini, cherry tomatoes, fresh basil, and parmesan cheese (vegetarian-friendly). This should cost around €12-15 and fits your dietary preferences!"
```

## 🔧 Advanced Configuration

### Custom Memory Types
Extend the system by adding new memory schemas in `src/agent/memory_schemas.py`:

```python
class CustomMemory(BaseModel):
    """Your custom memory schema"""
    # Add your fields here
```

### Memory Management
Use the `MemoryManager` class for advanced memory operations:

```python
from src.agent.memory_tools import MemoryManager

memory_manager = MemoryManager(model)
user_context = memory_manager.format_user_context(store, user_id)
```

## 🤝 Integration with Deployment

The enhanced agent is fully compatible with LangGraph Platform deployment:

```bash
# Deploy to LangGraph Platform
langgraph deploy

# Use deployed endpoint with memory
curl -X POST "https://your-deployment-url/threads" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: YOUR_SECRET_TOKEN" \
  -d '{
    "configurable": {"user_id": "user_123", "thread_id": "conversation_1"},
    "messages": [{"role": "user", "content": "What vegetarian meals can I make with my current grocery list?"}]
  }'
```

## 📈 Performance & Optimizations

- **Database**: Uses optimized `products_optimized` view (54x faster than original queries)
- **Memory**: Efficient storage with Trustcall for smart schema updates
- **Retries**: Intelligent retry logic prevents infinite loops
- **Caching**: Memory context is cached and reused within conversations

## 🛠️ Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install `trustcall` with `pip install trustcall`
2. **Memory Conflicts**: Ensure unique `user_id` for each user
3. **Schema Validation**: Check that memory schemas match expected format
4. **Product Search**: Use Dutch terms or brand names for better results

### Debug Mode
Enable detailed logging:
```python
import os
os.environ["LANGSMITH_TRACING"] = "true"
```

## 🚀 What's Next

Planned enhancements:
- 📱 **Recipe Recommendations** based on available ingredients
- 📊 **Nutrition Tracking** with calorie and macro monitoring  
- 🛍️ **Shopping History Analysis** for spending insights
- 🤖 **Smart Reordering** of frequently purchased items
- 📅 **Calendar Integration** for meal planning

---

**Built with**: LangGraph, OpenAI GPT-4, Supabase, Trustcall, and ❤️ 