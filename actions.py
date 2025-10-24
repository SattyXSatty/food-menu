"""
Actions Agent - MCP Server using FastMCP
Provides pure MCP tools - NO hardcoded menus or dishes
"""
from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("North Indian Food Menu Tools")

# ============================================================================
# TOOL 1: Get Current Date/Time/Day
# ============================================================================
@mcp.tool()
def check_calendar() -> dict:
    """Get current date, day of week, and time information"""
    print("CALLED: check_calendar()")
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "day": now.strftime("%A"),
        "time": now.strftime("%H:%M"),
        "is_weekend": now.weekday() >= 5,
        "month": now.strftime("%B"),
        "year": now.year
    }

# ============================================================================
# TOOL 2: Get Meal History
# ============================================================================
@mcp.tool()
def get_meal_history(days: int = 7) -> dict:
    """
    Retrieve recent meal history to avoid repetition
    
    Args:
        days: Number of days to look back (default: 7)
    """
    print(f"CALLED: get_meal_history(days={days})")
    try:
        if os.path.exists("user_preferences.json"):
            with open("user_preferences.json", 'r') as f:
                prefs = json.load(f)
                history = prefs.get("meal_history", [])
                recent = history[-days:] if len(history) > days else history
                return {
                    "recent_meals": recent,
                    "count": len(recent),
                    "note": f"Last {len(recent)} meals retrieved"
                }
    except Exception as e:
        print(f"Error reading meal history: {e}")
    
    return {
        "recent_meals": [],
        "count": 0,
        "note": "No meal history found"
    }

# ============================================================================
# TOOL 3: Get User Preferences
# ============================================================================
@mcp.tool()
def get_user_preferences() -> dict:
    """Get stored user preferences"""
    print("CALLED: get_user_preferences()")
    
    try:
        if os.path.exists("user_preferences.json"):
            with open("user_preferences.json", 'r') as f:
                prefs = json.load(f)
                # Don't return full history, just preferences
                return {
                    "taste": prefs.get("taste", "spicy"),
                    "food_style": prefs.get("food_style", "modern"),
                    "ingredients": prefs.get("ingredients", ["wheat flour", "pulses", "rice"]),
                    "dietary_type": prefs.get("dietary_type", "vegetarian"),
                    "avoid_ingredients": prefs.get("avoid_ingredients", [])
                }
    except:
        pass
    
    # Default preferences
    return {
        "taste": "spicy",
        "food_style": "modern",
        "ingredients": ["wheat flour", "pulses", "rice"],
        "dietary_type": "vegetarian",
        "avoid_ingredients": []
    }

