# Fix: API Key Not Available in MCP Server

## Problem

The system was showing:
```
Error: Cannot generate menu without API key
```

Even though the API key was:
- Exported in the shell: `export GEMINI_API_KEY='...'`
- Present in `.env` file

## Root Cause

The MCP server (`actions.py`) runs as a **separate process** spawned by `main.py`. 

When a process spawns a child process:
- Environment variables from the parent shell ARE inherited
- BUT `.env` file is NOT automatically loaded in the child process

The issue was that `actions.py` was not loading the `.env` file, so it couldn't see the API key.

## Solution

Added `python-dotenv` to load environment variables in the MCP server process.

### Changes Made

**1. Added python-dotenv dependency**

`requirements.txt`:
```python
python-dotenv>=1.0.0
```

`pyproject.toml`:
```python
dependencies = [
    ...
    "python-dotenv>=1.0.0",
]
```

**2. Load .env in actions.py**

```python
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
```

**3. Added debugging**

```python
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key status: {'Found' if api_key else 'NOT FOUND'}")
if api_key:
    print(f"API Key length: {len(api_key)} chars")
```

## How It Works Now

### Process Flow

```
Terminal
  ↓
  export GEMINI_API_KEY='...'  (sets in shell environment)
  ↓
main.py starts
  ↓
  Spawns child process: python actions.py
  ↓
actions.py starts
  ↓
  load_dotenv()  ← Loads .env file
  ↓
  os.getenv('GEMINI_API_KEY')  ← Gets API key
  ↓
  ✅ API key available!
```

### Two Ways to Provide API Key

**Option 1: Export in shell** (inherited by child process)
```bash
export GEMINI_API_KEY='your-key-here'
python main.py
```

**Option 2: Put in .env file** (loaded by dotenv)
```bash
# .env file
GEMINI_API_KEY=your-key-here
```
```bash
python main.py
```

**Option 3: Both** (most reliable)
- Export in shell for main.py
- .env file for actions.py child process

## Installation

```bash
# Install new dependency
uv sync

# Or with pip
pip install python-dotenv
```

## Testing

```bash
# Make sure API key is set
export GEMINI_API_KEY='your-key-here'

# Or create .env file
echo "GEMINI_API_KEY=your-key-here" > .env

# Run the application
python main.py
```

You should now see:
```
CALLED: generate_final_menu()
API Key status: Found
API Key length: 39 chars
Generated menu length: 850 chars
Generated menu preview: 🍽️ DINNER MENU...
```

## Why This Happens

**Parent-Child Process Environment**:
- Child processes inherit environment variables from parent
- BUT child processes don't automatically load `.env` files
- Each process needs to explicitly call `load_dotenv()`

**MCP Server Architecture**:
- `main.py` spawns `actions.py` as a separate process
- `actions.py` needs its own environment setup
- Can't rely on parent process's `.env` loading

## Summary

✅ Added `python-dotenv` dependency
✅ Load `.env` in `actions.py` with `load_dotenv()`
✅ Added debugging to show API key status
✅ Works with both exported env vars and `.env` file

The MCP server now has access to the API key and can generate menus! 🎉
