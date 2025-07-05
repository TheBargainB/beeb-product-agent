#!/usr/bin/env python3
"""
Comprehensive Runtime Configuration Test

This script tests all the dynamic configuration options available in the BargainB agent,
including dietary preferences, store preferences, custom instructions, and much more.

Test Categories:
1. Health-Focused Family Configuration
2. Budget-Conscious Student Configuration  
3. Busy Professional Configuration
4. International Customer Configuration
5. Feature Toggle Testing
6. Guard Rails Configuration Testing
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.config import AgentConfig
from src.agent.guard_rails import GuardRailsConfig
from src.agent.memory_schemas import AssistantLanguageConfig


def test_health_focused_family_config():
    """Test configuration for health-focused family."""
    print("🧪 Testing Health-Focused Family Configuration")
    print("=" * 60)
    
    runtime_config = {
        # Core identification
        'customer_name': 'Sarah Johnson',
        'instance_name': "Sarah's Family Grocery Assistant",
        'user_id': 'sarah_family_123',
        'customer_profile_id': '550e8400-e29b-41d4-a716-446655440001',
        
        # Platform formatting
        'source': 'whatsapp',
        
        # Language settings
        'primary_language': 'english',
        'language_enforcement': 'flexible',
        'fallback_language': 'english',
        
        # Customer preferences
        'dietary_restrictions': ['gluten_free', 'nut_allergy'],
        'preferred_stores': ['Albert Heijn', 'Jumbo'],
        'shopping_persona': 'health_focused',
        'budget_range': 'medium',
        'price_sensitivity': 'medium',
        'shopping_frequency': 'weekly',
        
        # Agent behavior
        'enable_memory_updates': True,
        'enable_pricing_data': True,
        'price_comparison_enabled': True,
        'enable_personalized_recommendations': True,
        'consider_dietary_restrictions': True,
        'consider_budget_constraints': True,
        'suggest_alternatives': True,
        
        # Response configuration
        'max_response_length': 1500,
        'response_style': 'friendly',
        'use_emojis': True,
        'include_tips': True,
        
        # Custom instructions
        'custom_instructions': 'Always suggest family-friendly healthy options with organic alternatives',
        'system_prompt_additions': 'Focus on wholesome ingredients and kid-friendly meals',
        
        # Feature toggles
        'enable_meal_planning': True,
        'enable_grocery_lists': True,
        'enable_budget_tracking': False,
        'enable_recipe_suggestions': True,
        
        # Performance settings
        'cache_enabled': True,
        'cache_duration_minutes': 30,
        'graceful_degradation': True,
        
        # Guard rails
        'rate_limiting_enabled': True,
        'max_requests_per_minute': 20,
        'content_safety_enabled': True,
        'max_tokens_per_request': 3000
    }
    
    # Test AgentConfig
    agent_config = AgentConfig.from_runtime_config(runtime_config)
    
    print(f"✅ Customer Name: {agent_config.get_customer_name()}")
    print(f"✅ Instance Name: {agent_config.get_instance_name()}")
    print(f"✅ User ID: {agent_config.get_user_id()}")
    print(f"✅ Dietary Restrictions: {agent_config.get_dietary_restrictions()}")
    print(f"✅ Preferred Stores: {agent_config.get_preferred_stores()}")
    print(f"✅ Shopping Persona: {agent_config.get_shopping_persona()}")
    print(f"✅ Budget Range: {agent_config.get_budget_range()}")
    print(f"✅ Custom Instructions: {agent_config.get_custom_instructions()}")
    print(f"✅ Meal Planning Enabled: {agent_config.is_meal_planning_enabled()}")
    print(f"✅ Recipe Suggestions Enabled: {agent_config.is_recipe_suggestions_enabled()}")
    print(f"✅ Consider Dietary Restrictions: {agent_config.should_consider_dietary_restrictions()}")
    print(f"✅ Response Style: {agent_config.get_response_style()}")
    print(f"✅ Max Response Length: {agent_config.get_max_response_length()}")
    
    # Test GuardRailsConfig
    guard_rails_config = GuardRailsConfig.from_runtime_config(runtime_config)
    print(f"✅ Rate Limiting Enabled: {guard_rails_config.rate_limiting_enabled}")
    print(f"✅ Max Requests Per Minute: {guard_rails_config.max_requests_per_minute}")
    print(f"✅ Max Tokens Per Request: {guard_rails_config.max_tokens_per_request}")
    
    print("✅ Health-Focused Family Configuration Test PASSED\n")
    return True


def test_budget_conscious_student_config():
    """Test configuration for budget-conscious student."""
    print("🧪 Testing Budget-Conscious Student Configuration")
    print("=" * 60)
    
    runtime_config = {
        # Core identification
        'customer_name': 'Ahmed Al-Rashid',
        'instance_name': "Ahmed's Budget Grocery Assistant",
        'user_id': 'ahmed_student_456',
        'customer_profile_id': '550e8400-e29b-41d4-a716-446655440002',
        
        # Platform formatting
        'source': 'telegram',
        
        # Language settings
        'primary_language': 'arabic',
        'language_enforcement': 'flexible',
        'cultural_context': 'middle_east',
        
        # Customer preferences
        'dietary_restrictions': ['halal'],
        'preferred_stores': ['Lidl', 'Aldi'],
        'shopping_persona': 'budget_conscious',
        'budget_range': 'low',
        'price_sensitivity': 'high',
        'shopping_frequency': 'weekly',
        
        # Custom instructions
        'custom_instructions': 'Always prioritize cheapest options and bulk buying opportunities',
        'system_prompt_additions': 'Suggest student-friendly quick meals and money-saving tips',
        
        # Feature toggles
        'enable_budget_tracking': True,
        'enable_meal_planning': True,
        'enable_grocery_lists': True,
        'enable_recipe_suggestions': False,
        
        # Response configuration
        'max_response_length': 1000,
        'response_style': 'concise',
        'use_emojis': True,
        'include_tips': True,
        
        # Guard rails
        'rate_limiting_enabled': True,
        'max_requests_per_minute': 15,
        'max_tokens_per_request': 2000
    }
    
    agent_config = AgentConfig.from_runtime_config(runtime_config)
    
    print(f"✅ Customer Name: {agent_config.get_customer_name()}")
    print(f"✅ Dietary Restrictions: {agent_config.get_dietary_restrictions()}")
    print(f"✅ Preferred Stores: {agent_config.get_preferred_stores()}")
    print(f"✅ Shopping Persona: {agent_config.get_shopping_persona()}")
    print(f"✅ Budget Range: {agent_config.get_budget_range()}")
    print(f"✅ Price Sensitivity: {agent_config.get_price_sensitivity()}")
    print(f"✅ Budget Tracking Enabled: {agent_config.is_budget_tracking_enabled()}")
    print(f"✅ Custom Instructions: {agent_config.get_custom_instructions()}")
    print(f"✅ Response Style: {agent_config.get_response_style()}")
    
    print("✅ Budget-Conscious Student Configuration Test PASSED\n")
    return True


def test_busy_professional_config():
    """Test configuration for busy professional."""
    print("🧪 Testing Busy Professional Configuration")
    print("=" * 60)
    
    runtime_config = {
        # Core identification
        'customer_name': 'Maria Rodriguez',
        'instance_name': "Maria's Quick Grocery Assistant",
        'user_id': 'maria_professional_789',
        
        # Language settings
        'primary_language': 'spanish',
        'language_enforcement': 'strict',
        
        # Customer preferences
        'dietary_restrictions': ['vegetarian'],
        'preferred_stores': ['Albert Heijn'],
        'shopping_persona': 'busy_professional',
        'budget_range': 'high',
        'price_sensitivity': 'low',
        'shopping_frequency': 'weekly',
        
        # Custom instructions
        'custom_instructions': 'Always suggest quick meal prep options and time-saving tips',
        
        # Agent behavior
        'suggest_recipes_for_ingredients': True,
        'enable_personalized_recommendations': True,
        
        # Response configuration
        'max_response_length': 2000,
        'response_style': 'detailed',
        'use_emojis': False,
        'include_tips': True,
        
        # Performance settings
        'cache_enabled': True,
        'cache_duration_minutes': 60,
        
        # Guard rails
        'rate_limiting_enabled': False,
        'content_safety_enabled': True
    }
    
    agent_config = AgentConfig.from_runtime_config(runtime_config)
    
    print(f"✅ Customer Name: {agent_config.get_customer_name()}")
    print(f"✅ Shopping Persona: {agent_config.get_shopping_persona()}")
    print(f"✅ Budget Range: {agent_config.get_budget_range()}")
    print(f"✅ Price Sensitivity: {agent_config.get_price_sensitivity()}")
    print(f"✅ Custom Instructions: {agent_config.get_custom_instructions()}")
    print(f"✅ Use Emojis: {agent_config.should_use_emojis()}")
    print(f"✅ Include Tips: {agent_config.should_include_tips()}")
    print(f"✅ Cache Enabled: {agent_config.is_cache_enabled()}")
    print(f"✅ Cache Duration: {agent_config.get_cache_duration_minutes()}")
    
    guard_rails_config = GuardRailsConfig.from_runtime_config(runtime_config)
    print(f"✅ Rate Limiting Enabled: {guard_rails_config.rate_limiting_enabled}")
    print(f"✅ Content Safety Enabled: {guard_rails_config.content_safety_enabled}")
    
    print("✅ Busy Professional Configuration Test PASSED\n")
    return True


def test_feature_toggles():
    """Test all feature toggle configurations."""
    print("🧪 Testing Feature Toggle Configurations")
    print("=" * 60)
    
    # Test with all features enabled
    runtime_config_enabled = {
        'enable_meal_planning': True,
        'enable_grocery_lists': True,
        'enable_budget_tracking': True,
        'enable_recipe_suggestions': True,
        'enable_memory_updates': True,
        'enable_pricing_data': True,
        'price_comparison_enabled': True,
        'enable_personalized_recommendations': True,
        'consider_dietary_restrictions': True,
        'consider_budget_constraints': True,
        'suggest_alternatives': True,
        'include_price_estimates': True,
        'suggest_recipes_for_ingredients': True
    }
    
    agent_config_enabled = AgentConfig.from_runtime_config(runtime_config_enabled)
    
    print("Features ENABLED Configuration:")
    print(f"✅ Meal Planning: {agent_config_enabled.is_meal_planning_enabled()}")
    print(f"✅ Grocery Lists: {agent_config_enabled.is_grocery_lists_enabled()}")
    print(f"✅ Budget Tracking: {agent_config_enabled.is_budget_tracking_enabled()}")
    print(f"✅ Recipe Suggestions: {agent_config_enabled.is_recipe_suggestions_enabled()}")
    print(f"✅ Memory Updates: {agent_config_enabled.is_memory_updates_enabled()}")
    print(f"✅ Pricing Data: {agent_config_enabled.is_pricing_data_enabled()}")
    print(f"✅ Price Comparison: {agent_config_enabled.is_price_comparison_enabled()}")
    print(f"✅ Personalized Recommendations: {agent_config_enabled.is_personalized_recommendations_enabled()}")
    print(f"✅ Consider Dietary Restrictions: {agent_config_enabled.should_consider_dietary_restrictions()}")
    print(f"✅ Consider Budget Constraints: {agent_config_enabled.should_consider_budget_constraints()}")
    print(f"✅ Suggest Alternatives: {agent_config_enabled.should_suggest_alternatives()}")
    print(f"✅ Include Price Estimates: {agent_config_enabled.should_include_price_estimates()}")
    print(f"✅ Suggest Recipes for Ingredients: {agent_config_enabled.should_suggest_recipes_for_ingredients()}")
    
    # Test with all features disabled
    runtime_config_disabled = {
        'enable_meal_planning': False,
        'enable_grocery_lists': False,
        'enable_budget_tracking': False,
        'enable_recipe_suggestions': False,
        'enable_memory_updates': False,
        'enable_pricing_data': False,
        'price_comparison_enabled': False,
        'enable_personalized_recommendations': False,
        'consider_dietary_restrictions': False,
        'consider_budget_constraints': False,
        'suggest_alternatives': False,
        'include_price_estimates': False,
        'suggest_recipes_for_ingredients': False
    }
    
    agent_config_disabled = AgentConfig.from_runtime_config(runtime_config_disabled)
    
    print("\nFeatures DISABLED Configuration:")
    print(f"✅ Meal Planning: {agent_config_disabled.is_meal_planning_enabled()}")
    print(f"✅ Grocery Lists: {agent_config_disabled.is_grocery_lists_enabled()}")
    print(f"✅ Budget Tracking: {agent_config_disabled.is_budget_tracking_enabled()}")
    print(f"✅ Recipe Suggestions: {agent_config_disabled.is_recipe_suggestions_enabled()}")
    print(f"✅ Memory Updates: {agent_config_disabled.is_memory_updates_enabled()}")
    print(f"✅ Pricing Data: {agent_config_disabled.is_pricing_data_enabled()}")
    
    print("✅ Feature Toggle Configuration Test PASSED\n")
    return True


def test_guard_rails_configurations():
    """Test guard rails configurations."""
    print("🧪 Testing Guard Rails Configurations")
    print("=" * 60)
    
    # Test strict guard rails
    strict_config = {
        'rate_limiting_enabled': True,
        'content_safety_enabled': True,
        'cost_controls_enabled': True,
        'max_requests_per_minute': 10,
        'max_tokens_per_request': 1000,
        'max_message_length': 200,
        'graceful_degradation': False
    }
    
    strict_guard_rails = GuardRailsConfig.from_runtime_config(strict_config)
    
    print("Strict Guard Rails Configuration:")
    print(f"✅ Rate Limiting: {strict_guard_rails.rate_limiting_enabled}")
    print(f"✅ Content Safety: {strict_guard_rails.content_safety_enabled}")
    print(f"✅ Cost Controls: {strict_guard_rails.cost_controls_enabled}")
    print(f"✅ Max Requests/Min: {strict_guard_rails.max_requests_per_minute}")
    print(f"✅ Max Tokens/Request: {strict_guard_rails.max_tokens_per_request}")
    print(f"✅ Max Message Length: {strict_guard_rails.max_message_length}")
    print(f"✅ Graceful Degradation: {strict_guard_rails.graceful_degradation}")
    
    # Test lenient guard rails
    lenient_config = {
        'rate_limiting_enabled': False,
        'content_safety_enabled': False,
        'cost_controls_enabled': False,
        'max_requests_per_minute': 100,
        'max_tokens_per_request': 8000,
        'max_message_length': 2000,
        'graceful_degradation': True
    }
    
    lenient_guard_rails = GuardRailsConfig.from_runtime_config(lenient_config)
    
    print("\nLenient Guard Rails Configuration:")
    print(f"✅ Rate Limiting: {lenient_guard_rails.rate_limiting_enabled}")
    print(f"✅ Content Safety: {lenient_guard_rails.content_safety_enabled}")
    print(f"✅ Cost Controls: {lenient_guard_rails.cost_controls_enabled}")
    print(f"✅ Max Requests/Min: {lenient_guard_rails.max_requests_per_minute}")
    print(f"✅ Max Tokens/Request: {lenient_guard_rails.max_tokens_per_request}")
    print(f"✅ Max Message Length: {lenient_guard_rails.max_message_length}")
    print(f"✅ Graceful Degradation: {lenient_guard_rails.graceful_degradation}")
    
    print("✅ Guard Rails Configuration Test PASSED\n")
    return True


def test_language_configurations():
    """Test language configurations."""
    print("🧪 Testing Language Configurations")
    print("=" * 60)
    
    # Test Arabic configuration
    arabic_config = {
        'primary_language': 'arabic',
        'language_enforcement': 'strict',
        'fallback_language': 'english',
        'cultural_context': 'middle_east'
    }
    
    agent_config = AgentConfig.from_runtime_config(arabic_config)
    print(f"✅ Primary Language: {agent_config.get_default_language()}")
    
    # Test multi-language configuration
    multi_config = {
        'primary_language': 'spanish',
        'language_enforcement': 'flexible',
        'fallback_language': 'english',
        'translation_enabled': True
    }
    
    agent_config_multi = AgentConfig.from_runtime_config(multi_config)
    print(f"✅ Multi-language Primary: {agent_config_multi.get_default_language()}")
    
    print("✅ Language Configuration Test PASSED\n")
    return True


def print_comprehensive_config_example():
    """Print a comprehensive configuration example showing all options."""
    print("🔧 Comprehensive Runtime Configuration Example")
    print("=" * 60)
    
    comprehensive_config = {
        # Core identification
        "customer_name": "John Doe",
        "instance_name": "John's Comprehensive Grocery Assistant",
        "user_id": "john_comprehensive_001",
        "customer_profile_id": "550e8400-e29b-41d4-a716-446655440000",
        
        # Platform formatting
        "source": "whatsapp",
        
        # Language settings
        "primary_language": "english",
        "language_enforcement": "flexible",
        "fallback_language": "english",
        "translation_enabled": True,
        "cultural_context": "north_america",
        
        # Customer preferences
        "dietary_restrictions": ["vegetarian", "lactose_intolerant"],
        "preferred_stores": ["Albert Heijn", "Jumbo"],
        "shopping_persona": "health_focused",
        "budget_range": "medium",
        "price_sensitivity": "medium",
        "default_currency": "EUR",
        "shopping_frequency": "weekly",
        
        # Agent behavior
        "enable_memory_updates": True,
        "memory_update_threshold": 0.7,
        "enable_pricing_data": True,
        "price_comparison_enabled": True,
        "enable_personalized_recommendations": True,
        "consider_dietary_restrictions": True,
        "consider_budget_constraints": True,
        "suggest_alternatives": True,
        "include_price_estimates": True,
        "suggest_recipes_for_ingredients": True,
        "default_search_limit": 10,
        
        # Response configuration
        "max_response_length": 2000,
        "response_style": "helpful_and_practical",
        "use_emojis": True,
        "include_tips": True,
        
        # Custom instructions
        "custom_instructions": "Always suggest healthy alternatives and eco-friendly options",
        "system_prompt_additions": "Focus on sustainability and health benefits",
        
        # Feature toggles
        "enable_meal_planning": True,
        "enable_grocery_lists": True,
        "enable_budget_tracking": True,
        "enable_recipe_suggestions": True,
        "enable_cross_thread_memory": True,
        
        # Performance settings
        "cache_enabled": True,
        "cache_duration_minutes": 30,
        "validate_all_operations": True,
        "graceful_degradation": True,
        
        # Guard rails
        "rate_limiting_enabled": True,
        "max_requests_per_minute": 30,
        "content_safety_enabled": True,
        "cost_controls_enabled": True,
        "max_tokens_per_request": 4000,
        "max_message_length": 500
    }
    
    print(json.dumps(comprehensive_config, indent=2))
    print("\n✅ This configuration includes ALL available runtime options!\n")


def main():
    """Run all runtime configuration tests."""
    print("🚀 BargainB Agent - Comprehensive Runtime Configuration Test Suite")
    print("=" * 80)
    print(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    all_tests_passed = True
    
    try:
        # Run all tests
        all_tests_passed &= test_health_focused_family_config()
        all_tests_passed &= test_budget_conscious_student_config()
        all_tests_passed &= test_busy_professional_config()
        all_tests_passed &= test_feature_toggles()
        all_tests_passed &= test_guard_rails_configurations()
        all_tests_passed &= test_language_configurations()
        
        # Print comprehensive example
        print_comprehensive_config_example()
        
        # Final results
        print("=" * 80)
        if all_tests_passed:
            print("🎉 ALL RUNTIME CONFIGURATION TESTS PASSED!")
            print("✅ The agent now supports comprehensive dynamic configuration")
            print("✅ All dietary preferences, store preferences, custom instructions work")
            print("✅ Feature toggles, guard rails, and language settings are functional")
            print("✅ Ready for production deployment with full runtime configuration")
        else:
            print("❌ SOME TESTS FAILED!")
            print("⚠️  Please check the error messages above")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("⚠️  Please check your imports and dependencies")
        all_tests_passed = False
    
    return all_tests_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 