
import asyncio
import os
import sys
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agent.brain import AgentBrain

async def verify_flow():
    print("🚀 Starting Ticket Flow Verification...")
    brain = AgentBrain()
    
    if not brain.model:
        print("❌ AgentBrain not initialized (no API key?). Skipping.")
        return

    history = []
    
    # 1. Initial User Input (Vague/Low Urgency)
    user_inputs = [
        "My payroll report failed.",
        "I need this fixed by end of day.",
        "It's blocking the whole team. No error logs."
    ]
    
    available_actions = [
        "propose_ticket | <Title> | <Urgency> | <Description>",
        "close_ticket"
    ]
    
    print(f"\n🧠 Phase 1: Initial Proposal Generation\n")

    initial_proposal_found = False
    
    for i, user_msg in enumerate(user_inputs):
        print(f"👤 User: {user_msg}")
        history.append(f"User: {user_msg}")
        
        # Think
        folder = await brain.think(
            user_message=user_msg,
            available_actions=available_actions,
            history=history,
            mode="ticket_assistant"
        )
        
        reply = folder.get("reply", "")
        actions = folder.get("actions", [])
        
        print(f"🤖 Bot: {reply}")
        history.append(f"Bot: {reply}")
        
        # Check for propose_ticket
        for action in actions:
            if "propose_ticket" in action:
                print(f"\n✅ SUCCESS: Initial Ticket Proposed!\nAction: {action}")
                initial_proposal_found = True
                break
        
        if initial_proposal_found:
            break
            
    if not initial_proposal_found:
        print("\n❌ FAILED: Agent did not propose an initial ticket.")
        sys.exit(1)

    # 2. Iterative Refinement (High Urgency Adjustment)
    print("\n🔄 Phase 2: Testing Iterative Refinement (Urgency Escalation)...")
    user_correction = "Actually, this is critical. It's blocking the CEO."
    print(f"👤 User: {user_correction}")
    history.append(f"User: {user_correction}")
    
    # Think again
    folder = await brain.think(
        user_message=user_correction,
        available_actions=available_actions,
        history=history,
        mode="ticket_assistant"
    )
    
    reply2 = folder.get("reply", "")
    actions2 = folder.get("actions", [])
    print(f"🤖 Bot: {reply2}")
    
    reproposal_found = False
    for act in actions2:
        if "propose_ticket" in act:
            print(f"\n✅ SUCCESS: Agent RE-PROPOSED ticket!\nAction: {act}")
            # Check if urgency increased (looking for 8, 9, 10 or Critical)
            if any(indicator in act for indicator in ["| 8 |", "| 9 |", "| 10 |", "Critical"]):
                 print("   Verify: Urgency successfully escalated.")
                 reproposal_found = True
            else:
                 print("   ⚠️  Warning: Ticket re-proposed but urgency score might not have increased enough.")
            break
            
    if not reproposal_found:
        print("\n❌ FAILED: Agent did not re-propose ticket after correction.")
        sys.exit(1)
        
    print("\n🎉 ALL TESTS PASSED: Ticket Assistant Flow is working as expected.")

if __name__ == "__main__":
    asyncio.run(verify_flow())
