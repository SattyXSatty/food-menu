# Quick Start Guide

## Installation

1. **Install dependencies**:
```bash
uv sync
```

Or with pip:
```bash
pip install -r requirements.txt
```

2. **Set API key**:
```bash
export GEMINI_API_KEY='your-gemini-api-key-here'
```

Get your API key from: https://aistudio.google.com/app/apikey

## Test MCP Server

Before running the full app, test that the MCP server works:

```bash
python test_mcp.py
```

You should see:
```
✅ Connected to MCP server
✅ Session created
✅ Session initialized
📋 Available tools (4):
   - check_calendar: Get current date, day, and time information
   - get_meal_history: Retrieve recent meal history to avoid repetition
   - check_ingredients: Check common ingredient availability in pantry
   - generate_menu: Generate North Indian food menu based on context
✅ All tests passed!
```

## Run the Application

```bash
uv run main.py
```

Or:
```bash
python main.py
```

## Example Session

```
🍽️  Welcome to North Indian Food Menu Suggester
================================================================================

🔧 Initializing Cognitive Agents...
✅ All agents initialized successfully
================================================================================

📝 What would you like to eat?
Your query: I want something light and healthy for lunch

================================================================================

🤔 PERCEPTION LAYER: Analyzing your query and generating questions...
📤 Generated Questions:
   1. How many people will be eating?
   2. How much time do you have for cooking?
   3. Any dietary restrictions?

================================================================================

💬 Please answer the following questions:
1. How many people will be eating?
> 2

2. How much time do you have for cooking?
> 30 minutes

3. Any dietary restrictions?
> vegetarian

================================================================================

🧠 PERCEPTION LAYER: Extracting facts from conversation...
📤 Perception Output:
   {
      "meal_type": "lunch",
      "number_of_people": 2,
      "time_available": "quick",
      "dietary_restrictions": ["vegetarian"],
      "occasion": "regular",
      "specific_requests": "light and healthy",
      "constraints": []
   }

================================================================================

💾 MEMORY LAYER: Retrieving stored preferences...
📤 Memory Output:
   Taste: spicy
   Food Style: modern
   Ingredients: wheat flour, pulses, rice

================================================================================

🔌 Establishing connection to MCP server...
✅ Connection established, creating session...
✅ Session created, initializing...
✅ MCP server ready

================================================================================

📋 Available MCP Tools: check_calendar, get_meal_history, check_ingredients, generate_menu

================================================================================

🔄 Starting Decision-Action Feedback Loop...

================================================================================

🎯 DECISION LAYER (Iteration 1): Analyzing situation...
📤 Decision Output:
   Status: needs_action
   Reasoning: Need to check date and recent meals to avoid repetition
   Actions Needed: check_calendar, get_meal_history

================================================================================

⚡ ACTIONS LAYER (Iteration 1): Executing MCP tools...
  🔧 Calling MCP tool: check_calendar
  ✅ check_calendar completed
  🔧 Calling MCP tool: get_meal_history
  ✅ get_meal_history completed
📤 Action Results:
   check_calendar: {
      "date": "2025-10-16",
      "day": "Thursday",
      "time": "14:30",
      "is_weekend": false
   }...
   get_meal_history: {
      "recent_meals": [],
      "count": 0,
      "note": "No meal history found"
   }...

================================================================================

🔁 Feeding results back to Decision Layer...

================================================================================

🎯 DECISION LAYER (Iteration 2): Analyzing situation...
📤 Decision Output:
   Status: needs_action
   Reasoning: Have context, now generating menu
   Actions Needed: generate_menu

================================================================================

⚡ ACTIONS LAYER (Iteration 2): Executing MCP tools...
  🔧 Calling MCP tool: generate_menu
  ✅ generate_menu completed
📤 Action Results:
   generate_menu: {
      "menu": "🍛 LUNCH MENU\n\nMain Course:\n• Dal Tadka...",
      "generated": true,
      "note": "Template menu for lunch"
   }...

================================================================================

🔁 Feeding results back to Decision Layer...

================================================================================

🎯 DECISION LAYER (Iteration 3): Analyzing situation...
📤 Decision Output:
   Status: complete
   Reasoning: Menu generated based on available information

================================================================================

✅ Decision Layer: Final response ready!

================================================================================

🎉 FINAL RESULT:
[Complete menu with dishes, cooking times, and ingredients]

================================================================================

✨ Process completed!
```

## Troubleshooting

### "GEMINI_API_KEY not set"
Set your API key:
```bash
export GEMINI_API_KEY='your-key'
```

### "Connection refused" or MCP errors
Make sure Python can find actions.py:
```bash
python actions.py
```
Should start the MCP server (it will wait for input).

### Import errors
Install all dependencies:
```bash
pip install google-generativeai mcp pydantic
```

## Next Steps

- Customize preferences in `user_preferences.json`
- Add more MCP tools in `actions.py`
- Modify prompts in each agent file
- Integrate with external APIs (weather, inventory, etc.)
