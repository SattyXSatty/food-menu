"""
Pydantic models for structured input/output
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Perception Models
class UserQuery(BaseModel):
    query: str
    timestamp: str

class GeneratedQuestions(BaseModel):
    questions: List[str]
    reasoning: Optional[str] = None

class ExtractedFacts(BaseModel):
    meal_type: str
    number_of_people: int = 2
    time_available: str = "normal"  # quick, normal, elaborate
    dietary_restrictions: List[str] = []
    occasion: str = "regular"
    specific_requests: Optional[str] = ""
    constraints: List[str] = []
    
    class Config:
        # Allow LLM to return empty list/string for optional fields
        str_strip_whitespace = True

# Memory Models
class UserPreferences(BaseModel):
    taste: str = "spicy"
    food_style: str = "modern"
    ingredients: List[str] = ["wheat flour", "pulses", "rice"]
    dietary_type: str = "vegetarian"
    avoid_ingredients: List[str] = []
    meal_history: List[Dict[str, Any]] = []

# Decision Models
class DecisionOutput(BaseModel):
    status: str  # "needs_action" or "complete"
    actions_needed: Optional[List[Any]] = None  # Can be list of strings or dicts with tool/params
    reasoning: str
    final_response: Optional[str] = None
    iteration: int = 1

class ActionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}

# Action Models
class CalendarInfo(BaseModel):
    date: str
    day: str
    time: str
    is_weekend: bool

class MealHistoryInfo(BaseModel):
    recent_meals: List[Dict[str, Any]]
    count: int
    note: str = ""

class MenuResponse(BaseModel):
    menu: str
    generated: bool
    note: str = ""

class ActionResult(BaseModel):
    tool_name: str
    result: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
