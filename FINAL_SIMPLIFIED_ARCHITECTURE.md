# Final Simplified Architecture

## Major Changes

Completely simplified the system by:
1. **Removed hardcoded dish databases** - No more predefined lists
2. **Removed prescribed workflow** - LLM decides everything
3. **Single menu generation tool** - Only `generate_final_menu` creates menus
4. **Full LLM autonomy** - LLM chooses which tools to call and when

## Tools (Simplified from 11 to 5)

### REMOVED Tools ❌
- ~~get_dishes_by_meal_type~~ - Had hardcoded dish lists
- ~~get_side_dishes~~ - Had hardcoded side dishes
- ~~get_beverages~~ - Had hardcoded beverages
- ~~filter_dishes~~ - No longer needed
- ~~get_available_ingredients~~ - Not essential
- ~~get_dish_details~~ - Not needed

### KEPT Tools ✅

**1. check_calendar()**
- Gets current date, day, time
- Useful for context

**2. get_meal_history(days)**
- Retrieves recent meals
- Helps avoid repetition

**3. get_user_preferences()**
- Gets taste, food style, ingredients
- From stored preferences

**4. generate_final_menu(context_json)** ⭐ KEY TOOL
- **Uses Gemini LLM** to generate complete menu
- Takes all context as input
- Returns detailed menu with:
  - Main dishes with descriptions
  - Side dishes
  - Beverages
  - Cooking times
  - Difficulty levels
  - Chef's notes
- **NO hardcoded dishes** - LLM creates everything

**5. save_meal_to_history(meal_data_json)**
- Saves meal to history
- Optional tool

## Decision Layer - Full LLM Autonomy

### OLD Approach ❌
```python
WORKFLOW (follow in order):
PHASE 1 - GATHER CONTEXT (Iteration 1):
1. Call check_calendar
2. Call get_meal_history|7
3. Call get_user_preferences

PHASE 2 - FETCH DISHES (Iteration 2-3):
4. Call get_dishes_by_meal_type|[meal_type]
5. Call get_side_dishes
...
```

**Problems**:
- Rigid workflow
- LLM had no freedom
- Unnecessary steps
- Hardcoded dishes

### NEW Approach ✅
```python
YOU DECIDE:
- Which tools to call and in what order
- How many tools you need
- When you have enough information
- When to call generate_final_menu
- When to provide FINAL_ANSWER

GUIDELINES (not strict rules):
- check_calendar: Useful for context
- get_meal_history: Helps avoid repetition
- get_user_preferences: Gets preferences
- generate_final_menu: Creates the menu (KEY TOOL)

YOU DECIDE what's appropriate based on the user's query!
```

**Benefits**:
- LLM has full autonomy
- Can be efficient (3 steps) or thorough (5 steps)
- Adapts to query complexity
- No unnecessary tool calls

## Example Workflows

### Simple Query: "suggest dinner"

**LLM decides (3 steps)**:
```
1. FUNCTION_CALL: get_user_preferences
   → Gets taste/style preferences

2. FUNCTION_CALL: generate_final_menu|{"meal_type":"dinner","preferences":{...}}
   → LLM generates complete menu

3. FINAL_ANSWER: [complete menu from tool]
   → Done!
```

### Complex Query: "suggest something for dinner which can be cooked quickly and I had dal yesterday"

**LLM decides (5 steps)**:
```
1. FUNCTION_CALL: check_calendar
   → Gets current day

2. FUNCTION_CALL: get_meal_history|7
   → Sees dal was eaten yesterday

3. FUNCTION_CALL: get_user_preferences
   → Gets preferences

4. FUNCTION_CALL: generate_final_menu|{"meal_type":"dinner","time_available":"quick","recent_meals":[...],"preferences":{...}}
   → LLM generates menu avoiding dal, quick cooking

5. FINAL_ANSWER: [complete menu]
   → Done!
```

## generate_final_menu - The Key Tool

This tool is where the magic happens:

