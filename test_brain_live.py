import sys
import os
import json
from dotenv import load_dotenv

# Setup paths (similar to bad_bot.py)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# We are likely running from C:\...\BearApplicationDepartment
# So PROJECT_ROOT might be that dir.
# But AgentBrain is in BAD/src/agent/brain.py.
# We need to ensure we can import it.

# Assuming we run this from C:\Users\Headsprung\Documents\projects\BearApplicationDepartment
BAD_DIR = os.path.join(os.getcwd(), 'BAD')
if BAD_DIR not in sys.path:
    sys.path.append(BAD_DIR)

# Load .env
load_dotenv()

try:
    from src.agent.brain import AgentBrain
except ImportError:
    # If running from inside BAD/
    sys.path.append(os.getcwd())
    from src.agent.brain import AgentBrain

def test_live_brain():
    print("🧠 Initializing Brain...")
    brain = AgentBrain()
    
    if not brain.client:
        print("❌ Client not initialized (Key missing?)")
        return

    brain.model_name = 'gemini-flash-lite-latest'
    print(f"🤖 Model: {brain.model_name}")
    print("💭 Thinking about 'Hello'...")
    
    # Mock actions
    actions = {"cleanup": {"description": "clean disk"}}
    
    # Run
    result = brain.think("Hello", actions)
    
    print("\n--- Result ---")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_live_brain()
