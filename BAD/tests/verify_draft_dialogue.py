import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agent.brain import AgentBrain

async def verify_draft_dialogue():
    print("🚀 Starting Draft Ticket Dialogue Verification...")
    brain = AgentBrain()
    
    if not brain.model:
        print("❌ AgentBrain not initialized. Skipping.")
        return

    history = []
    
    # User provides enough info for a draft
    user_inputs = [
        "I need a new repo for the 'Project X' initiative.",
        "It's high priority, need it by tomorrow for the kickoff meeting."
    ]
    
    available_actions = [
        "propose_ticket | <Title> | <Urgency> | <Description>",
        "close_ticket"
    ]
    
    print(f"\n🧠 Phase 1: Checking Draft Proposal Dialogue\n")

    proposal_found = False
    details_confirmed = False
    improvement_asked = False
    submit_reminder = False
    
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
        
        # Check if actions contain propose_ticket
        has_proposal = any("propose_ticket" in action for action in actions)
        
        if has_proposal:
            print(f"\n✅ Ticket Proposed via Action: {actions}")
            proposal_found = True
            
            # NOW Check the REPLY text for the required elements
            reply_lower = reply.lower()
            
            # 1. Ask if details are correct?
            if any(x in reply_lower for x in ["correct", "capture", "right", "details"]):
                details_confirmed = True
                print("   ✅ Checked: Asks if details are correct.")
            else:
                print("   ❌ Missing: Did not ask if details are correct.")

            # 2. Ask for improvements?
            if any(x in reply_lower for x in ["improve", "change", "add", "edit", "missing"]):
                improvement_asked = True
                print("   ✅ Checked: Asks for improvements/changes.")
            else:
                print("   ❌ Missing: Did not ask for improvements.")

            # 3. Remind to Submit/Approve?
            if any(x in reply_lower for x in ["submit", "approve", "accept", "button", "click"]):
                submit_reminder = True
                print("   ✅ Checked: Reminds to submit/click button.")
            else:
                print("   ❌ Missing: Did not remind to submit.")
            
            break

    if not proposal_found:
        print("\n❌ FAILED: Agent did not propose a ticket at all.")
        sys.exit(1)

    if details_confirmed and improvement_asked and submit_reminder:
        print("\n🎉 PASS: Draft dialogue contains all required elements!")
    else:
        print("\n❌ FAIL: Draft dialogue missing required elements.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_draft_dialogue())
