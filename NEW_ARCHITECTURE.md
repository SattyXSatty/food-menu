# New Architecture: Following talk2mcp.py Pattern

## What Changed

Completely redesigned the decision-action loop to follow the **talk2mcp.py** pattern where the LLM responds with simple text commands instead of complex JSON.

## Old vs New

### OLD Approach ❌
```python
# LLM returns complex JSON
{
  "status": "needs_action",
  "actions_needed": [
    {"tool": "filter_dishes", "params": {...}},
    {"tool": "get_side_dishes", "params": {...}}
  ],
  "reasoning": "..."
}
```

**Problems**:
- LLM called multiple tools at once
- Got stuck in loops
- Complex JSON parsing
- Hard to debug

### NEW Approach ✅
```python
# LLM returns simple text command
"FUNCTION_CALL: get_dishes_by_meal_type|dinner"
# or
"FINAL_ANSWER: 🍽️ DINNER MENU\nMain: Dal Makhani..."
```

**Benefits**:
- ONE tool call at a time
- Clear stopping condition (FINAL_ANSWER)
- Simple parsing
- Easy to debug
- Follows proven pattern from talk2mcp.py

## New Flow

```
User Query
    ↓
Perception (questions + extraction)
    ↓
Memory (preferences)
    ↓
┌─────────────────────────────────────┐
│  Decision-Action Loop               │
│                                     │
│  Iteration 1:                       │
│    LLM → "FUNCTION_CALL: check_calendar" │
│    Execute → Result                 │
│    ↓                                │
│  Iteration 2:                       │
│    LLM → "FUNCTION_CALL: get_meal_history|7" │
│    Execute → Result                 │
│    ↓                                │
│  Iteration 3:                       │
│    LLM → "FUNCTION_CALL: get_dishes_by_meal_type|dinner" │
│    Execute → Result                 │
│    ↓                                │
│  Iteration 4:                       │
│    LLM → "FUNCTION_CALL: filter_dishes|[json]|40|Easy|any" │
│    Execute → Result                 │
│    ↓                                │
│  Iteration 5:                       │
│    LLM → "FINAL_ANSWER: 🍽️ MENU..." │
│    STOP ✅                          │
└─────────────────────────────────────┘
```

## Key Components

### 1. Decision Agent (decision.py)

**System Prompt**:
```
RESPOND WITH EXACTLY ONE LINE:
Format: FUNCTION_CALL: tool_name|param1|param2|...
Or: FINAL_ANSWER: [complete menu]

WORKFLOW:
PHASE 1 - GATHER CONTEXT (Iteration 1):
1. Call check_calendar
2. Call get_meal_history|7
3. Call get_user_preferences

PHASE 2 - FETCH DISHES (Iteration 2-3):
4. Call get_dishes_by_meal_type|[meal_type]
5. Call get_side_dishes
6. Call get_beverages

PHASE 3 - FILTER (Iteration 4):
7. Call filter_dishes with constraints

PHASE 4 - FINALIZE (Iteration 5):
8. FINAL_ANSWER: Complete menu
```

**Response Parsing**:
```python
if response_text.startswith("FUNCTION_CALL:"):
    _, function_info = response_text.split(":", 1)
    parts = function_info.split("|")
    tool_name = parts[0]
    params = parts[1:]
    return {"type": "tool_call", "tool_name": tool_name, "params": params}

elif response_text.startswith("FINAL_ANSWER:"):
    final_answer = response_text.split(":", 1)[1].strip()
    return {"type": "final_answer", "final_response": final_answer}
```

### 2. Main Loop (main.py)

**Simple Loop**:
```python
while iteration < max_iterations:
    # Get decision from LLM
    decision = decision.make_decision(facts, memory, history, tools)
    
    if decision["type"] == "final_answer":
        print(decision["final_response"])
        break
    
    elif decision["type"] == "tool_call":
        result = await call_mcp_tool(session, decision["tool_name"], decision["params"])
        action_history.append({"tool_name": ..., "result": result})
```

**No Complex Logic**:
- No nested loops
- No multiple tool calls per iteration
- No complex state management
- Just: ask LLM → execute → repeat

### 3. Tool Calling (main.py)

**Parameter Handling**:
```python
async def call_mcp_tool(session, tool_name, params, tools):
    # Find tool schema
    tool = next((t for t in tools if t.name == tool_name), None)
    
    # Convert params to correct types based on schema
    arguments = {}
    for param_name, param_info in tool.inputSchema['properties'].items():
        param_type = param_info['type']
        if param_type == 'integer':
            arguments[param_name] = int(params[i])
        elif param_type == 'array':
            arguments[param_name] = [int(x) for x in params[i].split(',')]
        else:
            arguments[param_name] = str(params[i])
    
    # Call tool
    result = await session.call_tool(tool_name, arguments)
    return result
```

## Advantages

1. **Simplicity**: One tool at a time, clear flow
2. **Debuggability**: Easy to see what LLM decided
3. **Control**: Clear stopping condition (FINAL_ANSWER)
4. **Proven Pattern**: Based on working talk2mcp.py example
5. **No Loops**: LLM can't get stuck calling same tool repeatedly
6. **Flexible**: LLM decides order of tools based on context

## Example Session

```
Iteration 1:
  LLM → FUNCTION_CALL: check_calendar
  Result → {"date": "2025-10-17", "day": "Friday"}

Iteration 2:
  LLM → FUNCTION_CALL: get_meal_history|7
  Result → {"recent_meals": [], "count": 0}

Iteration 3:
  LLM → FUNCTION_CALL: get_dishes_by_meal_type|dinner
  Result → {"dishes": [{"name": "Dal Makhani", ...}, ...], "count": 6}

Iteration 4:
  LLM → FUNCTION_CALL: filter_dishes|[dishes_json]|40|Easy|any
  Result → {"filtered_dishes": [{"name": "Aloo Matar", ...}], "count": 2}

Iteration 5:
  LLM → FINAL_ANSWER: 🍽️ DINNER MENU
       Main: Aloo Matar (30 min, Easy)
       Side: Roti (20 min, Easy)
       Beverage: Masala Chai (10 min, Easy)
  DONE ✅
```

## Testing

```bash
# Install dependencies
uv sync

# Test MCP server
python test_mcp.py

# Run application
export GEMINI_API_KEY='your-key'
python main.py
```

Query: "suggest something for dinner which can be cooked quickly"

Expected:
- 5-6 iterations
- One tool call per iteration
- Final answer with complete menu
- No loops or repetition

## Migration Notes

- Removed complex `DecisionOutput` Pydantic model
- Simplified to dict with `type`, `tool_name`, `params`, `final_response`
- Removed `actions_needed` list (only one action at a time)
- Removed `status` field (use `type` instead)
- Added clear FUNCTION_CALL and FINAL_ANSWER formats
- Follows talk2mcp.py pattern exactly
