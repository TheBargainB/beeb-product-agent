"""Configuration management for the multi-customer agent."""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path


class AgentConfig:
    """Configuration loader and manager for the multi-customer agent."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            # Look for config.yaml in project root
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    # Customer Profile Methods
    def get_crm_profile_id(self) -> str:
        """Get the configured CRM profile ID as string (UUID)."""
        profile_id = self.config.get('customer_profile', {}).get('crm_profile_id')
        if profile_id is None:
            raise ValueError("crm_profile_id must be specified in customer_profile configuration")
        return str(profile_id)
    
    def get_customer_name(self) -> str:
        """Get the customer name."""
        return self.config.get('customer_profile', {}).get('customer_name', 'Unknown Customer')
    
    def get_instance_name(self) -> str:
        """Get the agent instance name."""
        return self.config.get('customer_profile', {}).get('instance_name', 'BargainB Personal Grocery Assistant')
    
    def get_instance_description(self) -> str:
        """Get the agent instance description."""
        return self.config.get('customer_profile', {}).get('instance_description', 'Personal grocery shopping assistant')
    
    def get_default_language(self) -> str:
        """Get the default language."""
        return self.config.get('customer_profile', {}).get('default_language', 'en')
    
    def get_preferred_stores(self) -> List[str]:
        """Get the customer's preferred stores."""
        return self.config.get('customer_profile', {}).get('preferred_stores', ['Albert Heijn'])
    
    def get_default_currency(self) -> str:
        """Get the default currency."""
        return self.config.get('customer_profile', {}).get('default_currency', 'EUR')
    
    def should_validate_profile(self) -> bool:
        """Check if profile validation is enabled."""
        return self.config.get('customer_profile', {}).get('validate_profile_exists', True)
    
    def should_auto_create_profile(self) -> bool:
        """Check if auto profile creation is enabled."""
        return self.config.get('customer_profile', {}).get('auto_create_profile', False)
    
    # Database Methods
    def get_required_tables(self) -> List[str]:
        """Get list of required database tables."""
        return self.config.get('database', {}).get('required_tables', [])
    
    def should_use_supabase_directly(self) -> bool:
        """Check if we should use Supabase directly instead of LangGraph store."""
        return self.config.get('database', {}).get('use_supabase_directly', True)
    
    def is_cross_thread_memory_enabled(self) -> bool:
        """Check if cross-thread memory is enabled."""
        return self.config.get('database', {}).get('enable_cross_thread_memory', True)
    
    # Agent Behavior Methods
    def is_memory_updates_enabled(self) -> bool:
        """Check if memory updates are enabled."""
        return self.config.get('agent', {}).get('enable_memory_updates', True)
    
    def get_memory_update_threshold(self) -> float:
        """Get the confidence threshold for memory updates."""
        return self.config.get('agent', {}).get('memory_update_threshold', 0.7)
    
    def get_default_search_limit(self) -> int:
        """Get default search limit for product queries."""
        return self.config.get('agent', {}).get('default_search_limit', 10)
    
    def is_pricing_data_enabled(self) -> bool:
        """Check if pricing data inclusion is enabled."""
        return self.config.get('agent', {}).get('enable_pricing_data', True)
    
    def is_price_comparison_enabled(self) -> bool:
        """Check if price comparison across stores is enabled."""
        return self.config.get('agent', {}).get('price_comparison_enabled', True)
    
    def is_personalized_recommendations_enabled(self) -> bool:
        """Check if personalized recommendations are enabled."""
        return self.config.get('agent', {}).get('enable_personalized_recommendations', True)
    
    def should_consider_dietary_restrictions(self) -> bool:
        """Check if dietary restrictions should be considered."""
        return self.config.get('agent', {}).get('consider_dietary_restrictions', True)
    
    def should_consider_budget_constraints(self) -> bool:
        """Check if budget constraints should be considered."""
        return self.config.get('agent', {}).get('consider_budget_constraints', True)
    
    def should_suggest_alternatives(self) -> bool:
        """Check if alternative suggestions are enabled."""
        return self.config.get('agent', {}).get('suggest_alternatives', True)
    
    def get_max_response_length(self) -> int:
        """Get maximum response length."""
        return self.config.get('agent', {}).get('max_response_length', 2000)
    
    def should_include_price_estimates(self) -> bool:
        """Check if price estimates should be included."""
        return self.config.get('agent', {}).get('include_price_estimates', True)
    
    def should_suggest_recipes_for_ingredients(self) -> bool:
        """Check if recipe suggestions for ingredients are enabled."""
        return self.config.get('agent', {}).get('suggest_recipes_for_ingredients', True)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.config.get('agent', {}).get('supported_languages', ['Dutch', 'English'])
    
    # Deployment Methods
    def get_environment(self) -> str:
        """Get the deployment environment."""
        return self.config.get('deployment', {}).get('environment', 'local')
    
    def is_customer_isolation_enabled(self) -> bool:
        """Check if customer data isolation is enabled."""
        return self.config.get('deployment', {}).get('enable_customer_isolation', True)
    
    def should_log_customer_interactions(self) -> bool:
        """Check if customer interactions should be logged."""
        return self.config.get('deployment', {}).get('log_customer_interactions', True)
    
    def is_cache_enabled(self) -> bool:
        """Check if product search caching is enabled."""
        return self.config.get('deployment', {}).get('cache_product_searches', True)
    
    def get_cache_duration_minutes(self) -> int:
        """Get cache duration in minutes."""
        return self.config.get('deployment', {}).get('cache_duration_minutes', 30)
    
    def should_validate_database_operations(self) -> bool:
        """Check if database operation validation is enabled."""
        return self.config.get('deployment', {}).get('validate_all_database_operations', True)
    
    def is_query_logging_enabled(self) -> bool:
        """Check if query logging is enabled."""
        return self.config.get('deployment', {}).get('enable_query_logging', False)
    
    # Local Development Methods
    def should_use_local_supabase(self) -> bool:
        """Check if local Supabase should be used."""
        return self.config.get('local_development', {}).get('use_local_supabase', False)
    
    def get_local_db_url(self) -> Optional[str]:
        """Get local database URL."""
        return self.config.get('local_development', {}).get('local_db_url')
    
    def get_test_customer_profile_id(self) -> str:
        """Get test customer profile ID."""
        return self.config.get('local_development', {}).get('test_customer_profile_id', self.get_crm_profile_id())
    
    def is_debug_logging_enabled(self) -> bool:
        """Check if debug logging is enabled."""
        return self.config.get('local_development', {}).get('enable_debug_logging', False)
    
    def should_simulate_slow_responses(self) -> bool:
        """Check if slow response simulation is enabled."""
        return self.config.get('local_development', {}).get('simulate_slow_responses', False)
    
    def should_use_mock_pricing_data(self) -> bool:
        """Check if mock pricing data should be used."""
        return self.config.get('local_development', {}).get('use_mock_pricing_data', False)
    
    def should_use_mock_customer_data(self) -> bool:
        """Check if mock customer data should be used."""
        return self.config.get('local_development', {}).get('mock_customer_data', False)
    
    # Guard Rails Methods
    def are_guard_rails_enabled(self) -> bool:
        """Check if guard rails are enabled."""
        return self.config.get('guard_rails', {}).get('rate_limiting', {}).get('enabled', False)
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return self.config.get('guard_rails', {}).get('rate_limiting', {})
    
    def get_content_safety_config(self) -> Dict[str, Any]:
        """Get content safety configuration."""
        return self.config.get('guard_rails', {}).get('content_safety', {})
    
    def get_cost_control_config(self) -> Dict[str, Any]:
        """Get cost control configuration."""
        return self.config.get('guard_rails', {}).get('cost_controls', {})
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """Get error handling configuration."""
        return self.config.get('guard_rails', {}).get('error_handling', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.config.get('guard_rails', {}).get('monitoring', {})
    
    def is_graceful_degradation_enabled(self) -> bool:
        """Check if graceful degradation is enabled."""
        return self.config.get('guard_rails', {}).get('error_handling', {}).get('graceful_degradation', False)

    # Validation and Summary Methods
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate the current configuration and return status."""
        validation_results = {
            'config_file_exists': self.config_path.exists(),
            'has_crm_profile_id': 'customer_profile' in self.config and 'crm_profile_id' in self.config['customer_profile'],
            'profile_id_is_valid': False,
            'has_required_sections': True,
            'has_valid_environment': False,
            'has_valid_stores': False
        }
        
        # Check if profile ID is valid (not empty, looks like UUID)
        try:
            profile_id = self.get_crm_profile_id()
            validation_results['profile_id_is_valid'] = len(profile_id) > 0
        except (ValueError, TypeError):
            validation_results['profile_id_is_valid'] = False
        
        # Check required sections exist
        required_sections = ['customer_profile', 'database', 'agent', 'deployment']
        for section in required_sections:
            if section not in self.config:
                validation_results['has_required_sections'] = False
                break
        
        # Check valid environment
        valid_environments = ['local', 'staging', 'production']
        validation_results['has_valid_environment'] = self.get_environment() in valid_environments
        
        # Check valid stores
        preferred_stores = self.get_preferred_stores()
        valid_stores = ['Albert Heijn', 'Jumbo', 'Dirk']
        validation_results['has_valid_stores'] = all(store in valid_stores for store in preferred_stores)
        
        return validation_results
    
    def get_config_summary(self) -> str:
        """Get a human-readable summary of the current configuration."""
        try:
            profile_id = self.get_crm_profile_id()
            customer_name = self.get_customer_name()
            instance_name = self.get_instance_name()
            environment = self.get_environment()
            preferred_stores = ', '.join(self.get_preferred_stores())
            validation = self.validate_configuration()
            
            summary = f"""
Multi-Customer Agent Configuration Summary:
==========================================
Customer: {customer_name}
Instance: {instance_name}
Environment: {environment}
CRM Profile ID: {profile_id}
Preferred Stores: {preferred_stores}
Default Language: {self.get_default_language()}
Config File: {self.config_path}

Features:
- Memory Updates: {'Enabled' if self.is_memory_updates_enabled() else 'Disabled'}
- Pricing Data: {'Enabled' if self.is_pricing_data_enabled() else 'Disabled'}
- Price Comparison: {'Enabled' if self.is_price_comparison_enabled() else 'Disabled'}
- Personalized Recommendations: {'Enabled' if self.is_personalized_recommendations_enabled() else 'Disabled'}
- Dietary Restrictions: {'Considered' if self.should_consider_dietary_restrictions() else 'Ignored'}
- Budget Constraints: {'Considered' if self.should_consider_budget_constraints() else 'Ignored'}

Configuration Status: {'Valid' if all(validation.values()) else 'Invalid'}
"""
            return summary.strip()
        except Exception as e:
            return f"Configuration Error: {e}"


# Global config instance
_config_instance = None

def get_config() -> AgentConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AgentConfig()
    return _config_instance

def reload_config() -> AgentConfig:
    """Reload the configuration from file."""
    global _config_instance
    _config_instance = AgentConfig()
    return _config_instance

def create_customer_config(customer_profile_id: str, customer_name: str, output_path: str) -> str:
    """Create a new customer-specific configuration file."""
    config_template = {
        'customer_profile': {
            'crm_profile_id': customer_profile_id,
            'customer_name': customer_name,
            'instance_name': f'{customer_name} Personal Grocery Assistant',
            'instance_description': f'Personal grocery shopping and meal planning assistant for {customer_name}',
            'default_language': 'en',
            'preferred_stores': ['Albert Heijn'],
            'default_currency': 'EUR',
            'validate_profile_exists': True,
            'auto_create_profile': False
        },
        'database': {
            'required_tables': [
                'crm_profiles', 'grocery_lists', 'recipes', 'meal_plans',
                'budget_periods', 'budget_categories', 'budget_expenses',
                'repo_products', 'albert_prices', 'jumbo_prices', 'dirk_prices'
            ],
            'use_supabase_directly': True,
            'enable_cross_thread_memory': True
        },
        'agent': {
            'enable_memory_updates': True,
            'memory_update_threshold': 0.7,
            'default_search_limit': 10,
            'enable_pricing_data': True,
            'price_comparison_enabled': True,
            'enable_personalized_recommendations': True,
            'consider_dietary_restrictions': True,
            'consider_budget_constraints': True,
            'suggest_alternatives': True,
            'max_response_length': 2000,
            'include_price_estimates': True,
            'suggest_recipes_for_ingredients': True,
            'supported_languages': ['Dutch', 'English']
        },
        'deployment': {
            'environment': 'production',
            'enable_customer_isolation': True,
            'log_customer_interactions': True,
            'cache_product_searches': True,
            'cache_duration_minutes': 30,
            'validate_all_database_operations': True,
            'enable_query_logging': False
        },
        'local_development': {
            'use_local_supabase': False,
            'local_db_url': None,
            'test_customer_profile_id': customer_profile_id,
            'enable_debug_logging': False,
            'simulate_slow_responses': False,
            'use_mock_pricing_data': False,
            'mock_customer_data': False
        }
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(config_template, f, default_flow_style=False)
    
    return f"Customer configuration created: {output_path}" 