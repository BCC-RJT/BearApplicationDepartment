import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use a model that supports JSON mode well or standard chat
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

SYSTEM_PROMPT = """
You are the "AI Receptionist" for the Bear Application Department (BAD) support system.
Your goal is to interview the user to create a structured support ticket.

**YOUR OBJECTIVE**:
Gather the following fields:
1.  **Issue Type**: (e.g., Bug, Feature Request, Access Issue, Billing, Other)
2.  **Description**: A detailed explanation of the problem.
3.  **Expected Outcome**: What the user wants to happen.
4.  **Priority**: (Low, Medium, High, Critical) - Infer this if possible, or ask.

**PROTOCOL**:
1.  **Greet**: If this is the start, welcome the user and ask what issue they are facing.
2.  **Clarify**: If the user is vague (e.g., "it's broken"), ask SPECIFIC clarifying questions.
3.  **No Fluff**: Keep responses concise and professional.
4.  **Done State**: When you have all 4 fields, output a JSON object with the final details.

**OUTPUT FORMAT**:
- If you need more info: Return a plain text question.
- If you have all info: Return a JSON object in this format:
```json
{
  "ticket_ready": true,
  "issue_type": "...",
  "description": "...",
  "expected_outcome": "...",
  "priority": "..."
}
```
"""

async def get_ai_response(history, user_input):
    """
    history: List of dicts [{"role": "user"|"model", "parts": ["..."]}]
    user_input: String
    """
    if not model:
        return "⚠️ Error: GEMINI_API_KEY is missing. Please configure the bot."

    # Construct chat session
    chat = model.start_chat(history=history)
    
    # Add system prompt to the context if it's the first message, 
    # or rely on the model instructions (Gemini 1.5/2.0 supports system_instruction).
    # For simplicity with 'start_chat', we can prepend it to the first message or use system_instruction if available.
    
    # Actually, let's just send the message. 
    # To enforce the persona, we usually send the system prompt as the first 'user' message or system instruction.
    # Let's try sending it as a system instruction via a fresh generation call if history is empty, 
    # but 'chat' object maintains history.
    
    # We'll use a stateless approach for the 'brain' function to be simpler to integrate with Discord's async nature
    # But retaining 'chat' object is better for multi-turn.
    # We'll assume the caller maintains the 'chat' logic or we rebuild it.
    
    # Refined approach:
    # 1. Take raw history.
    # 2. Append User Input.
    # 3. Send to model with System Prompt.
    
    messages = [{"role": "user", "parts": [SYSTEM_PROMPT]}] + history + [{"role": "user", "parts": [user_input]}]
    
    try:
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

def parse_ticket_data(ai_response_text):
    """
    Attempts to extract the JSON ticket data from the AI's response.
    Returns (is_ready, data_dict_or_none, clean_text)
    """
    try:
        # Look for JSON block
        import re
        match = re.search(r"```json\s*(\{.*?\})\s*```", ai_response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            if data.get("ticket_ready"):
                return True, data, "Ticket summary generated. Please review."
            
        # Try finding raw JSON (if model didn't use markdown)
        start = ai_response_text.find('{')
        end = ai_response_text.rfind('}')
        if start != -1 and end != -1:
             potential_json = ai_response_text[start:end+1]
             data = json.loads(potential_json)
             if data.get("ticket_ready"):
                return True, data, "Ticket summary generated."

    except Exception:
        pass
    
    return False, None, ai_response_text
