"""Memory management tools for user profiles, grocery lists, meal plans, and budgets."""

import uuid
from typing import TypedDict, Literal, Optional
from datetime import datetime, date

from trustcall import create_extractor
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage, merge_message_runs

from .memory_schemas import (
    UserProfile, GroceryItem, GroceryList, MealPlan, Budget,
    ShoppingHistory, UserGroceryLists, UserMealPlans, UserBudgets
)


# Update memory tool for routing decisions
class UpdateMemory(TypedDict):
    """Decision on what memory type to update"""
    update_type: Literal['profile', 'grocery_list', 'meal_plan', 'budget', 'shopping_history']


class MemoryManager:
    """Centralized memory management for the grocery/meal planning agent"""
    
    def __init__(self, model: ChatOpenAI):
        self.model = model
        
        # Create Trustcall extractors for different memory types
        self.profile_extractor = create_extractor(
            model,
            tools=[UserProfile],
            tool_choice="UserProfile"
        )
        
        self.grocery_extractor = create_extractor(
            model,
            tools=[GroceryItem, GroceryList],
            tool_choice="GroceryItem",
            enable_inserts=True
        )
        
        self.meal_extractor = create_extractor(
            model,
            tools=[MealPlan],
            tool_choice="MealPlan",
            enable_inserts=True
        )
        
        self.budget_extractor = create_extractor(
            model,
            tools=[Budget],
            tool_choice="Budget",
            enable_inserts=True
        )

    def get_user_profile(self, store: BaseStore, user_id: str) -> Optional[dict]:
        """Retrieve user profile from memory store"""
        namespace = ("profile", user_id)
        profile_memory = store.get(namespace, "user_profile")
        return profile_memory.value if profile_memory else None

    def get_grocery_lists(self, store: BaseStore, user_id: str) -> list:
        """Retrieve all grocery lists for a user"""
        namespace = ("grocery_lists", user_id)
        lists = store.search(namespace)
        return [item.value for item in lists]

    def get_meal_plans(self, store: BaseStore, user_id: str) -> list:
        """Retrieve all meal plans for a user"""
        namespace = ("meal_plans", user_id)
        plans = store.search(namespace)
        return [item.value for item in plans]

    def get_budgets(self, store: BaseStore, user_id: str) -> list:
        """Retrieve all budgets for a user"""
        namespace = ("budgets", user_id)
        budgets = store.search(namespace)
        return [item.value for item in budgets]

    def get_shopping_history(self, store: BaseStore, user_id: str) -> list:
        """Retrieve shopping history for a user"""
        namespace = ("shopping_history", user_id)
        history = store.search(namespace)
        return [item.value for item in history]

    def format_user_context(self, store: BaseStore, user_id: str) -> str:
        """Format all user memory context for the model"""
        profile = self.get_user_profile(store, user_id)
        grocery_lists = self.get_grocery_lists(store, user_id)
        meal_plans = self.get_meal_plans(store, user_id)
        budgets = self.get_budgets(store, user_id)

        context_parts = []

        # User Profile
        if profile:
            context_parts.append(f"**User Profile:**")
            context_parts.append(f"- Name: {profile.get('name', 'Unknown')}")
            context_parts.append(f"- Location: {profile.get('location', 'Unknown')}")
            context_parts.append(f"- Household Size: {profile.get('household_size', 'Unknown')}")
            if profile.get('dietary_preferences'):
                context_parts.append(f"- Dietary Preferences: {', '.join(profile['dietary_preferences'])}")
            if profile.get('allergies'):
                context_parts.append(f"- Allergies: {', '.join(profile['allergies'])}")
            if profile.get('preferred_stores'):
                context_parts.append(f"- Preferred Stores: {', '.join(profile['preferred_stores'])}")
            context_parts.append("")

        # Active Grocery Lists
        active_lists = [gl for gl in grocery_lists if gl.get('status') == 'active']
        if active_lists:
            context_parts.append(f"**Active Grocery Lists ({len(active_lists)}):**")
            for i, glist in enumerate(active_lists[:3], 1):  # Show max 3 lists
                context_parts.append(f"{i}. {glist.get('list_name', 'Unnamed List')} - {len(glist.get('items', []))} items")
            context_parts.append("")

        # Recent Meal Plans
        recent_plans = sorted(meal_plans, key=lambda x: x.get('meal_date', ''), reverse=True)[:5]
        if recent_plans:
            context_parts.append(f"**Recent Meal Plans ({len(recent_plans)}):**")
            for plan in recent_plans:
                context_parts.append(f"- {plan.get('meal_date', 'No date')}: {plan.get('meal_name', 'Unnamed')} ({plan.get('meal_type', 'unknown')})")
            context_parts.append("")

        # Current Budgets
        if budgets:
            context_parts.append(f"**Budgets:**")
            for budget in budgets:
                remaining = budget.get('remaining', budget.get('amount', 0))
                context_parts.append(f"- {budget.get('category', 'Unknown')}: €{remaining:.2f} remaining of €{budget.get('amount', 0):.2f} ({budget.get('period', 'unknown')})")
            context_parts.append("")

        return "\n".join(context_parts) if context_parts else "No user information stored."

    def update_profile(self, store: BaseStore, user_id: str, messages: list) -> str:
        """Update user profile using Trustcall"""
        namespace = ("profile", user_id)
        existing_memory = store.get(namespace, "user_profile")
        
        existing_profile = {"UserProfile": existing_memory.value} if existing_memory else None
        
        # Instruction for profile extraction
        instruction = "Extract and update user profile information from the conversation:"
        updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
        
        result = self.profile_extractor.invoke({
            "messages": updated_messages,
            "existing": existing_profile
        })
        
        # Save updated profile
        if result["responses"]:
            updated_profile = result["responses"][0].model_dump()
            store.put(namespace, "user_profile", updated_profile)
            return "Profile updated successfully"
        
        return "No profile updates needed"

    def update_grocery_lists(self, store: BaseStore, user_id: str, messages: list) -> str:
        """Update grocery lists using Trustcall"""
        namespace = ("grocery_lists", user_id)
        existing_items = store.search(namespace)
        
        # Format existing items for Trustcall
        existing_memories = (
            [(item.key, "GroceryItem", item.value) for item in existing_items]
            if existing_items else None
        )
        
        instruction = f"Extract grocery items and lists from the conversation. Current time: {datetime.now().isoformat()}"
        updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
        
        result = self.grocery_extractor.invoke({
            "messages": updated_messages,
            "existing": existing_memories
        })
        
        # Save grocery items
        updates = []
        for response, metadata in zip(result["responses"], result["response_metadata"]):
            item_id = metadata.get("json_doc_id", str(uuid.uuid4()))
            store.put(namespace, item_id, response.model_dump())
            updates.append(f"- {response.item_name}")
        
        return f"Updated grocery items:\n" + "\n".join(updates) if updates else "No grocery updates needed"

    def update_meal_plans(self, store: BaseStore, user_id: str, messages: list) -> str:
        """Update meal plans using Trustcall"""
        namespace = ("meal_plans", user_id)
        existing_items = store.search(namespace)
        
        existing_memories = (
            [(item.key, "MealPlan", item.value) for item in existing_items]
            if existing_items else None
        )
        
        instruction = f"Extract meal planning information from the conversation. Current date: {date.today().isoformat()}"
        updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
        
        result = self.meal_extractor.invoke({
            "messages": updated_messages,
            "existing": existing_memories
        })
        
        # Save meal plans
        updates = []
        for response, metadata in zip(result["responses"], result["response_metadata"]):
            plan_id = metadata.get("json_doc_id", str(uuid.uuid4()))
            store.put(namespace, plan_id, response.model_dump())
            updates.append(f"- {response.meal_name} ({response.meal_type}) for {response.meal_date}")
        
        return f"Updated meal plans:\n" + "\n".join(updates) if updates else "No meal plan updates needed"

    def update_budgets(self, store: BaseStore, user_id: str, messages: list) -> str:
        """Update budgets using Trustcall"""
        namespace = ("budgets", user_id)
        existing_items = store.search(namespace)
        
        existing_memories = (
            [(item.key, "Budget", item.value) for item in existing_items]
            if existing_items else None
        )
        
        instruction = "Extract budget information from the conversation:"
        updated_messages = [SystemMessage(content=instruction)] + messages[:-1]
        
        result = self.budget_extractor.invoke({
            "messages": updated_messages,
            "existing": existing_memories
        })
        
        # Save budgets
        updates = []
        for response, metadata in zip(result["responses"], result["response_metadata"]):
            budget_id = metadata.get("json_doc_id", str(uuid.uuid4()))
            
            # Calculate remaining amount
            budget_data = response.model_dump()
            budget_data['remaining'] = budget_data['amount'] - budget_data.get('spent', 0)
            
            store.put(namespace, budget_id, budget_data)
            updates.append(f"- {response.category}: €{response.amount} ({response.period})")
        
        return f"Updated budgets:\n" + "\n".join(updates) if updates else "No budget updates needed"

    def add_shopping_history(self, store: BaseStore, user_id: str, purchase_data: dict) -> str:
        """Add shopping history entry"""
        namespace = ("shopping_history", user_id)
        history_id = str(uuid.uuid4())
        
        # Add timestamp if not present
        if 'date' not in purchase_data:
            purchase_data['date'] = datetime.now().isoformat()
        
        store.put(namespace, history_id, purchase_data)
        
        # Update relevant budget
        if 'total_cost' in purchase_data:
            self._update_budget_spending(store, user_id, purchase_data['total_cost'])
        
        return f"Added shopping history: €{purchase_data.get('total_cost', 0):.2f} at {purchase_data.get('store', 'Unknown store')}"

    def _update_budget_spending(self, store: BaseStore, user_id: str, amount: float):
        """Update budget spending amounts"""
        namespace = ("budgets", user_id)
        budgets = store.search(namespace)
        
        for budget_item in budgets:
            budget = budget_item.value
            if budget.get('category') == 'groceries':  # Update grocery budget
                budget['spent'] = budget.get('spent', 0) + amount
                budget['remaining'] = budget.get('amount', 0) - budget['spent']
                store.put(namespace, budget_item.key, budget)
                break 