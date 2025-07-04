"""Memory management tools that work directly with Supabase tables."""

import uuid
import json
from typing import TypedDict, Literal, Optional, List, Dict, Any
from datetime import datetime, date

from trustcall import create_extractor
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, merge_message_runs

from .memory_schemas import (
    UserProfile,
    GroceryList,
    Recipe,
    MealPlan,
    BudgetPeriod,
    BudgetExpense
)
from .supabase_client import SupabaseClient
from .config import get_config


# Update memory tool for routing decisions
class UpdateMemory(TypedDict):
    """Decision on what memory type to update"""
    update_type: Literal['profile', 'grocery_list', 'meal_plan', 'budget', 'recipe']


class SupabaseMemoryManager:
    """Memory management that works directly with Supabase tables."""
    
    def __init__(self, model: ChatOpenAI, supabase_client: SupabaseClient, crm_profile_id: Optional[str] = None):
        self.model = model
        self.supabase = supabase_client
        self.config = get_config()
        
        # Use provided CRM profile ID (from runtime config) or fallback to YAML config
        self.crm_profile_id = crm_profile_id or self.config.get_crm_profile_id()
        
        # Skip validation if no profile ID is configured (general assistant mode)
        if self.crm_profile_id is None:
            print("⚠️  No CRM profile ID configured - running in general assistant mode")
            print("   Customer-specific features (memory, personalization) will be disabled")
        elif self.config.should_validate_profile():
            self._validate_profile_exists()
        
        # Create Trustcall extractors for different memory types
        self.profile_extractor = create_extractor(
            model,
            tools=[UserProfile],
            tool_choice="UserProfile"
        )
        
        # Create grocery and meal planning extractors
        self.grocery_extractor = create_extractor(
            model,
            tools=[GroceryList],
            tool_choice="GroceryList"
        )
        
        self.recipe_extractor = create_extractor(
            model,
            tools=[Recipe],
            tool_choice="Recipe"
        )
        
        self.meal_plan_extractor = create_extractor(
            model,
            tools=[MealPlan],
            tool_choice="MealPlan"
        )
        
        self.budget_extractor = create_extractor(
            model,
            tools=[BudgetPeriod],
            tool_choice="BudgetPeriod"
        )

    def _validate_profile_exists(self) -> None:
        """Validate that the configured CRM profile exists in the database"""
        try:
            result = self.supabase.client.table('crm_profiles').select('id').eq('id', self.crm_profile_id).execute()
            
            if not result.data:
                raise ValueError(f"Configured CRM profile ID {self.crm_profile_id} does not exist in the database")
                
            print(f"✅ Validated CRM profile {self.crm_profile_id} exists")
        except Exception as e:
            raise ValueError(f"Failed to validate CRM profile: {e}")

    # Profile Management
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Retrieve user profile from crm_profiles table"""
        if self.crm_profile_id is None:
            return None
        try:
            result = self.supabase.client.table('crm_profiles').select('*').eq('id', self.crm_profile_id).execute()
            
            if result.data:
                profile = result.data[0]
                return {
                    'full_name': profile.get('full_name'),
                    'preferred_name': profile.get('preferred_name'),
                    'email': profile.get('email'),
                    'lifecycle_stage': profile.get('lifecycle_stage'),
                    'preferred_stores': profile.get('preferred_stores', []),
                    'shopping_persona': profile.get('shopping_persona'),
                    'dietary_restrictions': profile.get('dietary_restrictions', []),
                    'budget_range': profile.get('budget_range'),
                    'shopping_frequency': profile.get('shopping_frequency'),
                    'product_interests': profile.get('product_interests', []),
                    'price_sensitivity': profile.get('price_sensitivity'),
                    'communication_style': profile.get('communication_style'),
                    'notification_preferences': profile.get('notification_preferences', {}),
                    'tags': profile.get('tags', []),
                    'notes': profile.get('notes')
                }
            return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

    def get_grocery_assistant_context(self) -> str:
        """Get customer preferences formatted for grocery assistant context"""
        if self.crm_profile_id is None:
            return "No customer profile available - providing general grocery assistance."
        
        profile = self.get_user_profile()
        if not profile:
            return "Customer profile not found - providing general grocery assistance."
        
        context_parts = []
        
        # Customer identification
        if profile.get('preferred_name') or profile.get('full_name'):
            name = profile.get('preferred_name') or profile.get('full_name')
            context_parts.append(f"Customer: {name}")
        
        # Dietary restrictions and allergies
        if profile.get('dietary_restrictions'):
            restrictions = ", ".join(profile['dietary_restrictions'])
            context_parts.append(f"Dietary Restrictions/Allergies: {restrictions}")
        
        # Preferred stores and locations
        if profile.get('preferred_stores'):
            stores = ", ".join(profile['preferred_stores'])
            context_parts.append(f"Preferred Stores: {stores}")
        
        # Shopping persona and style
        if profile.get('shopping_persona'):
            persona_descriptions = {
                'healthHero': 'Health-focused, prefers organic and nutritious options',
                'ecoShopper': 'Environmentally conscious, prefers sustainable and eco-friendly products',
                'sensitiveStomach': 'Has sensitive stomach, needs gentle and easily digestible foods',
                'budgetSaver': 'Budget-conscious, looks for deals and cost-effective options',
                'convenienceShopper': 'Values convenience, prefers quick and easy meal solutions'
            }
            persona = profile['shopping_persona']
            description = persona_descriptions.get(persona, persona)
            context_parts.append(f"Shopping Style: {description}")
        
        # Budget constraints
        if profile.get('budget_range'):
            budget = profile['budget_range']
            context_parts.append(f"Budget Range: {budget}")
        
        # Price sensitivity
        if profile.get('price_sensitivity'):
            sensitivity = profile['price_sensitivity']
            context_parts.append(f"Price Sensitivity: {sensitivity}")
        
        # Shopping frequency
        if profile.get('shopping_frequency'):
            frequency = profile['shopping_frequency']
            context_parts.append(f"Shopping Frequency: {frequency}")
        
        # Product interests
        if profile.get('product_interests'):
            interests = ", ".join(profile['product_interests'])
            context_parts.append(f"Product Interests: {interests}")
        
        # Communication style
        if profile.get('communication_style'):
            style = profile['communication_style']
            context_parts.append(f"Communication Preference: {style}")
        
        if context_parts:
            context = "CUSTOMER PROFILE:\n" + "\n".join(f"• {part}" for part in context_parts)
            context += "\n\nIMPORTANT: Always consider these preferences when making grocery recommendations, meal suggestions, and shopping advice."
            return context
        
        return "Customer profile exists but no grocery preferences configured."

    def update_user_profile(self, updates: Dict[str, Any]) -> str:
        """Update user profile in crm_profiles table"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot update user profile - no CRM profile ID configured"
        try:
            # Remove None values and prepare update data
            clean_updates = {k: v for k, v in updates.items() if v is not None}
            clean_updates['updated_at'] = datetime.now().isoformat()
            
            result = self.supabase.client.table('crm_profiles').update(clean_updates).eq('id', self.crm_profile_id).execute()
            
            if result.data:
                return f"✅ Updated user profile: {', '.join(clean_updates.keys())}"
            else:
                return "❌ Failed to update user profile"
        except Exception as e:
            return f"❌ Error updating profile: {e}"

    # Grocery List Management
    def get_grocery_lists(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve grocery lists from grocery_lists table"""
        if self.crm_profile_id is None:
            return []
        try:
            query = self.supabase.client.table('grocery_lists').select('*').eq('crm_profile_id', self.crm_profile_id)
            
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).execute()
            
            grocery_lists = []
            for gl in result.data:
                grocery_lists.append({
                    'id': gl['id'],
                    'list_name': gl['list_name'],
                    'status': gl['status'],
                    'products': gl['products'],  # JSONB array
                    'estimated_total': float(gl['estimated_total']) if gl['estimated_total'] else 0,
                    'actual_total': float(gl['actual_total']) if gl['actual_total'] else None,
                    'preferred_store': gl['preferred_store'],
                    'shopping_date': gl['shopping_date'],
                    'is_template': gl['is_template'],
                    'auto_reorder_enabled': gl['auto_reorder_enabled'],
                    'created_at': gl['created_at']
                })
            return grocery_lists
        except Exception as e:
            print(f"Error getting grocery lists: {e}")
            return []

    def create_grocery_list(self, grocery_list_data: Dict[str, Any]) -> str:
        """Create a new grocery list in grocery_lists table"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot create grocery list - no CRM profile ID configured"
        try:
            # Prepare grocery list data
            list_data = {
                'id': str(uuid.uuid4()),
                'crm_profile_id': self.crm_profile_id,
                'list_name': grocery_list_data.get('list_name', 'New Grocery List'),
                'products': grocery_list_data.get('products', []),
                'estimated_total': grocery_list_data.get('estimated_total'),
                'preferred_store': grocery_list_data.get('preferred_store'),
                'shopping_date': grocery_list_data.get('shopping_date'),
                'status': grocery_list_data.get('status', 'active'),
                'is_template': grocery_list_data.get('is_template', False),
                'auto_reorder_enabled': grocery_list_data.get('auto_reorder_enabled', False),
                'reorder_frequency': grocery_list_data.get('reorder_frequency'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.client.table('grocery_lists').insert(list_data).execute()
            
            if result.data:
                return f"✅ Created grocery list: {list_data['list_name']}"
            else:
                return "❌ Failed to create grocery list"
        except Exception as e:
            return f"❌ Error creating grocery list: {e}"

    def update_grocery_list(self, list_id: str, updates: Dict[str, Any]) -> str:
        """Update an existing grocery list"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot update grocery list - no CRM profile ID configured"
        try:
            clean_updates = {k: v for k, v in updates.items() if v is not None}
            clean_updates['updated_at'] = datetime.now().isoformat()
            
            result = self.supabase.client.table('grocery_lists').update(clean_updates).eq('id', list_id).eq('crm_profile_id', self.crm_profile_id).execute()
            
            if result.data:
                return f"✅ Updated grocery list"
            else:
                return "❌ Failed to update grocery list"
        except Exception as e:
            return f"❌ Error updating grocery list: {e}"

    # Meal Plan Management
    def get_meal_plans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve meal plans from meal_plans table"""
        if self.crm_profile_id is None:
            return []
        try:
            result = self.supabase.client.table('meal_plans').select('''
                *,
                recipes(name, prep_time_minutes, dietary_tags, instructions)
            ''').eq('crm_profile_id', self.crm_profile_id).order('meal_date', desc=True).limit(limit).execute()
            
            meal_plans = []
            for mp in result.data:
                meal_plans.append({
                    'id': mp['id'],
                    'plan_name': mp['plan_name'],
                    'meal_date': mp['meal_date'],
                    'meal_type': mp['meal_type'],
                    'custom_meal_name': mp['custom_meal_name'],
                    'recipe_name': mp['recipes']['name'] if mp['recipes'] else None,
                    'recipe_instructions': mp['recipes']['instructions'] if mp['recipes'] else None,
                    'planned_servings': mp['planned_servings'],
                    'prep_time': mp['recipes']['prep_time_minutes'] if mp['recipes'] else None,
                    'dietary_tags': mp['recipes']['dietary_tags'] if mp['recipes'] else [],
                    'is_completed': mp['is_completed'],
                    'notes': mp['notes']
                })
            return meal_plans
        except Exception as e:
            print(f"Error getting meal plans: {e}")
            return []

    def create_meal_plan(self, meal_plan_data: Dict[str, Any]) -> str:
        """Create a new meal plan in meal_plans table"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot create meal plan - no CRM profile ID configured"
        try:
            plan_data = {
                'id': str(uuid.uuid4()),
                'crm_profile_id': self.crm_profile_id,
                'plan_name': meal_plan_data.get('plan_name'),
                'meal_date': meal_plan_data.get('meal_date'),
                'meal_type': meal_plan_data.get('meal_type'),
                'recipe_id': meal_plan_data.get('recipe_id'),
                'custom_meal_name': meal_plan_data.get('custom_meal_name'),
                'planned_servings': meal_plan_data.get('planned_servings', 1),
                'notes': meal_plan_data.get('notes'),
                'is_completed': meal_plan_data.get('is_completed', False),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.client.table('meal_plans').insert(plan_data).execute()
            
            if result.data:
                meal_name = plan_data.get('custom_meal_name', 'meal plan')
                return f"✅ Created meal plan: {meal_name} for {plan_data['meal_date']}"
            else:
                return "❌ Failed to create meal plan"
        except Exception as e:
            return f"❌ Error creating meal plan: {e}"

    # Budget Management
    def get_active_budget(self) -> Optional[Dict[str, Any]]:
        """Get active budget period with categories"""
        if self.crm_profile_id is None:
            return None
        try:
            result = self.supabase.client.table('budget_periods').select('''
                *,
                budget_categories(*)
            ''').eq('crm_profile_id', self.crm_profile_id).eq('is_active', True).execute()
            
            if result.data:
                budget_period = result.data[0]
                return {
                    'period_id': budget_period['id'],
                    'period_name': budget_period['period_name'],
                    'period_type': budget_period['period_type'],
                    'start_date': budget_period['start_date'],
                    'end_date': budget_period['end_date'],
                    'total_budget': float(budget_period['total_budget']),
                    'total_spent': float(budget_period['total_spent'] or 0),
                    'currency': budget_period['currency'],
                    'categories': [
                        {
                            'id': cat['id'],
                            'name': cat['category_name'],
                            'allocated': float(cat['allocated_amount']),
                            'spent': float(cat['spent_amount'] or 0),
                            'remaining': float(cat['allocated_amount']) - float(cat['spent_amount'] or 0),
                            'type': cat['category_type'],
                            'priority': cat['priority_level']
                        }
                        for cat in budget_period['budget_categories']
                    ]
                }
            return None
        except Exception as e:
            print(f"Error getting active budget: {e}")
            return None

    def create_budget_period(self, budget_data: Dict[str, Any]) -> str:
        """Create a new budget period with categories"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot create budget period - no CRM profile ID configured"
        try:
            # First create the budget period
            period_id = str(uuid.uuid4())
            period_data = {
                'id': period_id,
                'crm_profile_id': self.crm_profile_id,
                'period_name': budget_data.get('period_name'),
                'period_type': budget_data.get('period_type'),
                'start_date': budget_data.get('start_date'),
                'end_date': budget_data.get('end_date'),
                'total_budget': budget_data.get('total_budget'),
                'currency': budget_data.get('currency', 'EUR'),
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.client.table('budget_periods').insert(period_data).execute()
            
            if result.data:
                # Create default budget categories
                categories = [
                    {'category_name': 'Groceries', 'allocated_amount': float(budget_data.get('total_budget', 0)) * 0.7, 'category_type': 'groceries', 'priority_level': 1},
                    {'category_name': 'Household Items', 'allocated_amount': float(budget_data.get('total_budget', 0)) * 0.2, 'category_type': 'household', 'priority_level': 2},
                    {'category_name': 'Treats & Snacks', 'allocated_amount': float(budget_data.get('total_budget', 0)) * 0.1, 'category_type': 'other', 'priority_level': 3}
                ]
                
                for cat in categories:
                    cat_data = {
                        'id': str(uuid.uuid4()),
                        'budget_period_id': period_id,
                        'category_name': cat['category_name'],
                        'allocated_amount': cat['allocated_amount'],
                        'spent_amount': 0,
                        'category_type': cat['category_type'],
                        'priority_level': cat['priority_level'],
                        'is_flexible': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    self.supabase.client.table('budget_categories').insert(cat_data).execute()
                
                return f"✅ Created budget period: {period_data['period_name']}"
            else:
                return "❌ Failed to create budget period"
        except Exception as e:
            return f"❌ Error creating budget: {e}"

    # Context Formatting
    def format_user_context(self) -> str:
        """Format all user memory context for the model with grocery-specific preferences"""
        if self.crm_profile_id is None:
            return "Running in general assistant mode - no customer-specific context available."
        
        context_parts = []
        
        # Enhanced grocery-specific customer preferences
        grocery_context = self.get_grocery_assistant_context()
        if grocery_context and grocery_context != "Customer profile exists but no grocery preferences configured.":
            context_parts.append(grocery_context)
            context_parts.append("")
        
        # Get additional data for current activity context
        grocery_lists = self.get_grocery_lists(status='active')
        meal_plans = self.get_meal_plans(limit=5)
        budget = self.get_active_budget()

        # Active Grocery Lists
        if grocery_lists:
            context_parts.append(f"**CURRENT GROCERY LISTS ({len(grocery_lists)}):**")
            for i, glist in enumerate(grocery_lists[:3], 1):  # Show max 3 lists
                item_count = len(glist.get('products', []))
                total = glist.get('estimated_total', 0)
                store = glist.get('preferred_store', '')
                store_info = f" at {store}" if store else ""
                context_parts.append(f"• {glist.get('list_name', 'Unnamed List')}: {item_count} items (€{total:.2f}){store_info}")
            context_parts.append("")

        # Recent Meal Plans
        if meal_plans:
            context_parts.append(f"**UPCOMING MEALS ({len(meal_plans)}):**")
            for plan in meal_plans:
                status = "✓" if plan.get('is_completed') else "○"
                meal_name = plan.get('custom_meal_name') or plan.get('recipe_name', 'Unnamed meal')
                context_parts.append(f"• {status} {plan.get('meal_date')}: {meal_name} ({plan.get('meal_type')})")
            context_parts.append("")

        # Active Budget
        if budget:
            context_parts.append("**CURRENT BUDGET:**")
            spent_percentage = (budget['total_spent'] / budget['total_budget'] * 100) if budget['total_budget'] > 0 else 0
            remaining = budget['total_budget'] - budget['total_spent']
            context_parts.append(f"• Period: {budget['period_name']} ({budget['period_type']})")
            context_parts.append(f"• Budget: €{remaining:.2f} remaining of €{budget['total_budget']:.2f} ({spent_percentage:.1f}% spent)")
            if budget['categories']:
                context_parts.append("• Categories:")
                for cat in budget['categories'][:3]:  # Show top 3 categories
                    context_parts.append(f"  - {cat['name']}: €{cat['remaining']:.2f} left (€{cat['allocated']:.2f} allocated)")
            context_parts.append("")

        if not context_parts:
            return "No user context available. This is a new customer with no preferences or activity."

        return "\n".join(context_parts)

    # Memory Update Methods using Trustcall
    def update_profile_memory(self, messages: List) -> str:
        """Update user profile using conversation context"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot update profile memory - no CRM profile ID configured"
        try:
            # Get existing profile
            existing_profile = self.get_user_profile()
            
            # Format existing profile for Trustcall
            existing_memories = None
            if existing_profile:
                existing_memories = [('profile', 'UserProfile', existing_profile)]
            
            # Create instruction for profile update
            instruction = "Extract and update user profile information from the conversation:"
            updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
            
            # Use Trustcall to extract updated profile
            result = self.profile_extractor.invoke({
                "messages": updated_messages,
                "existing": existing_memories
            })
            
            if result["responses"]:
                profile_updates = result["responses"][0].model_dump()
                return self.update_user_profile(profile_updates)
            
            return "No profile updates extracted from conversation"
            
        except Exception as e:
            return f"❌ Error updating profile memory: {e}"

    def update_grocery_memory(self, messages: List) -> str:
        """Update grocery lists using conversation context"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot update grocery memory - no CRM profile ID configured"
        try:
            # Create instruction for grocery list extraction
            instruction = "Extract grocery list information from the conversation. Create or update grocery lists with specific products:"
            updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
            
            # Use Trustcall to extract grocery list
            result = self.grocery_extractor.invoke({"messages": updated_messages})
            
            if result["responses"]:
                grocery_data = result["responses"][0].model_dump()
                return self.create_grocery_list(grocery_data)
            
            return "No grocery list information extracted from conversation"
            
        except Exception as e:
            return f"❌ Error updating grocery memory: {e}"
    
    def update_meal_plan_memory(self, messages: List) -> str:
        """Update meal plans using conversation context"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot update meal plan memory - no CRM profile ID configured"
        try:
            # Create instruction for meal plan extraction
            instruction = "Extract meal planning information from the conversation. Create or update meal plans with specific dates and meals:"
            updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
            
            # Use Trustcall to extract meal plan
            result = self.meal_plan_extractor.invoke({"messages": updated_messages})
            
            if result["responses"]:
                meal_plan_data = result["responses"][0].model_dump()
                return self.create_meal_plan(meal_plan_data)
            
            return "No meal plan information extracted from conversation"
            
        except Exception as e:
            return f"❌ Error updating meal plan memory: {e}"
    
    def update_recipe_memory(self, messages: List) -> str:
        """Update recipes using conversation context"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot update recipe memory - no CRM profile ID configured"
        try:
            # Create instruction for recipe extraction
            instruction = "Extract recipe information from the conversation. Create or update recipes with ingredients and instructions:"
            updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
            
            # Use Trustcall to extract recipe
            result = self.recipe_extractor.invoke({"messages": updated_messages})
            
            if result["responses"]:
                recipe_data = result["responses"][0].model_dump()
                return self.create_recipe(recipe_data)
            
            return "No recipe information extracted from conversation"
            
        except Exception as e:
            return f"❌ Error updating recipe memory: {e}"
    
    def create_recipe(self, recipe_data: Dict[str, Any]) -> str:
        """Create a new recipe in recipes table"""
        try:
            recipe_id = str(uuid.uuid4())
            data = {
                'id': recipe_id,
                'name': recipe_data.get('name'),
                'ingredients': recipe_data.get('ingredients', []),
                'instructions': recipe_data.get('instructions', []),
                'prep_time_minutes': recipe_data.get('prep_time_minutes'),
                'cook_time_minutes': recipe_data.get('cook_time_minutes'),
                'servings': recipe_data.get('servings'),
                'difficulty': recipe_data.get('difficulty', 'medium'),
                'dietary_tags': recipe_data.get('dietary_tags', []),
                'estimated_cost': recipe_data.get('estimated_cost'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.client.table('recipes').insert(data).execute()
            
            if result.data:
                return f"✅ Created recipe: {data['name']}"
            else:
                return "❌ Failed to create recipe"
        except Exception as e:
            return f"❌ Error creating recipe: {e}"



    def update_budget_memory(self, messages: List) -> str:
        """Update budget using conversation context"""
        if self.crm_profile_id is None:
            return "⚠️ Cannot update budget memory - no CRM profile ID configured"
        try:
            # Check if there's already an active budget
            existing_budget = self.get_active_budget()
            if existing_budget:
                return "Active budget already exists. Budget management features coming soon."
            
            # Create instruction for budget extraction
            instruction = "Extract budget information from the conversation. Create budget periods with amounts and timeframes:"
            updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
            
            # Use Trustcall to extract budget
            result = self.budget_extractor.invoke({"messages": updated_messages})
            
            if result["responses"]:
                budget_data = result["responses"][0].model_dump()
                return self.create_budget_period(budget_data)
            
            return "No budget information extracted from conversation"
            
        except Exception as e:
            return f"❌ Error updating budget memory: {e}"


# For backwards compatibility, alias the new class
MemoryManager = SupabaseMemoryManager 