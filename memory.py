"""
Memory Agent
Stores and retrieves user preferences using Pydantic models
"""
import os
import json
from models import UserPreferences

class MemoryAgent:
    def __init__(self):
        self.preferences_file = "user_preferences.json"
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> UserPreferences:
        """Load preferences from file"""
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    return UserPreferences(**data)
            except Exception as e:
                print(f"⚠️  Error loading preferences: {e}")
        
        # Return predefined default preferences
        return UserPreferences(
            taste="spicy",
            food_style="modern",
            ingredients=["wheat flour", "pulses", "rice"],
            dietary_type="vegetarian",
            avoid_ingredients=[],
            meal_history=[]
        )
    
    def _save_preferences(self):
        """Save preferences to file"""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences.model_dump(), f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving preferences: {e}")
    
    def get_preferences(self) -> UserPreferences:
        """Retrieve user preferences"""
        return self.preferences
    
    def update_preferences(self, new_data: dict):
        """Update preferences with new information"""
        # Add to meal history
        if "meal_type" in new_data:
            self.preferences.meal_history.append(new_data)
            # Keep only last 30 meals
            if len(self.preferences.meal_history) > 30:
                self.preferences.meal_history = self.preferences.meal_history[-30:]
        
        self._save_preferences()
    
    def add_meal_to_history(self, meal_data: dict):
        """Add a meal to history"""
        self.preferences.meal_history.append(meal_data)
        if len(self.preferences.meal_history) > 30:
            self.preferences.meal_history = self.preferences.meal_history[-30:]
        self._save_preferences()
