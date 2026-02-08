
import sys
import os
import asyncio
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from BAD.src.agent.brain import AgentBrain

async def test_brain_issue_listing():
    print("🧠 Testing Brain Decision for Issue Listing...")
    
    brain = AgentBrain()
    
    # Mock actions as they appear in actions.json
    actions = {
        "issue_manage": {
            "description": "Manage GitHub issues. Arguments: <command> [args...]. Commands: list, get <id>, close <id>, comment <id> <body>."
        },
        "cleanup": {
            "description": "Run the daily janitorial cleanup script."
        }
    }
    
    user_message = "what issues need to be resolved?"
    
    print(f"User Message: '{user_message}'")
    
    try:
        thought = await brain.think(user_message, actions, [])
        print("\n🤔 Brain Thought:")
        print(json.dumps(thought, indent=2))
        
        # Verification
        actions_chosen = thought.get("actions", [])
        if any("issue_manage list" in a for a in actions_chosen):
             print("\n✅ PASS: Brain selected 'issue_manage list'")
        else:
             print("\n❌ FAIL: Brain did NOT select 'issue_manage list'")
             
    except Exception as e:
        print(f"\n❌ Error during think: {e}")

if __name__ == "__main__":
    asyncio.run(test_brain_issue_listing())
