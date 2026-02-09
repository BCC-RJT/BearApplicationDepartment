import os
import json
import asyncio
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

class AgentBrain:
    def __init__(self):
        self.model = None
        
        if not GOOGLE_API_KEY:
            print("⚠️ Warning: GOOGLE_API_KEY not found. AgentBrain features disabled.")
            return

        # Attempt to verify key with a lightweight call
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            test_model = genai.GenerativeModel('gemini-2.0-flash')
            # Dry run a simple generation to test auth (count_tokens is fast)
            test_model.count_tokens("test")
            self.model = test_model
            print("✅ AgentBrain initialized successfully with Gemini 2.0 Flash")
        except Exception as e:
            print(f"❌ Error initializing AgentBrain (Invalid API Key?): {e}")
            print("⚠️ AgentBrain features disabled due to initialization failure.")
            self.model = None

    def load_memory(self):
        memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'memory.json')
        if os.path.exists(memory_path):
            with open(memory_path, 'r') as f:
                return f.read()
        return "{}"

    def save_memory(self, content):
        """Saves content to the long-term memory file, merging with existing data."""
        try:
            memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'memory.json')
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(memory_path), exist_ok=True)
            
            # Load existing memory
            current_memory = {}
            if os.path.exists(memory_path):
                with open(memory_path, 'r') as f:
                    try:
                        current_memory = json.load(f)
                    except json.JSONDecodeError:
                        print("⚠️ Warning: memory.json was not valid JSON, starting fresh.")
                        current_memory = {}

            # Merge new content
            if isinstance(content, dict):
                current_memory.update(content)
            else:
                if "notes" not in current_memory:
                    current_memory["notes"] = []
                if isinstance(current_memory["notes"], list):
                    current_memory["notes"].append(str(content))
                else:
                    current_memory["notes"] = [str(current_memory["notes"]), str(content)]
            
            with open(memory_path, 'w') as f:
                json.dump(current_memory, f, indent=2)
                
            print(f"DEBUG: Memory saved successfully to {memory_path}")
            return True
        except Exception as e:
            print(f"ERROR: Error saving memory: {e}")
            return False

    def _extract_json(self, text):
        """
        Robustly extracts JSON from a string, handling markdown blocks and loose text.
        """
        import re
        text = text.strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find a JSON block with regex
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        # Try to find from first { to last }
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                potential_json = text[start:end+1]
                return json.loads(potential_json)
        except json.JSONDecodeError:
            pass

        return None

    async def think(self, user_message, available_actions, history=None, status_context=None, mode="default"):
        """
        Processes the user message and returns a structured plan or reply.
        """
        if not self.model:
            # Return a professional "offline" message instead of technical error
            return {"reply": "I apologize, but my AI systems are currently offline. A staff member will be with you shortly."}

        # Load Long-Term Memory
        memory_content = self.load_memory()
        
        # Format Status Context
        status_text = "No active blockers."
        if status_context:
            pending_count = len(status_context.get("pending_plans", []))
            active_sessions = status_context.get("active_sessions", [])
            sync_status = status_context.get("sync_status", "Unknown")
            
            parts = [f"Sync Status: {sync_status}"]
            if pending_count > 0:
                parts.append(f"⛔ WAITING FOR APPROVAL: {pending_count} plan(s) are pending user reaction.")
            if active_sessions:
                parts.append(f"🔄 ACTIVE SESSIONS: Running in channels {active_sessions}.")
            
            if parts:
                status_text = "\n".join(parts)

        # Select System Prompt based on Mode
        if mode == "architect":
            system_prompt = f"""
You are 'Project Planner', a senior technical planner and strategist for 'Bear Application Department'.
Your goal is to help users design robust, scalable, and well-thought-out solutions.

CURRENT STATUS:
{status_text}

**YOUR BEHAVIOR**:
1.  **Clarify First**: Ask clarifying questions to understand the *why*, *who*, and *constraints*.
2.  **Gather Context**: You have access to `read_file` and `list_files`. Use them to read the `docs/`, `engineering-playbook/` or other relevant files in the repo to answer your own questions if possible.
    -   **Project Structure**:
        -   `engineering-playbook/`: Contains the engineering rules, procedures, and standards.
        -   `BAD/docs/`: Contains documentation specific to the 'Bear Application Department' codebase.
    -   Example: "I will read `engineering-playbook/README.md` to understand the standard procedure."
3.  **Plan**: Only when you are satisfied, output a detailed implementation plan in Markdown.
4.  **No Direct Execution**: You CANNOT write code or execute command-line scripts. You only plan.

LONG-TERM MEMORY (Context):
{memory_content}

RESPONSE FORMAT (JSON ONLY):
{{
  "thought_process": "I need to check the docs for the standard issue format...",
  "reply": "I am checking the engineering playbook...",
  "actions": ["read_file engineering-playbook/README.md"],
  "execute_now": true
}}
"""
        elif mode == "manager":
            system_prompt = f"""
You are the 'Session Manager' for the Bear Application Department (BAD) bot.
Your role is to guide the user on how to start working. There is currently NO active conversation session.

CURRENT STATUS:
{status_text}

**YOUR BEHAVIOR**:
1.  **Check Sync Status**: Look at STATUS_TEXT.
    -   If "Environment NOT Synced" -> Suggest running `!open` to sync code and prepare the environment.
    -   If "Environment Synced" -> Suggest running `!kickoff` to start a new Agent Session (conversation).
2.  **Explain Commands**:
    -   `!open`: Syncs the environment (git pull, check clean state).
    -   `!kickoff`: Starts a new conversational agent session.
    -   `!dashboard`: Shows active sessions and pending approvals.
    -   `!sessions`: Lists active sessions.
    -   `!close`: Closes the current session (commits & pushes).
3.  **Proactive Guidance**: If the user tells you what they want to do (e.g., "I want to fix a bug"), acknowledge it but explain that **they must start a session first** to do that.
    -   Example: "That sounds important! To get started on fixing that bug, we first need to open a session. Shall I run `!kickoff` for you?"
4.  **Action Execution**: You can execute safe commands like `!open` or `!kickoff` if the user explicitly asks or agrees to your suggestion.

LONG-TERM MEMORY:
{memory_content}

RESPONSE FORMAT (JSON ONLY):
{{
  "thought_process": "User wants to work but no session is active. Environment is synced.",
  "reply": "To start working on that, we need to kickoff a session. Shall I do that?",
  "actions": [], 
  "execute_now": false
}}
"""
        else:
            # Default / BAD Bot Mode
            system_prompt = f"""
You are an intelligent Discord bot for 'Bear Application Department'.
Your goal is to help users manage their engineering tasks, github issues, and servers.

CURRENT STATUS:
{status_text}

LONG-TERM MEMORY (Preferences & Facts):
{memory_content}

AVAILABLE ACTIONS:
{json.dumps(available_actions, indent=2)}

You can now use a "Conversational Flow":
1.  **Analyze Context**: extensive history is provided. Use it to understand "it", "that", etc.
2.  **Safe Actions**: If the user asks for information (e.g. "list issues", "get issue 1", "read file", "check status"), YOU MUST SET `execute_now` to `true`. Do NOT ask for confirmation. Run it immediately.
3.  **Mutating Actions**: If the user asks to change state (e.g. "close issue", "run cleanup", "delete"), set `execute_now` to `false` and I will ask for confirmation.
4.  **Memory**: Use the `remember` tool ONLY when the user explicitly provides a new preference or fact. Do NOT use it for conversation logging or trivial details.
5.  **Answering**: If the result of an action is in the history, interpret it and Answer the user in the `reply` field. Do NOT create a new plan just to show the answer.
6.  **Formatting**: When listing multiple items with URLs, YOU MUST wrap each URL in `<` and `>` (e.g. `<https://example.com>`) to prevent Discord from generating spammy embeds.

RESPONSE FORMAT (JSON ONLY):
{{
  "thought_process": "Analyze functionality and history...",
  "plan_summary": "Briefly describe what you will do.",
  "actions": ["action_name arg1", "action_name arg2"],
  "execute_now": true/false (true ONLY for read-only/safe actions like 'list' or 'get'),
  "reply": "Message to the user (optional if executing now)"
}}
"""
        
        prompt = f"{system_prompt}\n\n"
        
        if history:
            prompt += "CONVERSATION HISTORY:\n"
            for msg in history:
                prompt += f"{msg}\n"
            prompt += "\n"

        prompt += f"USER MESSAGE: {user_message}"

        max_retries = 3
        backoff = 2

        for attempt in range(max_retries + 1):
            try:
                # Run sync API call in a thread
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json"
                    )
                )
                
                text = response.text
                print(f"DEBUG: RAW MODEL RESPONSE:\n{text}")
                
                if not text:
                    raise ValueError("Empty response from Gemini API")
                
                # Robust JSON Extraction
                parsed_json = self._extract_json(text)
                if parsed_json:
                    return parsed_json
                else:
                    raise ValueError(f"Failed to parse JSON from response: {text[:100]}...")

            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < max_retries:
                    print(f"WARNING: Quota exceeded. Retrying in {backoff}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    print(f"Error in AgentBrain: {e}")
                    return {
                        "thought_process": "Error occurred during processing.",
                        "plan_summary": "",
                        "actions": [],
                        "reply": f"I encountered an error trying to think about that: {error_str[:100]}"
                    }
        else:
            self.client = genai.Client(api_key=GOOGLE_API_KEY)
            # Use a model that supports JSON mode well
            self.model_name = 'gemini-2.0-flash'

    def load_memory(self):
        memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'memory.json')
        if os.path.exists(memory_path):
            with open(memory_path, 'r') as f:
                return f.read()
        return "{}"

    def save_memory(self, content):
        """Saves content to the long-term memory file, merging with existing data."""
        try:
            memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'memory.json')
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(memory_path), exist_ok=True)
            
            # Load existing memory
            current_memory = {}
            if os.path.exists(memory_path):
                with open(memory_path, 'r') as f:
                    try:
                        current_memory = json.load(f)
                    except json.JSONDecodeError:
                        # If file is corrupted or empty, start fresh. 
                        # If it was plain text before, we might want to migrate it, but simple overwrite is safer for now to enforce JSON structure.
                        print("⚠️ Warning: memory.json was not valid JSON, starting fresh.")
                        current_memory = {}

            # Merge new content
            if isinstance(content, dict):
                # Deep merge or top-level update? Let's do top-level update for now.
                current_memory.update(content)
            else:
                # Assume string note
                if "notes" not in current_memory:
                    current_memory["notes"] = []
                if isinstance(current_memory["notes"], list):
                    current_memory["notes"].append(str(content))
                else:
                    # If notes collided with a non-list, force it to list
                    current_memory["notes"] = [str(current_memory["notes"]), str(content)]
            
            with open(memory_path, 'w') as f:
                json.dump(current_memory, f, indent=2)
                
            print(f"DEBUG: Memory saved successfully to {memory_path}")
            return True
        except Exception as e:
            print(f"ERROR: Error saving memory: {e}")
            return False

    def _extract_json(self, text):
        """
        Robustly extracts JSON from a string, handling markdown blocks and loose text.
        """
        import re
        text = text.strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find a JSON block with regex
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        # Try to find from first { to last }
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                potential_json = text[start:end+1]
                return json.loads(potential_json)
        except json.JSONDecodeError:
            pass

        return None

    async def think(self, user_message, available_actions, history=None, status_context=None, mode="default"):
        """
        Processes the user message and returns a structured plan or reply.
        """
        if not self.model:
            # Return a professional "offline" message instead of technical error
            return {"reply": "I apologize, but my AI systems are currently offline. A staff member will be with you shortly."}

        # Load Long-Term Memory
        memory_content = self.load_memory()
        
        # Format Status Context
        status_text = "No active blockers."
        if status_context:
            pending_count = len(status_context.get("pending_plans", []))
            active_sessions = status_context.get("active_sessions", [])
            sync_status = status_context.get("sync_status", "Unknown")
            
            parts = [f"Sync Status: {sync_status}"]
            if pending_count > 0:
                parts.append(f"⛔ WAITING FOR APPROVAL: {pending_count} plan(s) are pending user reaction.")
            if active_sessions:
                parts.append(f"🔄 ACTIVE SESSIONS: Running in channels {active_sessions}.")
            
            if parts:
                status_text = "\n".join(parts)

        # Select System Prompt based on Mode
        if mode == "architect":
            system_prompt = f"""
You are 'Project Planner', a senior technical planner and strategist for 'Bear Application Department'.
Your goal is to help users design robust, scalable, and well-thought-out solutions.

CURRENT STATUS:
{status_text}

**YOUR BEHAVIOR**:
1.  **Clarify First**: Ask clarifying questions to understand the *why*, *who*, and *constraints*.
2.  **Gather Context**: You have access to `read_file` and `list_files`. Use them to read the `docs/`, `engineering-playbook/` or other relevant files in the repo to answer your own questions if possible.
    -   **Project Structure**:
        -   `engineering-playbook/`: Contains the engineering rules, procedures, and standards.
        -   `BAD/docs/`: Contains documentation specific to the 'Bear Application Department' codebase.
    -   Example: "I will read `engineering-playbook/README.md` to understand the standard procedure."
3.  **Plan**: Only when you are satisfied, output a detailed implementation plan in Markdown.
4.  **No Direct Execution**: You CANNOT write code or execute command-line scripts. You only plan.

LONG-TERM MEMORY (Context):
{memory_content}

RESPONSE FORMAT (JSON ONLY):
{{
  "thought_process": "I need to check the docs for the standard issue format...",
  "reply": "I am checking the engineering playbook...",
  "actions": ["read_file engineering-playbook/README.md"],
  "execute_now": true
}}
"""
        elif mode == "manager":
            system_prompt = f"""
You are the 'Session Manager' for the Bear Application Department (BAD) bot.
Your role is to guide the user on how to start working. There is currently NO active conversation session.

CURRENT STATUS:
{status_text}

**YOUR BEHAVIOR**:
1.  **Check Sync Status**: Look at STATUS_TEXT.
    -   If "Environment NOT Synced" -> Suggest running `!open` to sync code and prepare the environment.
    -   If "Environment Synced" -> Suggest running `!kickoff` to start a new Agent Session (conversation).
2.  **Explain Commands**:
    -   `!open`: Syncs the environment (git pull, check clean state).
    -   `!kickoff`: Starts a new conversational agent session.
    -   `!dashboard`: Shows active sessions and pending approvals.
    -   `!sessions`: Lists active sessions.
    -   `!close`: Closes the current session (commits & pushes).
3.  **Proactive Guidance**: If the user tells you what they want to do (e.g., "I want to fix a bug"), acknowledge it but explain that **they must start a session first** to do that.
    -   Example: "That sounds important! To get started on fixing that bug, we first need to open a session. Shall I run `!kickoff` for you?"
4.  **Action Execution**: You can execute safe commands like `!open` or `!kickoff` if the user explicitly asks or agrees to your suggestion.

LONG-TERM MEMORY:
{memory_content}

RESPONSE FORMAT (JSON ONLY):
{{
  "thought_process": "User wants to work but no session is active. Environment is synced.",
  "reply": "To start working on that, we need to kickoff a session. Shall I do that?",
  "actions": [], 
  "execute_now": false
}}
"""
        elif mode == "ticket_assistant":
            system_prompt = f"""
You are the 'Expert Ticket Creation Assistant' for Bear Application Department.
Your goal is to help the user create a perfect ticket by gathering all necessary information.

CURRENT STATUS:
{status_text}

**YOUR BEHAVIOR**:
1.  **Greeting**: If this is the start of the conversation, greet the user warmly and ask how you can help.
2.  **Interview**: Ask follow-up questions to understand:
    -   **What** is the issue?
    -   **Who** is affected?
    -   **When** did it start?
    -   **Severity** (Low, Medium, High, Critical)
3.  **Guidance**: If the user is vague, guide them to be specific.
4.  **Completion**: When you have enough info, summarize it and tell the user to click "Submit Ticket" if they are ready.

LONG-TERM MEMORY:
{memory_content}

RESPONSE FORMAT (JSON ONLY):
{{
  "thought_process": "User just said 'help', I need to ask what's wrong.",
  "reply": "Hello! I'm here to help. What seems to be the issue today?",
  "actions": [], 
  "execute_now": false
}}
"""
        else:
            # Default / BAD Bot Mode
            system_prompt = f"""
You are an intelligent Discord bot for 'Bear Application Department'.
Your goal is to help users manage their engineering tasks, github issues, and servers.

CURRENT STATUS:
{status_text}

LONG-TERM MEMORY (Preferences & Facts):
{memory_content}

AVAILABLE ACTIONS:
{json.dumps(available_actions, indent=2)}

You can now use a "Conversational Flow":
1.  **Analyze Context**: extensive history is provided. Use it to understand "it", "that", etc.
2.  **Safe Actions**: If the user asks for information (e.g. "list issues", "get issue 1", "read file", "check status"), YOU MUST SET `execute_now` to `true`. Do NOT ask for confirmation. Run it immediately.
3.  **Mutating Actions**: If the user asks to change state (e.g. "close issue", "run cleanup", "delete"), set `execute_now` to `false` and I will ask for confirmation.
4.  **Memory**: Use the `remember` tool ONLY when the user explicitly provides a new preference or fact. Do NOT use it for conversation logging or trivial details.
5.  **Answering**: If the result of an action is in the history, interpret it and Answer the user in the `reply` field. Do NOT create a new plan just to show the answer.
6.  **Formatting**: When listing multiple items with URLs, YOU MUST wrap each URL in `<` and `>` (e.g. `<https://example.com>`) to prevent Discord from generating spammy embeds.

RESPONSE FORMAT (JSON ONLY):
{{
  "thought_process": "Analyze functionality and history...",
  "plan_summary": "Briefly describe what you will do.",
  "actions": ["action_name arg1", "action_name arg2"],
  "execute_now": true/false (true ONLY for read-only/safe actions like 'list' or 'get'),
  "reply": "Message to the user (optional if executing now)"
}}
"""
        
        prompt = f"{system_prompt}\n\n"
        
        if history:
            prompt += "CONVERSATION HISTORY:\n"
            for msg in history:
                prompt += f"{msg}\n"
            prompt += "\n"

        prompt += f"USER MESSAGE: {user_message}"

        max_retries = 5
        backoff = 4

        for attempt in range(max_retries + 1):
            try:
                # Run sync API call in a thread to avoid blocking the loop
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json"
                    )
                )
                
                # Parse the JSON response
                usage = response.usage_metadata
                if usage:
                    # Pricing for Gemini 1.5 Flash (approximate fallback for Flash-Lite/Latest)
                    # Input: $0.35 / 1M tokens, Output: $1.05 / 1M tokens
                    input_cost = (usage.prompt_token_count / 1_000_000) * 0.35
                    output_cost = (usage.candidates_token_count / 1_000_000) * 1.05
                    total_cost = input_cost + output_cost
                    
                    print(f"[COST] Usage: Input={usage.prompt_token_count}, Output={usage.candidates_token_count} | Est. Cost: ${total_cost:.6f}")
                
                text = response.text
                print(f"DEBUG: RAW MODEL RESPONSE:\n{text}")
                
                if not text:
                    print(f"DEBUG: Empty response. Candidates: {response.candidates}")
                    if response.candidates:
                         print(f"DEBUG: Finish reason: {response.candidates[0].finish_reason}")
                    raise ValueError("Empty response from Gemini API")
                
                # Robust JSON Extraction
                parsed_json = self._extract_json(text)
                if parsed_json:
                    return parsed_json
                else:
                    raise ValueError(f"Failed to parse JSON from response: {text[:100]}...")

            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < max_retries:
                    print(f"WARNING: Quota exceeded. Retrying in {backoff}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    print(f"Error in AgentBrain: {e}")
                    return {
                        "thought_process": "Error occurred during processing.",
                        "plan_summary": "",
                        "actions": [],
                        "reply": f"I encountered an error trying to think about that: {error_str[:100]}"
                    }
