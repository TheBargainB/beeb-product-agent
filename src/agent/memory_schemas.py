"""Memory schemas for user profiles, grocery lists, meal plans, and budgets."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, date


class UserProfile(BaseModel):
    """User profile schema for personalization"""
    name: Optional[str] = Field(description="User's name", default=None)
    location: Optional[str] = Field(description="User's location/city", default=None)
    household_size: Optional[int] = Field(description="Number of people in household", default=None)
    dietary_preferences: List[str] = Field(
        description="Dietary restrictions/preferences (vegetarian, vegan, gluten-free, etc.)",
        default_factory=list
    )
    allergies: List[str] = Field(
        description="Food allergies or intolerances",
        default_factory=list
    )
    preferred_stores: List[str] = Field(
        description="Preferred grocery stores (Albert Heijn, Jumbo, Dirk, etc.)",
        default_factory=list
    )
    cooking_skill_level: Optional[str] = Field(
        description="Cooking skill level (beginner, intermediate, advanced)",
        default=None
    )
    favorite_cuisines: List[str] = Field(
        description="Favorite types of cuisine",
        default_factory=list
    )


class GroceryItem(BaseModel):
    """Individual grocery item schema"""
    item_name: str = Field(description="Name of the grocery item")
    quantity: int = Field(description="Quantity needed", default=1)
    unit: Optional[str] = Field(description="Unit of measurement (kg, pieces, liters, etc.)", default=None)
    category: Optional[str] = Field(description="Product category", default=None)
    brand_preference: Optional[str] = Field(description="Preferred brand", default=None)
    estimated_price: Optional[float] = Field(description="Estimated price in euros", default=None)
    store: Optional[str] = Field(description="Preferred store to buy from", default=None)
    priority: str = Field(description="Priority level", default="medium")
    notes: Optional[str] = Field(description="Additional notes", default=None)
    purchased: bool = Field(description="Whether item has been purchased", default=False)
    date_added: datetime = Field(description="When item was added", default_factory=datetime.now)


class GroceryList(BaseModel):
    """Grocery list schema"""
    list_name: str = Field(description="Name of the grocery list")
    items: List[GroceryItem] = Field(description="Items in the grocery list", default_factory=list)
    total_estimated_cost: Optional[float] = Field(description="Total estimated cost", default=None)
    created_date: datetime = Field(description="When list was created", default_factory=datetime.now)
    target_date: Optional[date] = Field(description="Target shopping date", default=None)
    status: str = Field(description="List status", default="active")
    notes: Optional[str] = Field(description="Additional notes for the list", default=None)


class MealPlan(BaseModel):
    """Individual meal plan schema"""
    meal_name: str = Field(description="Name of the meal")
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = Field(description="Type of meal")
    meal_date: date = Field(description="Date for the meal")
    servings: int = Field(description="Number of servings", default=1)
    prep_time: Optional[int] = Field(description="Preparation time in minutes", default=None)
    cook_time: Optional[int] = Field(description="Cooking time in minutes", default=None)
    difficulty: Optional[str] = Field(description="Cooking difficulty level", default=None)
    cuisine_type: Optional[str] = Field(description="Type of cuisine", default=None)
    ingredients: List[str] = Field(description="Required ingredients", default_factory=list)
    instructions: Optional[str] = Field(description="Cooking instructions", default=None)
    nutritional_info: Optional[str] = Field(description="Nutritional information", default=None)
    cost_estimate: Optional[float] = Field(description="Estimated cost to make", default=None)
    tags: List[str] = Field(description="Tags for the meal (quick, healthy, etc.)", default_factory=list)


class Budget(BaseModel):
    """Budget tracking schema"""
    category: str = Field(description="Budget category (groceries, dining_out, household, etc.)")
    amount: float = Field(description="Budget amount in euros")
    period: Literal["weekly", "monthly", "yearly"] = Field(description="Budget period")
    spent: float = Field(description="Amount spent so far", default=0.0)
    remaining: float = Field(description="Remaining budget amount", default=0.0)
    start_date: date = Field(description="Budget period start date", default_factory=date.today)
    end_date: Optional[date] = Field(description="Budget period end date", default=None)
    notes: Optional[str] = Field(description="Budget notes or goals", default=None)
    alert_threshold: Optional[float] = Field(
        description="Percentage threshold for budget alerts (0.8 = 80%)",
        default=0.8
    )


class ShoppingHistory(BaseModel):
    """Shopping history tracking"""
    date: datetime = Field(description="Purchase date", default_factory=datetime.now)
    store: str = Field(description="Store where purchased")
    items: List[GroceryItem] = Field(description="Items purchased", default_factory=list)
    total_cost: float = Field(description="Total amount spent")
    payment_method: Optional[str] = Field(description="Payment method used", default=None)
    receipt_notes: Optional[str] = Field(description="Additional receipt notes", default=None)


# Collection schemas for managing multiple items
class UserGroceryLists(BaseModel):
    """Collection of grocery lists for a user"""
    lists: List[GroceryList] = Field(description="User's grocery lists", default_factory=list)


class UserMealPlans(BaseModel):
    """Collection of meal plans for a user"""
    plans: List[MealPlan] = Field(description="User's meal plans", default_factory=list)


class UserBudgets(BaseModel):
    """Collection of budgets for a user"""
    budgets: List[Budget] = Field(description="User's budgets", default_factory=list)


class UserShoppingHistory(BaseModel):
    """Collection of shopping history for a user"""
    history: List[ShoppingHistory] = Field(description="User's shopping history", default_factory=list) 