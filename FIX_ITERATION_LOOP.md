# Fix: Decision Layer Stuck in Loop

## Problem

The decision layer was getting stuck in a loop, repeatedly calling `filter_dishes` and exhausting all 5 iterations without providing a final result.

**Observed Behavior**:
- Iteration 3: Received filtered dishes ✅
- Iteration 4: Called filter_dishes again ❌
- Iteration 5: Called filter_dishes again ❌
- Max iterations reached without final menu ❌

## Root Cause

1. **No clear stopping condition**: LLM wasn't explicitly told when to stop
2. **Repetitive tool calls**: LLM kept calling the same tool multiple times
3. **No forced completion**: System allowed LLM to continue indefinitely
4. **Unclear iteration guidance**: Prompt didn't specify what to do at each iteration

## Fixes Applied

### 1. Updated System Prompt with Strict Rules

```python
STRICT DECISION PROCESS (MAX 5 ITERATIONS):
- Iteration 1: Call check_calendar, get_meal_history, get_user_preferences
- Iteration 2: Call get_dishes_by_meal_type, get_side_dishes, get_beverages
- Iteration 3: Call filter_dishes ONCE for main dishes (if needed)
- Iteration 4: Call get_dish_details for 2-3 selected dishes, then set status="complete"
- Iteration 5: MUST set status="complete" with final menu

CRITICAL RULES:
- DO NOT call filter_dishes multiple times in one iteration
- DO NOT repeat the same tool calls
- After iteration 3, you MUST have enough data to create a menu
- Iteration 4 or 5 MUST set status="complete"
```

### 2. Added Iteration-Specific Instructions

```python
CRITICAL INSTRUCTIONS FOR ITERATION {iteration}:
- This is iteration 1: Call check_calendar, get_meal_history, get_user_preferences
- This is iteration 2: Call get_dishes_by_meal_type, get_side_dishes, get_beverages
- This is iteration 3: Call filter_dishes ONCE to filter main dishes
- This is iteration 4+: You MUST set status='complete' and provide final_response

STOP CALLING TOOLS! You have enough data. Compile the final menu from action_history.
```

### 3. Forced Completion After Iteration 4

```python
# Force completion after iteration 4
if iteration >= 4 and data.get("status") != "complete":
    print(f"⚠️  Forcing completion at iteration {iteration}")
    data["status"] = "complete"
    if not data.get("final_response"):
        data["final_response"] = self._compile_menu_from_history(action_history, perceived_facts)
    data["actions_needed"] = None
```

### 4. Added Menu Compilation Helper

```python
def _compile_menu_from_history(self, action_history: list, perceived_facts: ExtractedFacts) -> str:
    """Compile final menu from action history"""
    menu_parts = [f"🍽️  {perceived_facts.meal_type.upper()} MENU\n"]
    
    # Extract filtered dishes from last few iterations
    for action in reversed(action_history[-3:]):
        results = action.get("results", {})
        
        # Check for filtered main dishes
        if "filter_dishes" in results:
            filtered = results["filter_dishes"].get("filtered_dishes", [])
            if filtered and len(filtered) > 0:
                menu_parts.append("\n🍛 Main Dishes:")
                for dish in filtered[:2]:  # Take first 2
                    name = dish.get("name", "Unknown")
                    time = dish.get("time", "?")
                    difficulty = dish.get("difficulty", "?")
                    menu_parts.append(f"• {name} ({time} min, {difficulty})")
                break
        
        # Add sides and beverages...
    
    return "\n".join(menu_parts)
```

### 5. Updated Fallback Decision Logic

```python
else:
    # Iteration 4+: MUST complete
    final_menu = self._compile_menu_from_history(action_history, perceived_facts)
    
    return DecisionOutput(
        status="complete",
        reasoning="Menu compiled from filtered results",
        final_response=final_menu,
        iteration=iteration
    )
```

## Expected Behavior Now

**Iteration 1**: Gather context (calendar, history, preferences)
**Iteration 2**: Fetch dishes (main, sides, beverages)
**Iteration 3**: Filter dishes based on constraints
**Iteration 4**: **COMPLETE** - Compile and return final menu ✅

## Testing

Run the application:
```bash
python main.py
```

Query: "suggest something for dinner which can be cooked quickly"

Expected flow:
1. ✅ Iteration 1: Context gathering
2. ✅ Iteration 2: Fetch dinner dishes
3. ✅ Iteration 3: Filter by time (quick = max 40 min)
4. ✅ Iteration 4: **STATUS=COMPLETE** with final menu

No more infinite loops! 🎉

## Key Improvements

1. ✅ Clear iteration boundaries
2. ✅ Explicit stopping conditions
3. ✅ Forced completion after iteration 4
4. ✅ Menu compilation from tool results
5. ✅ No repetitive tool calls
6. ✅ Fallback menu generation