```python
@mcp.tool()
def generate_final_menu(context_json: str) -> dict:
    """Generate complete North Indian food menu using LLM"""
    
    context = json.loads(context_json)
    
    # Initialize Gemini
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""You are an expert North Indian food menu planner.

CONTEXT:
{json.dumps(context, indent=2)}

Create a complete North Indian menu that:
1. Matches the meal type
2. Respects time constraints
3. Considers user preferences
4. Avoids recent meals
5. Is practical for home cooking

NORTH INDIAN CUISINE KNOWLEDGE:
- Breakfast: Paratha, Poha, Upma, Idli, Dosa...
- Lunch/Dinner: Dal, Sabzi, Paneer dishes, Rajma...
- Sides: Roti, Naan, Rice, Raita...
- Snacks: Samosa, Pakora, Chaat...
- Beverages: Chai, Lassi, Buttermilk...

FORMAT:
🍽️ [MEAL_TYPE] MENU

🍛 Main Dishes:
• [Dish] - [Description] ([Time] min, [Difficulty])
  Ingredients: [Key ingredients]

🥗 Side Dishes:
• [Dish] - [Description] ([Time] min, [Difficulty])

☕ Beverage:
• [Beverage] - [Description] ([Time] min)

⏱️ Total Time: [X] minutes
👥 Serves: [N] people

💡 Chef's Note:
[Why these dishes work together]"""

    response = model.generate_content(prompt)
    
    return {
        "success": True,
        "menu": response.text,
        "generated_by": "gemini-2.0-flash-exp"
    }
```

**Key Points**:
- Takes ALL context (preferences, constraints, history)
- Uses Gemini's knowledge of North Indian cuisine
- Generates specific dish names, not generic
- Includes descriptions, times, ingredients
- Adds chef's notes for context
- **NO hardcoded dishes anywhere**

## Benefits of New Architecture

### 1. Simplicity
- 5 tools instead of 11
- No hardcoded dish databases
- Clean, minimal code

### 2. Flexibility
- LLM decides workflow
- Adapts to query complexity
- Can be efficient or thorough

### 3. Intelligence
- LLM uses its knowledge of North Indian cuisine
- Creates contextually appropriate menus
- Considers all constraints

### 4. Maintainability
- No dish databases to maintain
- No workflow rules to update
- Just improve the prompt

### 5. Scalability
- Easy to add new cuisines (just update prompt)
- Easy to add new constraints
- No code changes needed

## Expected Output

```
🍽️ DINNER MENU

🍛 Main Dishes:
• Aloo Matar - Potato and peas curry with aromatic spices (30 min, Easy)
  Ingredients: Potatoes, peas, tomatoes, onions, spices
• Bhindi Masala - Crispy okra stir-fried with onions and spices (25 min, Easy)
  Ingredients: Okra, onions, tomatoes, spices

🥗 Side Dishes:
• Roti - Whole wheat flatbread, soft and warm (20 min, Easy)
  Ingredients: Wheat flour, water, ghee

☕ Beverage:
• Masala Chai - Traditional spiced tea with cardamom and ginger (10 min, Easy)
  Ingredients: Tea leaves, milk, sugar, cardamom, ginger

⏱️ Total Time: 45 minutes
👥 Serves: 2 people

💡 Chef's Note:
This menu is perfect for a quick weeknight dinner. The mild Aloo Matar balances 
the slightly tangy Bhindi Masala. Both dishes are easy to prepare and use common 
pantry ingredients. The meal is complete with fresh rotis and aromatic chai.
```

## Testing

```bash
# Test MCP server
python test_mcp.py

# Run application
export GEMINI_API_KEY='your-key'
python main.py
```

## Summary

✅ **Removed**: Hardcoded dishes, rigid workflow, unnecessary tools
✅ **Kept**: Essential context tools + one powerful menu generation tool
✅ **Result**: Simple, flexible, intelligent system where LLM has full control

The system is now **truly LLM-driven** with no hardcoded menus or prescribed workflows!
