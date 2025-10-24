# System Architecture

## Overview

This is a multi-agent cognitive AI system for North Indian food menu suggestions, implementing:
- **MCP (Model Context Protocol)** for tool execution
- **Pydantic** for structured data validation
- **Feedback loops** for iterative decision-making
- **LLM-driven tool selection** via Gemini 2 Flash

## Components

### 1. Main.py - Orchestrator
**Role**: Coordinates all agents and manages MCP client

**Flow**:
1. Initializes all agents
2. Collects user query
3. Manages perception → memory → decision loop
4. Establishes MCP connection to actions.py
5. Runs decision-action feedback loop
6. Returns final result

**Key Features**:
- Async MCP client using `stdio_client`
- Pydantic model validation
- Action history tracking
- Iteration limit (max 5)

### 2. Perception.py - Understanding Layer
**Role**: Extracts structured facts from user conversation

**Capabilities**:
- Generates clarifying questions based on user query
- Collects user responses interactively
- Extracts facts into `ExtractedFacts` Pydantic model

**LLM Usage**:
- Gemini 2 Flash with JSON mode
- Structured output via Pydantic

**Output Model**:
```python
ExtractedFacts(
    meal_type: str,
    number_of_people: int,
    time_available: str,
    dietary_restrictions: List[str],
    occasion: str,
    specific_requests: Optional[str],
    constraints: List[str]
)
```

### 3. Memory.py - Preference Storage
**Role**: Manages user preferences and meal history

**Predefined Preferences**:
- `taste: "spicy"`
- `food_style: "modern"`
- `ingredients: ["wheat flour", "pulses", "rice"]`
- `dietary_type: "vegetarian"`

**Features**:
- Persistent storage in `user_preferences.json`
- Pydantic `UserPreferences` model
- Meal history tracking (last 30 meals)
- Automatic save/load

### 4. Decision.py - Decision Making
**Role**: Analyzes context and decides which MCP tools to call

**Decision Process**:
1. Receives: perceived facts, memory, action history
2. Analyzes: what information is missing
3. Decides: which MCP tools to call
4. Evaluates: is information sufficient?
5. Returns: `DecisionOutput` with status and actions

**LLM Usage**:
- Gemini 2 Flash with JSON mode
- Structured output via Pydantic
- Tool selection based on context

**Output Model**:
```python
DecisionOutput(
    status: str,  # "needs_action" or "complete"
    actions_needed: Optional[List[str]],
    reasoning: str,
    final_response: Optional[str],
    iteration: int
)
```

### 5. Actions.py - MCP Server
**Role**: Provides MCP tools for external actions

**MCP Tools**:

1. **check_calendar**
   - Parameters: None
   - Returns: `CalendarInfo` (date, day, time, is_weekend)
   - Use: Context about current time

2. **get_meal_history**
   - Parameters: `days` (default: 7)
   - Returns: `MealHistoryInfo` (recent_meals, count)
   - Use: Avoid repetition

3. **check_ingredients**
   - Parameters: None
   - Returns: Available ingredients list
   - Use: Verify what's available

4. **generate_menu**
   - Parameters: `meal_type`, `preferences`
   - Returns: `MenuResponse` (menu, generated, note)
   - Use: Create final menu

**Implementation**:
- MCP Server using `mcp.server`
- Stdio communication
- Pydantic models for all outputs
- Async tool handlers

### 6. Models.py - Data Structures
**Role**: Defines all Pydantic models for type safety

