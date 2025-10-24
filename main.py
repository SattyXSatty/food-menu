"""
Main Orchestration Layer
Follows talk2mcp.py pattern: LLM responds with FUNCTION_CALL or FINAL_ANSWER
"""
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from perception import PerceptionAgent
from memory import MemoryAgent
from decision import DecisionAgent
from models import ExtractedFacts, UserPreferences
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()

def print_separator():
    print("\n" + "="*80 + "\n")

def reset_state():
    """Reset global state"""
    global iteration, action_history
    iteration = 0
    action_history = []

# Global variables
iteration = 0
action_history = []

async def call_mcp_tool(session: ClientSession, tool_name: str, params: list, tools: list) -> dict:
    """Call a single MCP tool with parameters"""
    print(f"  🔧 Calling MCP tool: {tool_name}")
    if params:
        print(f"     Parameters: {params}")
    
    try:
        # Find the tool schema
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}
        
        # Prepare arguments according to schema
        arguments = {}
        schema_properties = tool.inputSchema.get('properties', {})
        
        param_index = 0
        for param_name, param_info in schema_properties.items():
            param_type = param_info.get('type', 'string')
            
            if param_type == 'array':
                # For arrays, take remaining params or parse comma-separated
                if param_index < len(params):
                    value = params[param_index]
                    if ',' in value:
                        array_values = [int(x.strip()) for x in value.split(',')]
                    else:
                        array_values = [int(params[i]) for i in range(param_index, len(params))]
                    arguments[param_name] = array_values
                param_index = len(params)
            elif param_index < len(params):
                value = params[param_index]
                if param_type == 'integer':
                    arguments[param_name] = int(value)
                elif param_type == 'number':
                    arguments[param_name] = float(value)
                else:
                    arguments[param_name] = str(value)
                param_index += 1
            else:
                # Use default if available
                if 'default' in param_info:
                    arguments[param_name] = param_info['default']
        
        # Call the tool
        result = await session.call_tool(tool_name, arguments=arguments)
        
        # Extract result
        if hasattr(result, 'content') and result.content:
            if isinstance(result.content, list):
                result_data = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        try:
                            result_data.append(json.loads(item.text))
                        except:
                            result_data.append(item.text)
                    else:
                        result_data.append(str(item))
                
                # Unwrap single item
                if len(result_data) == 1:
                    result_data = result_data[0]
            else:
                result_data = str(result.content)
        else:
            result_data = str(result)
        
        print(f"  ✅ {tool_name} completed")
        return result_data
        
    except Exception as e:
        print(f"  ❌ {tool_name} failed: {e}")
        return {"error": str(e)}

