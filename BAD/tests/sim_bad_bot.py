import sys
import os
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Mock things before importing bad_bot if possible, 
# but bad_bot imports at top level. 
# We'll just import and mock the bot object and brain.

from BAD.src.agent.brain import AgentBrain

# Mock constants if needed? No, logic is generic.

async def test_pending_plan_logic():
    print("🧪 Starting Pending Plan Logic Simulation...")
    
    # 1. Setup Mock Brain
    mock_brain = MagicMock()
    mock_brain.save_memory.return_value = True
    
    # 2. Setup Mock Message/Reaction/User
    mock_user = MagicMock()
    mock_user.id = 12345
    
    mock_message = AsyncMock()
    mock_message.id = 999
    mock_message.channel.send = AsyncMock()
    mock_message.edit = AsyncMock()
    mock_message.embeds = [MagicMock()] # For the embed update
    
    mock_reaction = MagicMock()
    mock_reaction.message = mock_message
    mock_reaction.emoji = "✅"
    
    # 3. Import BAD BOT and Inject Mocks
    import BAD.src.bridge.bad_bot as bad_bot
    bad_bot.brain = mock_brain
    bad_bot.pending_plans = {
        999: {
            "actions": ["remember This is a test memory", "cleanup"],
            "status": "pending",
            "author_id": 12345
        }
    }
    
    # Mock run_script to avoid actual subprocess calls
    bad_bot.run_script = AsyncMock(return_value="✅ Script Ran")
    
    # 4. Trigger on_reaction_add
    print("▶️ Triggering on_reaction_add...")
    await bad_bot.on_reaction_add(mock_reaction, mock_user)
    
    # 5. Verify Results
    print("\n🔍 Verification:")
    
    # 5a. Check Remember
    mock_brain.save_memory.assert_called()
    called_arg = mock_brain.save_memory.call_args[0][0]
    if called_arg == "This is a test memory":
        print("✅ save_memory called with correct string")
    else:
        print(f"❌ save_memory called with unexpected arg: {called_arg}")
        
    # 5b. Check Run Script
    bad_bot.run_script.assert_called_with("cleanup", [])
    print("✅ run_script called for 'cleanup'")
    
    # 5c. Check Message Updates
    # Expect: "Updated memory", "Running cleanup", "Cleanup result", "Plan executed"
    send_calls = [c[0][0] for c in mock_message.channel.send.call_args_list]
    print(f"ℹ️ Messages sent: {send_calls}")
    
    if "✅ I have updated my long-term memory." in send_calls:
        print("✅ Success message sent for memory")
    else:
        print("❌ Success message MISSING for memory")

if __name__ == "__main__":
    asyncio.run(test_pending_plan_logic())
