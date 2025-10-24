# Fixes Applied

## Error 1: Meal Type Not Extracted from Query

**Problem**: User said "dinner" but system extracted "lunch"

**Root Cause**: 
- LLM wasn't explicitly instructed to extract meal type from query
- Fallback extraction defaulted to "lunch"

**Fixes Applied**:

1. **perception.py** - Updated extraction prompt:
```python
CRITICAL: 
- If user mentions "dinner", meal_type MUST be "dinner"
- If user mentions "breakfast", meal_type MUST be "breakfast"
- If user mentions "lunch", meal_type MUST be "lunch"
- If user mentions "snacks", meal_type MUST be "snacks"
```

2. **perception.py** - Improved fallback extraction:
```python
def _fallback_extraction(self, user_query: str) -> ExtractedFacts:
    # Try to detect meal type from query
    query_lower = user_query.lower()
    meal_type = "lunch"  # default
    if "breakfast" in query_lower:
        meal_type = "breakfast"
    elif "dinner" in query_lower:
        meal_type = "dinner"
    elif "snack" in query_lower:
        meal_type = "snacks"
    elif "lunch" in query_lower:
        meal_type = "lunch"
```

## Error 2: Pydantic Validation Error

**Problem**: 
```
1 validation error for ExtractedFacts
specific_requests
  Input should be a valid string [type=string_type, input_value=[], input_type=list]
```

**Root Cause**: 
- LLM returned `specific_requests` as a list `[]` instead of string
- Pydantic model expected string

**Fixes Applied**:

1. **models.py** - Updated ExtractedFacts model:
```python
class ExtractedFacts(BaseModel):
    specific_requests: Optional[str] = ""  # Default to empty string
    
    class Config:
        str_strip_whitespace = True
```

2. **perception.py** - Added data cleaning before validation:
```python
# Clean up data before validation
if "specific_requests" in data:
    if isinstance(data["specific_requests"], list):
        data["specific_requests"] = " ".join(str(x) for x in data["specific_requests"])
    elif data["specific_requests"] is None:
        data["specific_requests"] = ""

# Ensure lists are lists
for field in ["dietary_restrictions", "constraints"]:
    if field in data and not isinstance(data[field], list):
        data[field] = []
```

3. **perception.py** - Updated extraction prompt:
```python
- specific_requests: string with any specific dishes or ingredients mentioned (empty string if none)

CRITICAL: 
- specific_requests must be a STRING, not a list
```

## Error 3: TypeError in Main Loop

**Problem**:
```
TypeError: sequence item 0: expected str instance, dict found
```

**Root Cause**: 
- `actions_needed` can now be a list of dicts `[{"tool": "name", "params": {...}}]`
- Code tried to join them as strings

**Fixes Applied**:

**main.py** - Handle both string and dict formats:
```python
if decision_output.actions_needed:
    # Handle both string and dict formats
    actions_str = []
    for action in decision_output.actions_needed:
        if isinstance(action, dict):
            actions_str.append(action.get("tool", str(action)))
        else:
            actions_str.append(str(action))
    print(f"   Actions Needed: {', '.join(actions_str)}")
```

## Summary

All three errors have been fixed:

1. ✅ Meal type now correctly extracted from user query
2. ✅ Pydantic validation handles LLM returning lists/None for string fields
3. ✅ Main loop handles both string and dict action formats

## Testing

Run the test to verify MCP tools work:
```bash
uv sync
python test_mcp.py
```

Run the full application:
```bash
export GEMINI_API_KEY='your-key'
python main.py
```

Test with: "suggest something for dinner which can be cooked quickly"
- Should extract meal_type="dinner"
- Should extract time_available="quick"
- Should call appropriate MCP tools
