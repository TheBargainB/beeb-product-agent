"""Memory schemas that match the actual Supabase database structure."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, date
from uuid import UUID


class UserProfile(BaseModel):
    """User profile schema matching crm_profiles table"""
    full_name: Optional[str] = Field(description="User's full name", default=None)
    preferred_name: Optional[str] = Field(description="User's preferred name", default=None)
    email: Optional[str] = Field(description="User's email address", default=None)
    date_of_birth: Optional[date] = Field(description="User's date of birth", default=None)
    lifecycle_stage: Optional[str] = Field(description="Customer lifecycle stage", default="customer")
    preferred_stores: List[str] = Field(
        description="Preferred grocery stores (Albert Heijn, Jumbo, Dirk, etc.)",
        default_factory=list
    )
    shopping_persona: Optional[str] = Field(description="Shopping personality type", default=None)
    dietary_restrictions: List[str] = Field(
        description="Dietary restrictions/preferences",
        default_factory=list
    )
    budget_range: Optional[str] = Field(description="General budget range", default=None)
    shopping_frequency: Optional[str] = Field(description="How often they shop", default=None)
    product_interests: List[str] = Field(description="Product categories of interest", default_factory=list)
    price_sensitivity: Optional[str] = Field(description="Price sensitivity level", default=None)
    communication_style: Optional[str] = Field(description="Preferred communication style", default=None)
    response_time_preference: Optional[str] = Field(description="Preferred response time", default=None)
    notification_preferences: Dict[str, Any] = Field(description="Notification settings", default_factory=dict)
    tags: List[str] = Field(description="Customer tags", default_factory=list)
    notes: Optional[str] = Field(description="Additional notes", default=None)


class GroceryListProduct(BaseModel):
    """Product item in grocery list matching the JSONB structure"""
    gtin: str = Field(description="Product GTIN/barcode")
    title: str = Field(description="Product title/name")
    category: str = Field(description="Product category")
    quantity: int = Field(description="Quantity needed", default=1)
    estimated_price: float = Field(description="Estimated price per item")
    actual_price: Optional[float] = Field(description="Actual price paid", default=None)
    purchased: Optional[bool] = Field(description="Whether item was purchased", default=False)
    notes: Optional[str] = Field(description="Item notes", default=None)


class GroceryList(BaseModel):
    """Grocery list schema matching grocery_lists table"""
    list_name: str = Field(description="Name of the grocery list")
    products: List[GroceryListProduct] = Field(description="Products in the list", default_factory=list)
    estimated_total: Optional[float] = Field(description="Total estimated cost", default=None)
    actual_total: Optional[float] = Field(description="Total actual cost", default=None)
    preferred_store: Optional[str] = Field(description="Preferred store for shopping", default=None)
    shopping_date: Optional[date] = Field(description="Planned shopping date", default=None)
    status: str = Field(description="List status (active, completed, archived)", default="active")
    is_template: bool = Field(description="Whether this is a template list", default=False)
    auto_reorder_enabled: bool = Field(description="Enable automatic reordering", default=False)
    reorder_frequency: Optional[str] = Field(description="Reorder frequency if auto-reorder enabled", default=None)


class MealPlan(BaseModel):
    """Meal plan schema matching meal_plans table"""
    plan_name: Optional[str] = Field(description="Name of the meal plan", default=None)
    meal_date: date = Field(description="Date for the meal")
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = Field(description="Type of meal")
    recipe_id: Optional[UUID] = Field(description="Reference to recipe if using existing recipe", default=None)
    custom_meal_name: Optional[str] = Field(description="Custom meal name if not using recipe", default=None)
    planned_servings: int = Field(description="Number of servings planned", default=1)
    notes: Optional[str] = Field(description="Additional notes", default=None)
    is_completed: bool = Field(description="Whether meal was completed", default=False)


class Recipe(BaseModel):
    """Recipe schema matching recipes table"""
    name: str = Field(description="Recipe name")
    description: Optional[str] = Field(description="Recipe description", default=None)
    instructions: str = Field(description="Cooking instructions")
    prep_time_minutes: Optional[int] = Field(description="Preparation time in minutes", default=None)
    cook_time_minutes: Optional[int] = Field(description="Cooking time in minutes", default=None)
    servings: int = Field(description="Number of servings", default=1)
    difficulty_level: Optional[str] = Field(description="Difficulty level", default="easy")
    cuisine_type: Optional[str] = Field(description="Type of cuisine", default=None)
    dietary_tags: List[str] = Field(description="Dietary tags (vegetarian, vegan, etc.)", default_factory=list)
    nutrition_info: Dict[str, Any] = Field(description="Nutritional information", default_factory=dict)
    image_url: Optional[str] = Field(description="Recipe image URL", default=None)
    is_public: bool = Field(description="Whether recipe is public", default=True)


class BudgetPeriod(BaseModel):
    """Budget period schema matching budget_periods table"""
    period_name: str = Field(description="Name of the budget period")
    period_type: Literal["weekly", "monthly", "yearly"] = Field(description="Type of budget period")
    start_date: date = Field(description="Period start date")
    end_date: date = Field(description="Period end date")
    total_budget: float = Field(description="Total budget amount")
    total_spent: Optional[float] = Field(description="Total amount spent", default=0)
    total_saved: Optional[float] = Field(description="Total amount saved", default=0)
    currency: str = Field(description="Currency code", default="EUR")
    is_active: bool = Field(description="Whether this budget period is active", default=True)


class BudgetCategory(BaseModel):
    """Budget category schema matching budget_categories table"""
    category_name: str = Field(description="Name of the budget category")
    allocated_amount: float = Field(description="Amount allocated to this category")
    spent_amount: Optional[float] = Field(description="Amount spent in this category", default=0)
    category_type: Optional[str] = Field(description="Type of category (groceries, household, etc.)", default=None)
    priority_level: Optional[int] = Field(description="Priority level (1=highest)", default=None)
    is_flexible: bool = Field(description="Whether this category budget is flexible", default=True)


class BudgetExpense(BaseModel):
    """Budget expense schema matching budget_expenses table"""
    expense_name: str = Field(description="Name/description of the expense")
    amount: float = Field(description="Expense amount")
    expense_date: date = Field(description="Date of expense")
    expense_type: Optional[str] = Field(description="Type of expense", default=None)
    store_name: Optional[str] = Field(description="Store where expense occurred", default=None)
    receipt_number: Optional[str] = Field(description="Receipt number", default=None)
    products_data: Optional[Dict[str, Any]] = Field(description="Products purchased data", default=None)
    payment_method: Optional[str] = Field(description="Payment method used", default=None)
    tags: List[str] = Field(description="Expense tags", default_factory=list)
    notes: Optional[str] = Field(description="Additional notes", default=None)


# Collection schemas for memory management
class UserGroceryLists(BaseModel):
    """Collection of grocery lists for a user"""
    lists: List[GroceryList] = Field(description="User's grocery lists", default_factory=list)


class UserMealPlans(BaseModel):
    """Collection of meal plans for a user"""
    plans: List[MealPlan] = Field(description="User's meal plans", default_factory=list)


class UserBudgets(BaseModel):
    """Collection of user budgets including periods and categories"""
    budget_periods: List[BudgetPeriod] = Field(description="User's budget periods", default_factory=list)
    budget_categories: List[BudgetCategory] = Field(description="User's budget categories", default_factory=list) 