# ============================================================================
# TOOL 4: Generate Final Menu (LLM-powered)
# ============================================================================
@mcp.tool()
def generate_final_menu(context_json: str) -> dict:
    """
    Generate complete North Indian food menu using LLM based on all context
    
    Args:
        context_json: JSON string with all context (meal_type, preferences, constraints, etc.)
    """
    print("CALLED: generate_final_menu()")
    print(f"Context received: {context_json[:200]}...")
    
    try:
        context = json.loads(context_json)
        print(f"Parsed context keys: {list(context.keys())}")
    except Exception as e:
        print(f"Error parsing context: {e}")
        return {
            "success": False,
            "error": "Invalid context JSON",
            "menu": "Error: Could not parse context"
        }
    
    # Initialize Gemini
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"API Key status: {'Found' if api_key else 'NOT FOUND'}")
    if api_key:
        print(f"API Key length: {len(api_key)} chars")
    
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set!")
        print("Please set it with: export GEMINI_API_KEY='your-key'")
        return {
            "success": False,
            "error": "GEMINI_API_KEY not set",
            "menu": "Error: Cannot generate menu without API key. Please set GEMINI_API_KEY environment variable."
        }
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Build comprehensive prompt
        prompt = f"""You are an expert North Indian food menu planner.  
Generate a complete, detailed, and practical menu for home cooking.

────────────────────────────
CONTEXT PROVIDED:
{json.dumps(context, indent=2)}

────────────────────────────
YOUR TASK
Create a complete North Indian menu that:
1. Matches the meal type (breakfast/lunch/dinner/snacks)  
2. Respects time constraints:  
   • quick = 30–40 min • normal = 45–60 min • elaborate = 60+ min  
3. Considers user preferences (taste, style, preferred ingredients)  
4. Avoids dishes from recent meal history (if provided)  
5. Is realistic for home cooking  
6. Includes 2–3 main dishes, 1–2 sides, and 1 beverage  

────────────────────────────
REASONING FRAMEWORK
Before producing the output, **think step-by-step**:
1. Analyze the context → determine meal type, time, preferences, constraints.  
2. Plan dishes that balance nutrition, flavor, and cooking time.  
3. Verify: ensure dishes match time and difficulty constraints, and complement each other.  
4. If any info is missing or conflicting → make a reasonable assumption and mention it briefly in the Chef’s Note.  
5. Finally, format the menu strictly as per the template below.

────────────────────────────
NORTH INDIAN CUISINE KNOWLEDGE
- **Breakfast:** Paratha, Poha, Upma, Aloo Puri, Chole Bhature  
- **Lunch/Dinner:** Dal, Paneer, Rajma, Chole, Sabzi, Rice dishes  
- **Sides:** Roti, Naan, Rice, Raita, Salad, Papad  
- **Snacks:** Samosa, Pakora, Chaat, Kachori, Dhokla  
- **Beverages:** Chai, Lassi, Buttermilk, Shikanji  

────────────────────────────
FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

🍽️ [MEAL_TYPE] MENU

🍛 **Main Dishes:**
• [Dish Name] – [Brief description] ([Cooking time] min, [Difficulty: Easy/Medium/Hard])  
  Ingredients: [Key ingredients]  
• [Dish Name] – [Brief description] ([Cooking time] min, [Difficulty])  
  Ingredients: [Key ingredients]

🥗 **Side Dishes:**
• [Dish Name] – [Brief description] ([Cooking time] min, [Difficulty])  
  Ingredients: [Key ingredients]

☕ **Beverage:**
• [Drink Name] – [Brief description] ([Cooking time] min, [Difficulty])  
  Ingredients: [Key ingredients]

⏱️ **Total Time:** [Total cooking time] minutes  
👥 **Serves:** [Number of people]

💡 **Chef's Note
"""

        response = model.generate_content(prompt)
        menu_text = response.text.strip()
        
        print(f"Generated menu length: {len(menu_text)} chars")
        print(f"Generated menu preview: {menu_text[:200]}...")
        
        return {
            "success": True,
            "menu": menu_text,
            "generated_by": "gemini-2.0-flash-exp"
        }
        
    except Exception as e:
        print(f"Error generating menu with LLM: {e}")
        return {
            "success": False,
            "error": str(e),
            "menu": f"Error generating menu: {str(e)}"
        }

# ============================================================================
# TOOL 5: Save Meal to History
# ============================================================================
@mcp.tool()
def save_meal_to_history(meal_data_json: str) -> dict:
    """
    Save a meal to history
    
    Args:
        meal_data_json: JSON string with meal information
    """
    print(f"CALLED: save_meal_to_history()")
    
    try:
        meal_data = json.loads(meal_data_json)
        
        # Load existing preferences
        prefs = {}
        if os.path.exists("user_preferences.json"):
            with open("user_preferences.json", 'r') as f:
                prefs = json.load(f)
        
        # Add timestamp
        meal_data["timestamp"] = datetime.now().isoformat()
        
        # Add to history
        if "meal_history" not in prefs:
            prefs["meal_history"] = []
        
        prefs["meal_history"].append(meal_data)
        
        # Keep only last 30 meals
        if len(prefs["meal_history"]) > 30:
            prefs["meal_history"] = prefs["meal_history"][-30:]
        
        # Save
        with open("user_preferences.json", 'w') as f:
            json.dump(prefs, f, indent=2)
        
        return {
            "success": True,
            "message": "Meal saved to history",
            "total_meals": len(prefs["meal_history"])
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import sys
    print("🚀 Starting North Indian Food Menu MCP Server...")
    mcp.run(transport="stdio")
