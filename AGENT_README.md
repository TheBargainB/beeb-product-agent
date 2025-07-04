# Product Retrieval Agent

A LangGraph-based retrieval agent that can search and answer questions about products in your Supabase database. This agent is built following the agentic RAG pattern and adapted to work with your product data in the `repo_` tables.

## Features

- **Intelligent Product Search**: Searches across product titles, descriptions, brands, and categories
- **Multiple Search Methods**: 
  - General text search
  - Search by specific GTIN
  - Search by category
  - Search by brand
- **Document Grading**: Evaluates whether retrieved product information is relevant to the user's question
- **Question Rewriting**: Automatically improves queries that don't return relevant results
- **Contextual Responses**: Provides detailed product information including brands, categories, packaging, and attributes

## Architecture

The agent follows the agentic RAG pattern with these components:

1. **Query Generation**: Decides whether to search for products or respond directly
2. **Product Retrieval**: Uses multiple tools to search the Supabase database
3. **Relevance Grading**: Evaluates if retrieved products answer the user's question
4. **Question Rewriting**: Improves queries that don't return relevant results
5. **Answer Generation**: Creates helpful responses based on product data

## Setup

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Environment Variables

Create a `.env` file in the project root with:

```bash
# OpenAI API Key (from your account)
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith API Key (optional, for tracing)
LANGSMITH_API_KEY=your_langsmith_api_key_here

# Supabase Configuration
SUPABASE_URL=https://oumhprsxyxnocgbzosvh.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

The Supabase keys are available in your `supabase.md` file.

### 3. Configuration Architecture

The agent uses a **multi-customer architecture** where the same codebase serves multiple customers:

#### General Configuration (config.yaml)
```yaml
customer_profile:
  crm_profile_id: null  # Always null - customer ID comes from runtime
```
- The YAML config contains general settings only
- No customer-specific data is hardcoded
- Same config is used for all customers

#### Runtime Customer Configuration
Customer profile IDs are passed when creating/using assistants:

```python
# Example: Running agent with customer-specific profile
config = {
    "configurable": {
        "user_id": "user_123",
        "customer_profile_id": "uuid-of-customer-from-database"
    }
}

result = graph.invoke({
    "messages": [{"role": "user", "content": "What products do you have?"}]
}, config)
```

**Benefits:**
- ✅ One codebase serves multiple customers
- ✅ Customer-specific memory and personalization
- ✅ No hardcoded customer data
- ✅ Easy to scale to new customers

### 4. Test the Setup

```bash
python test_agent.py
```

This will verify your environment setup and test basic functionality.

## Usage

### Basic Usage

```python
from src.agent import run_agent

# Ask about products
response = run_agent("What dairy products do you have?")
print(response)

# Search by brand
response = run_agent("Show me AH products")
print(response)

# Search by category
response = run_agent("Find bread products")
print(response)

# Get specific product
response = run_agent("Tell me about product with GTIN 1234567890123")
print(response)
```

### Using the Graph Directly

```python
from src.agent import graph

# Stream responses for real-time updates
for chunk in graph.stream({
    "messages": [{"role": "user", "content": "What products do you have?"}]
}):
    for node, update in chunk.items():
        print(f"Update from {node}:")
        print(update["messages"][-1].content)
```

### LangGraph Studio

Start the development server:

```bash
langgraph dev
```

Then open LangGraph Studio in your browser to interact with the agent visually.

## Available Tools

The agent has access to these product search tools:

1. **`search_products`**: General text search across product names and descriptions
2. **`get_product_by_gtin`**: Get specific product details by GTIN
3. **`search_products_by_category`**: Find products in a specific category
4. **`search_products_by_brand`**: Find products from a specific brand

## Example Queries

- "What dairy products do you have?"
- "Show me products from AH brand"
- "Find me some bread options"
- "What's the price of product GTIN 1234567890123?"
- "Do you have any organic products?"
- "Show me products in the beverages category"

## Database Schema

The agent works with these Supabase tables:

- **`repo_products`**: Main product information (title, description, GTIN, image)
- **`repo_brands`**: Brand information
- **`repo_categories`**: Product categories
- **`repo_subcategories`**: Product subcategories  
- **`repo_packaging`**: Unit amounts, quantities, packaging details
- **`repo_product_attributes`**: Product attributes (type, flavor, size, etc.)

## Customization

### Adding New Tools

Add new search methods in `src/agent/tools.py`:

```python
@tool
def search_by_price_range(min_price: float, max_price: float) -> str:
    """Search products within a price range."""
    # Implementation here
    pass
```

### Modifying Prompts

Update the prompts in `src/agent/nodes.py` to change how the agent interprets and responds to queries.

### Changing Models

Modify the model initialization in `src/agent/nodes.py`:

```python
# Use a different OpenAI model
response_model = init_chat_model("openai:gpt-4", temperature=0)

# Or use a different provider
response_model = init_chat_model("anthropic:claude-3-sonnet", temperature=0)
```

## Troubleshooting

### Common Issues

1. **Environment Variables**: Make sure all required variables are set in `.env`
2. **Supabase Connection**: Verify your Supabase keys and URL are correct
3. **Product Data**: Ensure your product data is uploaded to the `repo_` tables
4. **OpenAI API**: Check your OpenAI API key and account credits

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Specific Components

Test individual components:

```python
# Test Supabase connection
from src.agent.supabase_client import SupabaseClient
client = SupabaseClient()
products = client.search_products("bread")
print(products)

# Test tools
from src.agent.tools import search_products
result = search_products.invoke({"query": "milk"})
print(result)
```

## Next Steps

1. **Enhanced Search**: Add semantic search using embeddings
2. **Price Integration**: Include pricing information from your data
3. **Image Analysis**: Add image-based product search
4. **Conversation Memory**: Maintain context across multiple queries
5. **Recommendation Engine**: Suggest related products

## Support

For issues or questions:
1. Check the `test_agent.py` output for diagnostics
2. Review the LangGraph documentation
3. Verify your Supabase data structure matches expectations 