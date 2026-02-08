import sys
import os
import json
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.brain import AgentBrain

def test_memory_persistence():
    # Setup: Backup existing memory if it exists
    memory_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'memory.json')
    backup_path = memory_path + ".bak"
    if os.path.exists(memory_path):
        shutil.copy(memory_path, backup_path)
    
    try:
        # Reset memory for test
        if os.path.exists(memory_path):
            os.remove(memory_path)

        brain = AgentBrain()
        
        print("Step 1: Saving first memory...")
        brain.save_memory({"preference": "dark_mode"})
        
        print("Step 2: Saving second memory...")
        brain.save_memory("User likes brief answers")
        
        print("Step 3: Loading memory...")
        final_memory = brain.load_memory()
        print(f"Final Memory content: {final_memory}")
        
        try:
            memory_data = json.loads(final_memory)
        except json.JSONDecodeError:
            print("FAIL: Memory is not valid JSON")
            return

        # Verification
        has_pref = "preference" in memory_data and memory_data["preference"] == "dark_mode"
        # Adjusted expectation: The string might be under a "notes" key or similar after refactor
        # For now, let's see what happens. If it overwrites, one will be missing.
        
        has_note = False
        if "notes" in memory_data and isinstance(memory_data["notes"], list):
            has_note = "User likes brief answers" in memory_data["notes"]
        elif isinstance(memory_data, str): # Current behavior might just be a string?
             has_note = "User likes brief answers" in memory_data
        
        if has_pref and has_note:
            print("PASS: Memory contains both updates.")
        else:
            print("FAIL: Memory is missing updates.")
            print(f"Has Preference: {has_pref}")
            print(f"Has Note: {has_note}")

    finally:
        # Cleanup: Restore backup if it existed
        if os.path.exists(backup_path):
            shutil.move(backup_path, memory_path)
        elif os.path.exists(memory_path):
            os.remove(memory_path)

if __name__ == "__main__":
    test_memory_persistence()
