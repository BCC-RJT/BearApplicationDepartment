import asyncio
import sys
import os

# Add src to path
# Add src to path
# __file__ is inside tests/
# os.path.dirname(__file__) is tests/
# .. is BAD/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.brain import AgentBrain

async def test_smart_logic():
    print("🧠 Initializing Brain for Smart Logic Test...")
    brain = AgentBrain()
    
    if not brain.model:
        print("❌ Brain not initialized (likely missing API Key). Skipping test.")
        return

    # Scenario 1: Vague Request
    print("\n--- Scenario 1: Vague Request ---")
    user_msg_1 = "I need a copy of invoice 124abc"
    history = []
    
    response = await brain.think(user_msg_1, available_actions=["propose_ticket"], history=history, mode="ticket_assistant")
    print(f"User: {user_msg_1}")
    print(f"Bot Reply: {response.get('reply')}")
    print(f"Actions: {response.get('actions')}")

    if any("propose_ticket" in action for action in response.get("actions", [])):
        print("❌ FAILED: Bot proposed ticket too early!")
    else:
        print("✅ PASSED: Bot asked for context.")

    # Scenario 2: Detailed Request
    print("\n--- Scenario 2: Detailed Request ---")
    user_msg_2 = "I need a copy of invoice 124abc from xyz vendor on job ABC for the EOM audit. It's high priority. Attached is the error log."
    # Simulate attachment in message content as per new logic
    user_msg_2_with_attachment = user_msg_2 + "\n\n[System Note: User uploaded files]\n<Attachment: http://example.com/log.txt>"
    
    response = await brain.think(user_msg_2_with_attachment, available_actions=["propose_ticket"], history=[], mode="ticket_assistant")
    print(f"User: {user_msg_2}")
    print(f"Bot Reply: {response.get('reply')}")
    print(f"Actions: {response.get('actions')}")

    if any("propose_ticket" in action for action in response.get("actions", [])):
        print("✅ PASSED: Bot proposed ticket as expected.")
    else:
        print("❌ FAILED: Bot did not propose ticket despite full context.")

if __name__ == "__main__":
    asyncio.run(test_smart_logic())