**Models**:
- `UserQuery` - Initial user input
- `GeneratedQuestions` - Questions from perception
- `ExtractedFacts` - Structured user requirements
- `UserPreferences` - Memory preferences
- `DecisionOutput` - Decision layer output
- `CalendarInfo` - Calendar tool output
- `MealHistoryInfo` - History tool output
- `MenuResponse` - Menu generation output
- `ActionResult` - Generic action result

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│                  "I want light lunch"                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Generate Questions (LLM)                          │  │
│  │    → GeneratedQuestions model                        │  │
│  │ 2. Collect Responses (User Input)                    │  │
│  │ 3. Extract Facts (LLM)                               │  │
│  │    → ExtractedFacts model                            │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      MEMORY LAYER                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Load Preferences                                     │  │
│  │    → UserPreferences model                           │  │
│  │    • taste: spicy                                    │  │
│  │    • food_style: modern                              │  │
│  │    • ingredients: [wheat, pulses, rice]             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP CONNECTION                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ stdio_client → actions.py (MCP Server)               │  │
│  │ Available Tools:                                     │  │
│  │   • check_calendar                                   │  │
│  │   • get_meal_history                                 │  │
│  │   • check_ingredients                                │  │
│  │   • generate_menu                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DECISION-ACTION FEEDBACK LOOP                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ITERATION 1                                         │  │
│  │ ┌─────────────────────────────────────────────────┐ │  │
│  │ │ Decision (LLM):                                 │ │  │
│  │ │   Analyze: ExtractedFacts + UserPreferences     │ │  │
│  │ │   Decide: Need calendar & history               │ │  │
│  │ │   → DecisionOutput(                             │ │  │
│  │ │       status="needs_action",                    │ │  │
│  │ │       actions=["check_calendar",                │ │  │
│  │ │                "get_meal_history"]              │ │  │
│  │ │     )                                           │ │  │
│  │ └─────────────────────────────────────────────────┘ │  │
│  │                        ↓                            │  │
│  │ ┌─────────────────────────────────────────────────┐ │  │
│  │ │ Actions (MCP Tools):                            │ │  │
│  │ │   Call: check_calendar                          │ │  │
│  │ │     → CalendarInfo(date, day, time)             │ │  │
│  │ │   Call: get_meal_history                        │ │  │
│  │ │     → MealHistoryInfo(recent_meals)             │ │  │
│  │ └─────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ITERATION 2                                         │  │
│  │ ┌─────────────────────────────────────────────────┐ │  │
│  │ │ Decision (LLM):                                 │ │  │
│  │ │   Analyze: Previous results + context           │ │  │
│  │ │   Decide: Ready to generate menu                │ │  │
│  │ │   → DecisionOutput(                             │ │  │
│  │ │       status="needs_action",                    │ │  │
│  │ │       actions=["generate_menu"]                 │ │  │
│  │ │     )                                           │ │  │
│  │ └─────────────────────────────────────────────────┘ │  │
│  │                        ↓                            │  │
│  │ ┌─────────────────────────────────────────────────┐ │  │
│  │ │ Actions (MCP Tools):                            │ │  │
│  │ │   Call: generate_menu                           │ │  │
│  │ │     → MenuResponse(menu, generated)             │ │  │
│  │ └─────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ITERATION 3                                         │  │
│  │ ┌─────────────────────────────────────────────────┐ │  │
│  │ │ Decision (LLM):                                 │ │  │
│  │ │   Analyze: All results collected                │ │  │
│  │ │   Decide: Information sufficient                │ │  │
│  │ │   → DecisionOutput(                             │ │  │
│  │ │       status="complete",                        │ │  │
│  │ │       final_response="[Complete Menu]"          │ │  │
│  │ │     )                                           │ │  │
│  │ └─────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      FINAL OUTPUT                           │
│                   Complete Menu with:                       │
│                   • Dishes                                  │
│                   • Cooking times                           │
│                   • Ingredients                             │
│                   • Difficulty levels                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. MCP Implementation
- **Why**: Proper separation of concerns, tools as services
- **How**: Actions.py runs as independent MCP server
- **Benefit**: Tools can be reused, tested independently

### 2. Pydantic Models
- **Why**: Type safety, validation, documentation
- **How**: All data flows through Pydantic models
- **Benefit**: Catch errors early, clear contracts

### 3. Feedback Loop
- **Why**: LLM needs multiple steps to gather information
- **How**: Decision layer evaluates and requests more tools
- **Benefit**: Flexible, adaptive decision-making

### 4. Structured Output
- **Why**: Reliable parsing, no hallucination
- **How**: Gemini JSON mode + Pydantic validation
- **Benefit**: Consistent, predictable outputs

### 5. Predefined Memory
- **Why**: Consistent baseline preferences
- **How**: Default values in UserPreferences model
- **Benefit**: Works immediately, customizable

## Extension Points

### Add New MCP Tools
1. Define tool in `actions.py` `@app.list_tools()`
2. Implement handler in `@app.call_tool()`
3. Create Pydantic model in `models.py`
4. LLM will automatically discover and use it

### Add New Agents
1. Create new agent file (e.g., `nutrition.py`)
2. Define Pydantic models for I/O
3. Integrate in `main.py` orchestration
4. Update decision layer to use new agent

### Integrate External APIs
1. Add API calls in MCP tools
2. Return structured Pydantic models
3. LLM uses results in decision-making

### Add Database
1. Replace JSON file in `memory.py`
2. Keep Pydantic models unchanged
3. Implement save/load with DB queries

## Performance Considerations

- **Async I/O**: All MCP calls are async
- **Iteration Limit**: Max 5 iterations prevents infinite loops
- **Caching**: Memory preferences cached in-memory
- **Streaming**: Could add streaming for long menu generation

## Security Considerations

- **API Key**: Stored in environment variable
- **Input Validation**: Pydantic validates all inputs
- **Tool Isolation**: MCP tools run in separate process
- **No Code Execution**: Only predefined tools callable
