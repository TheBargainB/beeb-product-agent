"""Tools for the product retrieval agent."""

import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from .supabase_client import SupabaseClient


# Initialize Supabase client
supabase_client = SupabaseClient()


def format_product_result(product: Dict[str, Any]) -> str:
    """Format a product result for the LLM."""
    # Use optimized view fields - much simpler!
    result = f"Product: {product.get('title', 'N/A')}\n"
    result += f"GTIN: {product.get('gtin', 'N/A')}\n"
    result += f"Description: {product.get('description', 'N/A')}\n"
    
    # Brand and category from optimized view
    if product.get('brand_name'):
        result += f"Brand: {product.get('brand_name')}\n"
    
    if product.get('category_name'):
        result += f"Category: {product.get('category_name')}\n"
    
    if product.get('subcategory_name'):
        result += f"Subcategory: {product.get('subcategory_name')}\n"
    
    # Pricing from optimized view - all stores in one place!
    pricing_info = []
    
    # Albert Heijn pricing
    albert_price = product.get('albert_price')
    if albert_price:
        pricing_info.append(f"Albert Heijn: €{albert_price}")
    
    # Dirk pricing  
    dirk_price = product.get('dirk_price')
    if dirk_price:
        pricing_info.append(f"Dirk: €{dirk_price}")
    
    # Jumbo pricing
    jumbo_price = product.get('jumbo_price')
    if jumbo_price:
        pricing_info.append(f"Jumbo: €{jumbo_price}")
    
    if pricing_info:
        result += f"Prices: {', '.join(pricing_info)}\n"
    
    # Best price if available
    if product.get('best_price') and product.get('best_store'):
        result += f"Best Deal: €{product.get('best_price')} at {product.get('best_store')}\n"
    
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
def search_products(query: str) -> str:
    """
    Search for products in the database using text search.
    Use this tool to find products based on product names, descriptions, or general search terms.
    
    Args:
        query: The search query string
        
    Returns:
        Formatted string containing product information
    """
    try:
        products = supabase_client.search_products(query, limit=10)
        
        if not products:
            return f"No products found for query: {query}"
        
        result = f"Found {len(products)} products for query '{query}':\n\n"
        for product in products:
            result += format_product_result(product)
        
        return result
        
    except Exception as e:
        return f"Error searching products: {e}"


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
    
    Args:
        category: The category name to search within
        
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


# List of all available tools
AVAILABLE_TOOLS = [
    search_products,
    get_product_by_gtin,
    search_products_by_category,
    search_products_by_brand,
] 