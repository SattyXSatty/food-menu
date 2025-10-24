import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")

response = model.generate_content("Hello from Gemini!")
print(response.text)


max_iterations = 10  # Increased to allow for calculation + visualization steps
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(model, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise


def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are a math agent solving problems step by step. You have calculation tools AND visualization tools.

Available tools:
{tools_description}

RESPOND WITH EXACTLY ONE LINE (no explanations):
Format: FUNCTION_CALL: function_name|param1|param2|...
Or: FINAL_ANSWER: [your answer]

WORKFLOW (follow in order):
PHASE 1 - CALCULATE:
1. Use the math tools to calculate the answer

PHASE 2 - VISUALIZE (after you have the FINAL_ANSWER):
2. Open Preview
3. Draw box with x1=100, y1=100, height=700, width=500 with blue colour
4. Add text in the box with FINAL_ANSWER into, keep the font size to fit the box 
5. Show it in the preview

PHASE 3 - FINISH:
6. FINAL_ANSWER: The answer is YOUR_NUMBER and is displayed in Preview

IMPORTANT:
- For arrays, use comma-separated: int_list_to_exponential_sum|73,78,68,73,65
- Don't repeat the same function call
- Move to visualization ONLY after you have the final calculated answer
- Each step should progress toward the goal

Examples:
FUNCTION_CALL: add|5|3
FUNCTION_CALL: strings_to_chars_to_int|INDIA
FINAL_ANSWER: The sum is 1.6e33 and is displayed in Preview"""

                query = """Find the ASCII values of characters in INDIA and then return sum of exponentials of those values. """
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    
                    # Build context with history
                    if iteration == 0:
                        context = f"Query: {query}"
                    else:
                        history = "\n".join(iteration_response)
                        context = f"Query: {query}\n\nWhat you've done so far:\n{history}\n\nNext step:"
                    
                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\n{context}"
                    try:
                        response = await generate_with_timeout(model, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            param_index = 0
                            for param_name, param_info in schema_properties.items():
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Processing parameter {param_name} (type: {param_type})")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'array':
                                    # For arrays, take all remaining params or parse comma-separated
                                    if param_index < len(params):
                                        value = params[param_index]
                                        if ',' in value:
                                            # Comma-separated list
                                            array_values = [int(x.strip()) for x in value.split(',')]
                                        else:
                                            # Multiple parameters are the array elements
                                            array_values = [int(params[i]) for i in range(param_index, len(params))]
                                        arguments[param_name] = array_values
                                        print(f"DEBUG: Array parameter {param_name} = {array_values}")
                                    param_index = len(params)  # Consume all remaining params
                                elif param_index < len(params):
                                    value = params[param_index]
                                    print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                    
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

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = []
                                    for item in result.content:
                                        if hasattr(item, 'text'):
                                            iteration_result.append(item.text)
                                        else:
                                            iteration_result.append(str(item))
                                    # If single item, unwrap it
                                    if len(iteration_result) == 1:
                                        iteration_result = iteration_result[0]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(str(x) for x in iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            # Format response clearly
                            if isinstance(iteration_result, list):
                                result_display = f"[{', '.join(str(x) for x in iteration_result)}]"
                            else:
                                result_display = str(iteration_result)
                            
                            iteration_response.append(
                                f"✓ Step {iteration + 1}: {func_name} → {result_display}"
                            )
                            last_response = iteration_result

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Agent Execution Complete ===")
                        final_answer = response_text.split(":", 1)[1].strip()
                        print(f"Final Answer: {final_answer}")
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
