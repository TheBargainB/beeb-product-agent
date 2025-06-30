"""Supabase client configuration for the retrieval agent."""

import os
from supabase import create_client, Client
from typing import List, Dict, Any


class SupabaseClient:
    """Client for interacting with Supabase product database."""
    
    def __init__(self):
        """Initialize the Supabase client."""
        self.url = os.getenv("SUPABASE_URL", "https://oumhprsxyxnocgbzosvh.supabase.co")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.key:
            raise ValueError("SUPABASE_ANON_KEY environment variable is required")
        
        self.client: Client = create_client(self.url, self.key)
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search products using text search across multiple fields.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries with pricing info
        """
        try:
            # Search across product name and get category info
            response = (
                self.client
                .from_("products")
                .select("""
                    *,
                    categories(*)
                """)
                .ilike("name", f"%{query}%")
                .limit(limit)
                .execute()
            )
            
            if response.data:
                # Enrich with pricing data
                enriched_products = []
                for product in response.data:
                    enriched_product = self._enrich_with_pricing(product)
                    enriched_products.append(enriched_product)
                return enriched_products
            else:
                print(f"No products found for query: {query}")
                return []
            
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    def get_product_by_gtin(self, gtin: str) -> Dict[str, Any] | None:
        """
        Get a specific product by GTIN.
        
        Args:
            gtin: Product GTIN
            
        Returns:
            Product dictionary with pricing info or None if not found
        """
        try:
            response = (
                self.client
                .from_("products")
                .select("""
                    *,
                    categories(*)
                """)
                .eq("gtin", gtin)
                .single()
                .execute()
            )
            
            if response.data:
                return self._enrich_with_pricing(response.data)
            else:
                print(f"No product found with GTIN: {gtin}")
                return None
            
        except Exception as e:
            print(f"Error fetching product {gtin}: {e}")
            return None
    
    def search_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search products by category name.
        
        Args:
            category: Category name
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        try:
            # Find category ID(s) matching the name
            category_response = (
                self.client
                .from_("categories")
                .select("id")
                .ilike("name", f"%{category}%")
                .execute()
            )
            
            if not category_response.data:
                print(f"No category found matching: {category}")
                return []
            
            category_ids = [cat["id"] for cat in category_response.data]
            
            # Get products with these categories
            response = (
                self.client
                .from_("products")
                .select("""
                    *,
                    categories(*)
                """)
                .in_("category_id", category_ids)
                .limit(limit)
                .execute()
            )
            
            if response.data:
                enriched_products = []
                for product in response.data:
                    enriched_product = self._enrich_with_pricing(product)
                    enriched_products.append(enriched_product)
                return enriched_products
            else:
                return []
            
        except Exception as e:
            print(f"Error searching by category {category}: {e}")
            return []
    
    def search_by_brand(self, brand: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search products by brand name in the pricing tables.
        
        Args:
            brand: Brand name
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        try:
            # Search for brand in jumbo_prices which has brand_name
            brand_response = (
                self.client
                .from_("jumbo_prices")
                .select("gtin")
                .ilike("brand_name", f"%{brand}%")
                .limit(limit * 2)  # Get more GTINs to account for duplicates
                .execute()
            )
            
            if not brand_response.data:
                print(f"No brand found matching: {brand}")
                return []
            
            # Get unique GTINs
            gtins = list(set(price["gtin"] for price in brand_response.data))[:limit]
            
            # Get products with these GTINs
            response = (
                self.client
                .from_("products")
                .select("""
                    *,
                    categories(*)
                """)
                .in_("gtin", gtins)
                .limit(limit)
                .execute()
            )
            
            if response.data:
                enriched_products = []
                for product in response.data:
                    enriched_product = self._enrich_with_pricing(product)
                    enriched_products.append(enriched_product)
                return enriched_products
            else:
                return []
            
        except Exception as e:
            print(f"Error searching by brand {brand}: {e}")
            return []
    
    def _enrich_with_pricing(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a product with pricing information from various stores.
        
        Args:
            product: Base product dictionary
            
        Returns:
            Enhanced product dictionary with pricing info
        """
        gtin = product.get("gtin")
        if not gtin:
            return product
        
        # Try to get pricing from each store
        stores = ["albert_prices", "dirk_prices", "jumbo_prices"]
        pricing_info = {}
        
        for store in stores:
            try:
                store_response = (
                    self.client
                    .from_(store)
                    .select("*")
                    .eq("gtin", gtin)
                    .limit(1)
                    .execute()
                )
                
                if store_response.data:
                    pricing_info[store.replace("_prices", "")] = store_response.data[0]
                    
            except Exception as e:
                # Continue if one store fails
                pass
        
        # Add pricing info to product
        if pricing_info:
            product["pricing"] = pricing_info
            
            # Extract brand info if available
            for store_data in pricing_info.values():
                if "brand_name" in store_data and store_data["brand_name"]:
                    product["brand_name"] = store_data["brand_name"]
                    break
                elif "store_product_name" in store_data:
                    # Try to extract brand from product name
                    name = store_data["store_product_name"]
                    if name:
                        product["full_product_name"] = name
                    break
        
        return product
    
    def test_connection(self) -> bool:
        """
        Test the database connection and schema.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test basic connection by getting a few products
            response = (
                self.client
                .from_("products")
                .select("id, name")
                .limit(1)
                .execute()
            )
            
            if response.data:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed: No data returned")
                return False
                
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False 