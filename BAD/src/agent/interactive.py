import asyncio
import sys
import os
import json

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agent.brain import AgentBrain

async def main():
    print("🤖 Agent Session Started. Type 'exit' to quit.")
    brain = AgentBrain()
    
    # Simple history buffer for this session
    history = []
    
    while True:
        try:
            # Read input from stdin
            # In a real shell, input() blocks, but we are running in asyncio context?
            # Actually, let's just use sync input() since session_manager sends lines via pipe
            user_input = await asyncio.to_thread(sys.stdin.readline)
            
            if not user_input:
                break
                
            user_input = user_input.strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("Session ending...")
                break
                
            # Think
            # We need available actions. For now, let's just pass a default set or load from config.
            # Ideally bad_bot passed them, but running standalone means we load independently.
            # Let's verify if actions.json is available.
            actions_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'actions.json')
            available_actions = {}
            if os.path.exists(actions_path):
                with open(actions_path, 'r') as f:
                    available_actions = json.load(f)
            
            response = await brain.think(
                user_message=user_input,
                available_actions=available_actions,
                history=history,
                mode="default" # or architect/etc dynamic based on input? For now default.
            )
            
            # Print response for session manager to capture and send to Discord
            if "reply" in response:
                print(f"🤖 {response['reply']}")
                history.append(f"Bot: {response['reply']}")
            
            if "actions" in response and response["actions"]:
               print(f"⚡ Suggested Actions: {response['actions']}")

            # Update history
            history.append(f"User: {user_input}")
            # Keep history manageable
            if len(history) > 20:
                history = history[-20:]
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