async def main_async():
    global iteration, action_history
    reset_state()
    
    print("🍽️  Welcome to North Indian Food Menu Suggester")
    print_separator()
    
    # Initialize cognitive agents
    print("🔧 Initializing Cognitive Agents...")
    perception = PerceptionAgent()
    memory = MemoryAgent()
    decision = DecisionAgent()
    print("✅ All agents initialized successfully")
    print_separator()
    
    # Step 1: Get user's free-form query
    print("📝 What would you like to eat?")
    user_query = input("Your query: ").strip()
    print_separator()
    
    # Step 2: Generate clarifying questions
    print("🤔 PERCEPTION LAYER: Analyzing your query and generating questions...")
    questions = perception.generate_questions(user_query)
    print(f"📤 Generated Questions:")
    for i, q in enumerate(questions.questions, 1):
        print(f"   {i}. {q}")
    print_separator()
    
    # Step 3: Collect user responses
    print("💬 Please answer the following questions:")
    user_responses = perception.collect_responses(questions)
    print_separator()
    
    # Step 4: Extract facts
    print("🧠 PERCEPTION LAYER: Extracting facts from conversation...")
    perceived_facts: ExtractedFacts = perception.extract_facts(user_query, user_responses)
    print(f"📤 Perception Output:")
    print(f"   Meal Type: {perceived_facts.meal_type}")
    print(f"   People: {perceived_facts.number_of_people}")
    print(f"   Time: {perceived_facts.time_available}")
    print_separator()
    
    # Step 5: Retrieve memory preferences
    print("💾 MEMORY LAYER: Retrieving stored preferences...")
    user_preferences: UserPreferences = memory.get_preferences()
    print(f"📤 Memory Output:")
    print(f"   Taste: {user_preferences.taste}")
    print(f"   Food Style: {user_preferences.food_style}")
    print(f"   Ingredients: {', '.join(user_preferences.ingredients)}")
    print_separator()
    
    # Step 6: Connect to MCP server
    print("🔌 Establishing connection to MCP server...")
    server_params = StdioServerParameters(
        command="python",
        args=["actions.py"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            print("✅ Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("✅ Session created, initializing...")
                await session.initialize()
                print("✅ MCP server ready")
                print_separator()
                
                # Get available tools
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"📋 Available MCP Tools ({len(tools)}):")
                for tool in tools:
                    print(f"   - {tool.name}")
                print_separator()
                
                # Prepare tools list for decision agent
                tools_list = []
                for tool in tools:
                    params_list = []
                    if 'properties' in tool.inputSchema:
                        for param_name, param_info in tool.inputSchema['properties'].items():
                            param_type = param_info.get('type', 'string')
                            params_list.append(f"{param_name}:{param_type}")
                    
                    tools_list.append({
                        "name": tool.name,
                        "description": tool.description,
                        "params": ", ".join(params_list) if params_list else "no params"
                    })
                
                # Decision-Action Loop (like talk2mcp.py)
                print("🔄 Starting Decision-Action Loop...")
                print_separator()
                
                max_iterations = 12  # Increased to allow for generate_final_menu
                iteration = 0
                
                while iteration < max_iterations:
                    iteration += 1
                    print(f"🎯 DECISION LAYER (Iteration {iteration}):")
                    
                    # Get decision from LLM
                    decision_output = decision.make_decision(
                        perceived_facts=perceived_facts,
                        memory_data=user_preferences,
                        action_history=action_history,
                        tools_list=tools_list
                    )
                    
                    print(f"📤 Decision: {decision_output['type']}")
                    print(f"   Reasoning: {decision_output['reasoning']}")
                    print_separator()
                    
                    # Check if final answer
                    if decision_output["type"] == "final_answer":
                        print("✅ Decision Layer: Final response ready!")
                        print_separator()
                        
                        # Debug: Check if menu is complete
                        final_response = decision_output["final_response"]
                        print(f"   🔍 Debug: Final response length: {len(final_response)} chars")
                        
                        if len(final_response) < 200:
                            print("⚠️  Warning: Final response seems short. Checking action history...")
                            print(f"   🔍 Debug: Action history has {len(action_history)} actions")
                            
                            # Try to get menu from history
                            for i, action in enumerate(reversed(action_history)):
                                tool = action.get("tool_name")
                                print(f"   🔍 Debug: Checking action {len(action_history)-i}: {tool}")
                                
                                if tool == "generate_final_menu":
                                    result = action.get("result", {})
                                    print(f"   🔍 Debug: Found generate_final_menu result")
                                    print(f"   🔍 Debug: Result type: {type(result)}")
                                    print(f"   🔍 Debug: Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                                    
                                    if isinstance(result, dict) and "menu" in result:
                                        menu = result["menu"]
                                        print(f"   🔍 Debug: Found menu in result ({len(menu)} chars)")
                                        print(f"   🔍 Debug: Menu preview: {menu[:100]}...")
                                        final_response = menu
                                        print("✅ Retrieved full menu from generate_final_menu result")
                                    else:
                                        print(f"   ⚠️  Debug: No 'menu' key in result!")
                                    break
                        
                        print("🎉 FINAL RESULT:")
                        print(final_response)
                        
                        # Save to memory
                        memory.add_meal_to_history({
                            "date": datetime.now().isoformat(),
                            "meal_type": perceived_facts.meal_type,
                            "query": user_query
                        })
                        break
                    
                    # Execute tool call
                    elif decision_output["type"] == "tool_call":
                        tool_name = decision_output["tool_name"]
                        params = decision_output["params"]
                        
                        print(f"⚡ ACTIONS LAYER: Executing {tool_name}...")
                        result = await call_mcp_tool(session, tool_name, params, tools)
                        
                        # Show result summary
                        if isinstance(result, dict):
                            if "count" in result:
                                print(f"   📊 Result: Found {result['count']} items")
                            elif "date" in result:
                                print(f"   📅 Result: {result.get('date')} ({result.get('day')})")
                            elif "menu" in result:
                                # Show first few lines of menu
                                menu_text = result["menu"]
                                menu_lines = menu_text.split('\n')[:8]
                                print(f"   📊 Result: Menu generated ({len(menu_text)} chars)")
                                print(f"   📊 Success: {result.get('success', 'unknown')}")
                                for line in menu_lines:
                                    print(f"      {line}")
                                if len(menu_text.split('\n')) > 8:
                                    print(f"      ... ({len(menu_text.split('\n'))} total lines)")
                            else:
                                print(f"   📊 Result: {str(result)[:100]}...")
                        else:
                            print(f"   📊 Result: {str(result)[:100]}...")
                        print_separator()
                        
                        # Store in history
                        action_history.append({
                            "iteration": iteration,
                            "tool_name": tool_name,
                            "params": params,
                            "result": result
                        })
                        
                        # Debug: If this was generate_final_menu, verify the result
                        if tool_name == "generate_final_menu" and isinstance(result, dict):
                            if "menu" in result:
                                print(f"   🔍 Debug: Stored menu in history ({len(result['menu'])} chars)")
                            else:
                                print(f"   ⚠️  Debug: No 'menu' key in result! Keys: {list(result.keys())}")
                        
                        print(f"🔁 Feeding result back to Decision Layer...")
                        print_separator()
                
                if iteration >= max_iterations:
                    print("⚠️  Maximum iterations reached.")
                    print_separator()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()
    
    print("✨ Process completed!")

def main():
    """Entry point"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
