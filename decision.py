"""
Decision Agent
LLM freely decides which tool to call or provide final answer
NO prescribed workflow - LLM has full autonomy
"""
import google.generativeai as genai
import os
import json
from models import ExtractedFacts, UserPreferences

class DecisionAgent:
    def __init__(self):
        # Initialize Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
            print("⚠️  Warning: GEMINI_API_KEY not set. Using fallback mode.")
    
    def create_system_prompt(self, tools_list: list) -> str:
        """Create system prompt with available tools"""
        tools_description = "\n".join([
            f"{i+1}. {tool['name']}({tool['params']}) - {tool['description']}"
            for i, tool in enumerate(tools_list)
        ])
        
        return f"""You are an intelligent Decision Agent for a North Indian food recommendation system.  
Your goal is to generate a personalized menu from the user's request.  
You have FULL AUTONOMY to decide which tools to call, in what order, and when to give the final answer.

AVAILABLE MCP TOOLS:
{tools_description}

────────────────────────────
RESPONSE FORMAT (choose ONE)
FUNCTION_CALL: tool_name|param1|param2|...
FINAL_ANSWER: [complete menu text]

────────────────────────────
REASONING FRAMEWORK
1. Understand intent → infer meal type, people, time, preferences, etc.  
2. Plan relevant tools (check_calendar, get_meal_history, get_user_preferences, etc.).  
3. Execute one tool at a time; don’t repeat.  
4. When ready, call generate_final_menu with all context as JSON.  
5. After it returns, immediately give FINAL_ANSWER with the full menu text.

────────────────────────────
TOOL NOTES
- check_calendar → get day/time context  
- get_meal_history → avoid repetition  
- get_user_preferences → know taste/style  
- generate_final_menu → **must be called before FINAL_ANSWER**; pass all info (meal_type, preferences, etc.)  
- save_meal_to_history → optional after success  

────────────────────────────
SELF-CHECK & FALLBACKS
Before calling generate_final_menu or FINAL_ANSWER, ensure:  
• meal_type and preferences known or inferred  
• JSON payload complete and valid  
If a tool fails, retry once or continue logically. Never invent menus or output tool errors.

────────────────────────────
EXAMPLES

Simple Flow  
FUNCTION_CALL: get_user_preferences  
FUNCTION_CALL: generate_final_menu|{"meal_type":"dinner","preferences":{"spicy":true}}  
FINAL_ANSWER: [menu text]

Thorough Flow  
FUNCTION_CALL: check_calendar  
FUNCTION_CALL: get_meal_history|7  
FUNCTION_CALL: get_user_preferences  
FUNCTION_CALL: generate_final_menu|{"meal_type":"lunch","day":"Sunday","preferences":{...},"history":[...]}  
FINAL_ANSWER: [menu text]

────────────────────────────
CRITICAL RULES
- Only one tool per message.  
- Next response after generate_final_menu must be FINAL_ANSWER.  
- Never create menus yourself.  
- Be efficient; avoid redundant calls.

────────────────────────────


YOU DECIDE what's appropriate based on the user's query!"""
    
    def make_decision(
        self, 
        perceived_facts: ExtractedFacts, 
        memory_data: UserPreferences, 
        action_history: list,
        tools_list: list
    ) -> dict:
        """
        Make decision - returns either a tool call or final answer
        
        Returns:
            {
                "type": "tool_call" or "final_answer",
                "tool_name": str (if tool_call),
                "params": list (if tool_call),
                "final_response": str (if final_answer),
                "reasoning": str
            }
        """
        iteration = len(action_history) + 1
        
        # Build context with history
        if iteration == 1:
            context = f"""USER REQUEST:
Meal Type: {perceived_facts.meal_type}
Number of People: {perceived_facts.number_of_people}
Time Available: {perceived_facts.time_available}
Specific Requests: {perceived_facts.specific_requests}
Dietary Restrictions: {', '.join(perceived_facts.dietary_restrictions) if perceived_facts.dietary_restrictions else 'None'}

USER PREFERENCES (from memory):
Taste: {memory_data.taste}
Food Style: {memory_data.food_style}
Preferred Ingredients: {', '.join(memory_data.ingredients)}
Dietary Type: {memory_data.dietary_type}

This is your first decision. What tool should you call first?"""
        else:
            # Build history of what's been done
            history_lines = []
            for i, action in enumerate(action_history, 1):
                tool = action.get("tool_name", "unknown")
                result = action.get("result", {})
                
                # Summarize result
                if isinstance(result, dict):
                    if "count" in result:
                        summary = f"Found {result['count']} items"
                    elif "date" in result:
                        summary = f"Date: {result.get('date')}, Day: {result.get('day')}"
                    elif "menu" in result:
                        menu_preview = result.get('menu', '')[:150]
                        summary = f"Generated menu: {menu_preview}..."
                    elif "taste" in result:
                        summary = f"Taste: {result.get('taste')}, Style: {result.get('food_style')}"
                    elif "recent_meals" in result:
                        count = result.get('count', 0)
                        summary = f"Found {count} recent meals"
                    else:
                        summary = "Completed"
                else:
                    summary = str(result)[:100]
                
                history_lines.append(f"✓ Step {i}: {tool} → {summary}")
            
            history = "\n".join(history_lines)
            
            # Check if last action was generate_final_menu
            last_tool = action_history[-1].get("tool_name") if action_history else None
            if last_tool == "generate_final_menu":
                last_result = action_history[-1].get("result", {})
                if isinstance(last_result, dict) and "menu" in last_result:
                    context = f"""USER REQUEST:
Meal Type: {perceived_facts.meal_type}

WHAT YOU'VE DONE:
{history}

The generate_final_menu tool has returned a complete menu.
Your NEXT response MUST be:
FINAL_ANSWER: [paste the COMPLETE menu from generate_final_menu result]

DO NOT create a new menu. Use the menu that was already generated."""
                else:
                    context = f"""USER REQUEST:
Meal Type: {perceived_facts.meal_type}
Time Available: {perceived_facts.time_available}

WHAT YOU'VE DONE SO FAR:
{history}

Iteration {iteration}. What's your next step?"""
            else:
                context = f"""USER REQUEST:
Meal Type: {perceived_facts.meal_type}
Time Available: {perceived_facts.time_available}
Specific Requests: {perceived_facts.specific_requests}

WHAT YOU'VE DONE SO FAR:
{history}

Iteration {iteration}. What's your next step?
(Remember: generate_final_menu creates the detailed menu, then you provide FINAL_ANSWER with that menu)"""
        
        system_prompt = self.create_system_prompt(tools_list)
        prompt = f"{system_prompt}\n\n{context}"
        
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Find the response line
                for line in response_text.split('\n'):
                    line = line.strip()
                    if line.startswith("FUNCTION_CALL:") or line.startswith("FINAL_ANSWER:"):
                        response_text = line
                        break
                
                print(f"🤖 LLM Response: {response_text[:100]}...")
                
                # Parse response
                if response_text.startswith("FUNCTION_CALL:"):
                    _, function_info = response_text.split(":", 1)
                    parts = [p.strip() for p in function_info.split("|")]
                    tool_name = parts[0]
                    params = parts[1:] if len(parts) > 1 else []
                    
                    return {
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "params": params,
                        "reasoning": f"LLM decided to call {tool_name}"
                    }
                
                elif response_text.startswith("FINAL_ANSWER:"):
                    final_answer = response_text.split(":", 1)[1].strip()
                    
                    # ALWAYS try to get menu from last action if it was generate_final_menu
                    if action_history:
                        for action in reversed(action_history):
                            if action.get("tool_name") == "generate_final_menu":
                                result = action.get("result", {})
                                if isinstance(result, dict) and "menu" in result:
                                    menu = result["menu"]
                                    # If LLM's answer is short, use the full menu
                                    if len(final_answer) < 200:
                                        final_answer = menu
                                    # If LLM's answer doesn't contain main dishes, use the full menu
                                    elif "Main Dishes:" not in final_answer and "🍛" not in final_answer:
                                        final_answer = menu
                                break
                    
                    return {
                        "type": "final_answer",
                        "final_response": final_answer,
                        "reasoning": "LLM provided final answer"
                    }
                
                else:
                    # Fallback if format is wrong
                    return self._fallback_decision(iteration, perceived_facts, action_history)
                    
            except Exception as e:
                print(f"⚠️  Gemini API error: {e}")
                return self._fallback_decision(iteration, perceived_facts, action_history)
        else:
            return self._fallback_decision(iteration, perceived_facts, action_history)
    
    def _fallback_decision(self, iteration: int, perceived_facts: ExtractedFacts, action_history: list) -> dict:
        """Fallback decision without API"""
        
        if iteration == 1:
            return {
                "type": "tool_call",
                "tool_name": "get_user_preferences",
                "params": [],
                "reasoning": "Getting user preferences"
            }
        elif iteration == 2:
            return {
                "type": "tool_call",
                "tool_name": "get_meal_history",
                "params": ["7"],
                "reasoning": "Checking recent meals"
            }
        elif iteration == 3:
            # Build context for generate_final_menu
            context = {
                "meal_type": perceived_facts.meal_type,
                "number_of_people": perceived_facts.number_of_people,
                "time_available": perceived_facts.time_available,
                "specific_requests": perceived_facts.specific_requests
            }
            
            # Add data from history
            for action in action_history:
                result = action.get("result", {})
                tool_name = action.get("tool_name", "")
                
                if tool_name == "get_user_preferences":
                    context["preferences"] = result
                elif tool_name == "get_meal_history":
                    context["recent_meals"] = result.get("recent_meals", [])
            
            return {
                "type": "tool_call",
                "tool_name": "generate_final_menu",
                "params": [json.dumps(context)],
                "reasoning": "Generating final menu"
            }
        else:
            # Get menu from last action
            if action_history:
                last_action = action_history[-1]
                if last_action.get("tool_name") == "generate_final_menu":
                    result = last_action.get("result", {})
                    if isinstance(result, dict) and "menu" in result:
                        return {
                            "type": "final_answer",
                            "final_response": result["menu"],
                            "reasoning": "Using generated menu"
                        }
            
            return {
                "type": "final_answer",
                "final_response": f"Menu for {perceived_facts.meal_type} - Please try again with more details.",
                "reasoning": "Fallback final answer"
            }
