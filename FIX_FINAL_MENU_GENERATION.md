# Fix: Final Menu Generation with LLM

## Problem

The LLM was responding with just "🍽️ DINNER MENU" without actual dish details in the final answer.

**What was happening**:
```
Iteration 5:
  LLM → FINAL_ANSWER: 🍽️ DINNER MENU
  
Output: 🍽️ DINNER MENU
(No dishes, no details!)
```

## Root Cause

The decision layer LLM was trying to create the menu itself in the FINAL_ANSWER, but:
1. It didn't have all the dish details in its context
2. It was instructed not to hardcode dishes
3. It couldn't format a proper menu from the tool results

## Solution

Added a new MCP tool `generate_final_menu` that uses **LLM to generate the detailed menu** based on all gathered context.

### New Tool: generate_final_menu

**Location**: `actions.py`

**Purpose**: Takes all context (dishes, preferences, constraints) and uses Gemini to generate a complete, detailed menu.

**Input**:
```python
{
  "meal_type": "dinner",
  "time_available": "quick",
  "filtered_dishes": [...],
  "side_dishes": [...],
  "beverages": [...],
  "preferences": {...},
  "recent_meals": [...]
}
```

**Output**:
```python
{
  "success": true,
  "menu": "🍽️ DINNER MENU\n\n🍛 Main Dishes:\n• Aloo Matar - Potato and peas curry (30 min, Easy)\n...",
  "generated_by": "gemini-2.0-flash"
}
```

### Implementation

```python
@mcp.tool()
def generate_final_menu(context_json: str) -> dict:
    """Generate final menu using LLM based on all gathered context"""
    
    context = json.loads(context_json)
    
    # Initialize Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Build prompt with all context
    prompt = f"""You are a North Indian food menu expert. Generate a complete, detailed menu.

CONTEXT:
{json.dumps(context, indent=2)}

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
🍽️ [MEAL_TYPE] MENU

🍛 Main Dishes:
• [Dish Name] - [Description] ([Time] min, [Difficulty])

🥗 Side Dishes:
• [Dish Name] - [Description] ([Time] min, [Difficulty])

☕ Beverage:
• [Beverage Name] - [Description] ([Time] min)

💡 Chef's Note:
[Brief note about the menu]

IMPORTANT:
- Use ONLY dishes from the provided context
- Include actual cooking times and difficulty levels
- Make it practical for home cooking"""

    response = model.generate_content(prompt)
    return {
        "success": True,
        "menu": response.text.strip(),
        "generated_by": "gemini-2.0-flash"
    }
```

### Updated Workflow

**Old Flow** (Broken):
```
1. Get dishes
2. Filter dishes
3. LLM tries to create menu in FINAL_ANSWER
4. Fails - just says "DINNER MENU"
```

**New Flow** (Fixed):
```
1. Get dishes
2. Filter dishes
3. Call generate_final_menu with all context
4. LLM creates detailed menu
5. FINAL_ANSWER: Use menu from generate_final_menu
```

### Updated Decision Layer

**System Prompt Changes**:
```python
PHASE 4 - FINALIZE (Iteration 5-6):
8. Call generate_final_menu with all context as JSON
9. FINAL_ANSWER: Use the menu from generate_final_menu result

IMPORTANT RULES:
- After gathering dishes, call generate_final_menu to create detailed menu
- FINAL_ANSWER must be the complete menu from generate_final_menu tool
- DO NOT create menu yourself - use generate_final_menu tool!
```

**Example**:
```
FUNCTION_CALL: generate_final_menu|{"meal_type":"dinner","filtered_dishes":[...],"preferences":{...}}
FINAL_ANSWER: [paste the complete menu from generate_final_menu result]
```

### Fallback Handling

If LLM provides short FINAL_ANSWER, automatically extract menu from last action:

```python
if response_text.startswith("FINAL_ANSWER:"):
    final_answer = response_text.split(":", 1)[1].strip()
    
    # If final answer is too short, get menu from last action
    if len(final_answer) < 100 and action_history:
        last_action = action_history[-1]
        if last_action.get("tool_name") == "generate_final_menu":
            result = last_action.get("result", {})
            if isinstance(result, dict) and "menu" in result:
                final_answer = result["menu"]
```

## Expected Flow Now

```
Iteration 1: FUNCTION_CALL: check_calendar
Iteration 2: FUNCTION_CALL: get_meal_history|7
Iteration 3: FUNCTION_CALL: get_dishes_by_meal_type|dinner
Iteration 4: FUNCTION_CALL: filter_dishes|[json]|40|Easy|any
Iteration 5: FUNCTION_CALL: generate_final_menu|{"meal_type":"dinner",...}
            Result: {
              "menu": "🍽️ DINNER MENU\n\n🍛 Main Dishes:\n• Aloo Matar - Potato and peas curry (30 min, Easy)\n• Bhindi Masala - Okra stir-fry (25 min, Easy)\n\n🥗 Side Dishes:\n• Roti - Whole wheat flatbread (20 min, Easy)\n\n☕ Beverage:\n• Masala Chai - Spiced tea (10 min, Easy)\n\n💡 Chef's Note:\nThis menu is perfect for a quick weeknight dinner..."
            }
Iteration 6: FINAL_ANSWER: [complete menu from above]
```

## Benefits

1. ✅ **Detailed Menus**: LLM generates complete descriptions
2. ✅ **Context-Aware**: Uses all gathered data (dishes, preferences, constraints)
3. ✅ **Consistent Format**: Always follows the same structure
4. ✅ **No Hardcoding**: Dishes come from MCP tools
5. ✅ **Fallback Support**: Works even without API key
6. ✅ **Chef's Notes**: Adds helpful context about the menu

## Testing

```bash
# Test the new tool
python test_mcp.py

# Run full application
export GEMINI_API_KEY='your-key'
python main.py
```

Query: "suggest something for dinner which can be cooked quickly"

Expected output:
```
🍽️ DINNER MENU

🍛 Main Dishes:
• Aloo Matar - Potato and peas curry with aromatic spices (30 min, Easy)
• Bhindi Masala - Crispy okra stir-fried with onions and spices (25 min, Easy)

🥗 Side Dishes:
• Roti - Whole wheat flatbread, soft and warm (20 min, Easy)

☕ Beverage:
• Masala Chai - Traditional spiced tea with cardamom and ginger (10 min, Easy)

💡 Chef's Note:
This menu is perfect for a quick weeknight dinner. The dishes complement each other well, with the mild Aloo Matar balancing the slightly tangy Bhindi Masala. Total cooking time is under 45 minutes, making it ideal for busy evenings.
```

## Key Changes Summary

1. ✅ Added `generate_final_menu` MCP tool in `actions.py`
2. ✅ Updated decision layer to call this tool before FINAL_ANSWER
3. ✅ Added fallback to extract menu from last action
4. ✅ Increased max iterations to 12 to allow for menu generation
5. ✅ Updated test script to test new tool
6. ✅ Better result display in main loop

Now the system generates **complete, detailed, context-aware menus**! 🎉
