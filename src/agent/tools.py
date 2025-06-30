"""Tools for the product retrieval agent."""

import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from .supabase_client import SupabaseClient


# Initialize Supabase client
supabase_client = SupabaseClient()


def format_product_result(product: Dict[str, Any]) -> str:
    """Format a product result for the LLM."""
    # Try both 'name' and 'title' fields for product name
    product_name = product.get('name') or product.get('title', 'N/A')
    result = f"Product: {product_name}\n"
    result += f"GTIN: {product.get('gtin', 'N/A')}\n"
    result += f"Description: {product.get('description', 'N/A')}\n"
    
    # Add category information from direct relationship
    if product.get('categories'):
        category = product['categories']
        if isinstance(category, dict):
            result += f"Category: {category.get('name', 'N/A')}\n"
    
    # Add pricing information if available
    pricing_info = []
    if product.get('albert'):
        albert = product['albert']
        price = albert.get('price_per_unit', albert.get('price'))
        if price:
            pricing_info.append(f"Albert Heijn: €{price}")
    
    if product.get('jumbo'):
        jumbo = product['jumbo']
        price = jumbo.get('price_per_unit', jumbo.get('price'))
        brand = jumbo.get('brand_name')
        if price:
            pricing_info.append(f"Jumbo: €{price}")
        if brand:
            result += f"Brand: {brand}\n"
    
    if product.get('dirk'):
        dirk = product['dirk']
        price = dirk.get('price_per_unit', dirk.get('price'))
        if price:
            pricing_info.append(f"Dirk: €{price}")
    
    if pricing_info:
        result += f"Prices: {', '.join(pricing_info)}\n"
    
    # Legacy support for repo_* tables
    if product.get('repo_brands'):
        brand = product['repo_brands']
        result += f"Brand: {brand.get('name', 'N/A')}\n"
    
    if product.get('repo_categories'):
        category = product['repo_categories']
        result += f"Category: {category.get('name', 'N/A')}\n"
    
    if product.get('repo_subcategories'):
        subcategory = product['repo_subcategories']
        result += f"Subcategory: {subcategory.get('name', 'N/A')}\n"
    
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