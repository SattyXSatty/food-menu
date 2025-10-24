# North Indian Food Menu Suggester

A multi-agent AI system with **proper MCP (Model Context Protocol)** implementation and **Pydantic** structured I/O that suggests personalized food menus using Gemini 2 Flash.

## Architecture

The system uses 5 cognitive layers with MCP tools and feedback loops:

1. **main.py** - Orchestration layer with MCP client
2. **perception.py** - Generates questions and extracts facts (Pydantic models)
3. **memory.py** - Stores predefined preferences (Pydantic models)
4. **decision.py** - Makes decisions and calls MCP tools via LLM
5. **actions.py** - **MCP Server** providing tools (calendar, meal history, menu generation)
6. **models.py** - Pydantic models for all structured data

## Key Features

✅ **Proper MCP Implementation** - Actions layer runs as MCP server, Decision layer calls tools
✅ **Pydantic Structured I/O** - All data validated with Pydantic models
✅ **LLM-Driven Tool Calls** - Gemini decides which MCP tools to call
✅ **Feedback Loop** - Decision layer calls Actions repeatedly until satisfied
✅ **Dynamic Query Processing** - User writes free-form query, LLM generates questions
✅ **Predefined Memory** - Taste (spicy), style (modern), ingredients (wheat, pulses, rice)
✅ **Repetition Avoidance** - Checks recent meal history via MCP tool

## MCP Tools (in actions.py)

The Actions layer runs as an MCP server providing these tools:

- **check_calendar** - Get current date/day/time
- **get_meal_history** - Retrieve recent meals (parameter: days=7)
- **check_ingredients** - Verify ingredient availability
- **generate_menu** - Create menu suggestions (parameters: meal_type, preferences)

## Pydantic Models (in models.py)

All data flows through validated Pydantic models:

- `ExtractedFacts` - User requirements from perception
- `UserPreferences` - Memory preferences
- `DecisionOutput` - Decision layer output
- `CalendarInfo`, `MealHistoryInfo`, `MenuResponse` - Tool outputs

## Setup

1. Install dependencies:

```bash
uv sync
```

Or manually:

```bash
pip install -r requirements.txt
```

2. Set your Gemini API key:

```bash
export GEMINI_API_KEY='your-api-key-here'
```

3. Run the application:

```bash
uv run main.py
```

Or:

```bash
python main.py
```

## How It Works

```
User Query
    ↓
Perception: Generate Questions → Collect Answers → Extract Facts (Pydantic)
    ↓
Memory: Retrieve Preferences (Pydantic: spicy, modern, wheat/pulses/rice)
    ↓
┌─────────────────────────────────────────────────┐
│  MCP Client connects to Actions MCP Server      │
│                                                 │
│  Decision-Action Feedback Loop:                 │
│                                                 │
│  Decision (LLM): Which tools to call?           │
│      ↓                                          │
│  MCP Client → Actions Server                    │
│    - check_calendar                             │
│    - get_meal_history                           │
│    - generate_menu                              │
│      ↓                                          │
│  Results (Pydantic) → Decision Layer            │
│      ↓                                          │
│  Decision: Need more tools? → Loop             │
│  Decision: status="complete" → Exit             │
└─────────────────────────────────────────────────┘
    ↓
Final Menu Response
```

## Example Flow

1. **User**: "I want something light for lunch"
2. **Perception**: Generates questions (meal type, people, time)
3. **User**: Answers questions
4. **Perception**: Extracts facts → `ExtractedFacts` model
5. **Memory**: Provides → `UserPreferences` model
6. **MCP Connection**: Establishes stdio connection to actions.py
7. **Decision Loop**:
   - **Iteration 1**: LLM decides to call `check_calendar`, `get_meal_history`
   - MCP client calls tools → Results returned
   - **Iteration 2**: LLM analyzes results, calls `generate_menu`
   - **Iteration 3**: LLM sets `status="complete"`, returns final menu
8. **Output**: Complete menu with reasoning

## File Structure

```
.
├── main.py              # Orchestrator with MCP client
├── perception.py        # Question generation & fact extraction
├── memory.py            # Preference storage
├── decision.py          # Decision making (calls MCP tools)
├── actions.py           # MCP Server with tools
├── models.py            # Pydantic models
├── requirements.txt     # Dependencies
├── pyproject.toml       # Project config
└── README.md
```

## Dependencies

- `google-generativeai>=0.3.0` - Gemini 2 Flash LLM
- `mcp>=0.9.0` - Model Context Protocol
- `pydantic>=2.0.0` - Data validation

## Customization

Edit `user_preferences.json` to change default preferences:

```json
{
  "taste": "spicy",
  "food_style": "modern",
  "ingredients": ["wheat flour", "pulses", "rice"],
  "dietary_type": "vegetarian",
  "avoid_ingredients": [],
  "meal_history": []
}
```

## Technical Details

### MCP Implementation

The system uses proper MCP architecture:
- **Server**: `actions.py` runs as stdio MCP server
- **Client**: `main.py` connects via `stdio_client`
- **Tools**: Registered with `@app.list_tools()` and `@app.call_tool()`
- **Communication**: JSON-RPC over stdio

### Pydantic Integration

All data is validated:
- Input validation on user data
- Output validation from LLM (JSON mode)
- Type safety across all layers
- Automatic serialization/deserialization

### LLM Tool Calling

Gemini 2 Flash decides which tools to call:
- Analyzes context and determines needs
- Requests specific MCP tools
- Evaluates results and decides next steps
- Continues until satisfied (status="complete")
