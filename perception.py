"""
Perception Agent
Understands and extracts facts from user input using Gemini 2 Flash with Pydantic
"""
import google.generativeai as genai
import os
import json
from models import GeneratedQuestions, ExtractedFacts

class PerceptionAgent:
    def __init__(self):
        self.question_prompt = """You are a Perception Agent in a North Indian Food Recommendation System.

---

### 🎯 Objective
Understand the user's query and generate 2–4 clarifying questions to collect essential context before recommending dishes.

---

### 🧠 Step-by-Step Reasoning Framework
1. **Understand the Query**
   - Identify any mentioned meal type, people count, time, restrictions, or occasion.
2. **Detect Missing Details**
   - For each category (meal type, people, time, dietary restrictions, occasion), mark whether info is missing or unclear.
3. **Generate Clarifying Questions**
   - Ask concise, contextually relevant questions only for missing details.
   - Avoid redundant or overly generic questions.
4. **Verify**
   - Ensure at least 2 and at most 4 questions are produced.
   - Check that each question directly helps improve food recommendation relevance.
5. **Output**
   - Respond **only** in structured JSON as defined below.

---

### 🧾 Output Format
Return a valid JSON object in this structure:
```json
{
  "questions": ["question 1", "question 2", "question 3"],
  "reasoning": "brief explanation of why these questions were asked"
}
"""

        self.extraction_prompt = """You are a Perception Agent extracting structured facts from a conversation about North Indian food preferences.

---

### 🎯 Objective
Understand the user's input and extract relevant factual information into a structured JSON object.

---

### 🧠 Step-by-Step Reasoning Framework
1. **Understand the Input**
   - Read the user’s statement carefully and identify clues about meal type, number of people, time available, restrictions, occasion, requests, and constraints.

2. **Determine Each Field**
   - **meal_type:** must directly reflect if words like "breakfast", "lunch", "dinner", or "snack(s)" are mentioned.  
   - **number_of_people:** infer an integer if mentioned (e.g., “for two of us” → 2).  
   - **time_available:** classify as “quick”, “normal”, or “elaborate” based on context (e.g., “in a hurry” → quick).  
   - **dietary_restrictions:** list of restrictions like “vegetarian”, “vegan”, “no onion/garlic”.  
   - **occasion:** detect if the meal is for a “regular day”, “special occasion”, “festival”, or “guests”.  
   - **specific_requests:** store any explicitly mentioned dishes or ingredients as a **string** (not a list).  
   - **constraints:** list of ingredients or conditions to avoid.

3. **Sanity Checks**
   - Ensure all expected keys are present.  
   - Default empty values:  
     - Lists → `[]`  
     - Strings → `""`  
     - Integers → `0`  
   - Confirm `specific_requests` is a **string**, never a list.  
   - Ensure the JSON is valid and well-formed.

4. **Output**
   - Return only a **valid JSON object** matching the structure below.  
   - Do not include explanations or commentary.

---

### 🧾 Output Format
```json
{
  "meal_type": "breakfast/lunch/dinner/snacks",
  "number_of_people": 0,
  "time_available": "quick/normal/elaborate",
  "dietary_restrictions": [],
  "occasion": "regular/special/guests/etc",
  "specific_requests": "",
  "constraints": []
}
"""
        
        # Initialize Gemini with structured output
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config={
                    "response_mime_type": "application/json"
                }
            )
        else:
            self.model = None
            print("⚠️  Warning: GEMINI_API_KEY not set. Using fallback mode.")
    
    def generate_questions(self, user_query: str) -> GeneratedQuestions:
        """Generate clarifying questions based on user query"""
        if self.model:
            try:
                response = self.model.generate_content(
                    f"{self.question_prompt}\n\nUser Query: {user_query}"
                )
                data = json.loads(response.text)
                return GeneratedQuestions(**data)
            except Exception as e:
                print(f"⚠️  Gemini API error: {e}")
                return self._fallback_questions()
        else:
            return self._fallback_questions()
    
    def collect_responses(self, questions: GeneratedQuestions) -> dict:
        """Collect user responses to questions"""
        responses = {}
        
        for i, question in enumerate(questions.questions, 1):
            answer = input(f"{i}. {question}\n> ").strip()
            responses[question] = answer
        
        return responses
    
    def extract_facts(self, user_query: str, user_responses: dict) -> ExtractedFacts:
        """Extract facts from query and responses"""
        conversation = f"Initial Query: {user_query}\n\n"
        for q, a in user_responses.items():
            conversation += f"Q: {q}\nA: {a}\n\n"
        
        if self.model:
            try:
                response = self.model.generate_content(
                    f"{self.extraction_prompt}\n\nConversation:\n{conversation}"
                )
                data = json.loads(response.text)
                
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
                
                return ExtractedFacts(**data)
            except Exception as e:
                print(f"⚠️  Gemini API error: {e}")
                return self._fallback_extraction(user_query)
        else:
            return self._fallback_extraction(user_query)
    
    def _fallback_questions(self) -> GeneratedQuestions:
        """Fallback questions without API"""
        return GeneratedQuestions(
            questions=[
                "What meal are you planning? (breakfast/lunch/dinner/snacks)",
                "How many people will be eating?",
                "How much time do you have for cooking?"
            ],
            reasoning="Basic questions to understand meal requirements"
        )
    
    def _fallback_extraction(self, user_query: str) -> ExtractedFacts:
        """Fallback extraction without API"""
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
        
        # Detect time constraint
        time_available = "normal"
        if "quick" in query_lower or "fast" in query_lower or "hurry" in query_lower:
            time_available = "quick"
        
        return ExtractedFacts(
            meal_type=meal_type,
            number_of_people=2,
            time_available=time_available,
            dietary_restrictions=[],
            occasion="regular",
            specific_requests=user_query,
            constraints=[]
        )
