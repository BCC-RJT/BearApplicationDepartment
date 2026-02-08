import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from BAD.src.agent.brain import AgentBrain

def test_memory():
    print("Testing AgentBrain.save_memory...")
    brain = AgentBrain()
    
    test_data = {"test_key": "test_value", "timestamp": "now"}
    
    if brain.save_memory(test_data):
        print("✅ save_memory returned True")
    else:
        print("❌ save_memory returned False")
        
    # Verify file content
    # Correct path: .../BAD/config/memory.json
    # __file__ is .../BAD/tests/test_memory.py
    # dirname -> .../BAD/tests
    # dirname -> .../BAD
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    memory_path = os.path.join(project_root, 'config', 'memory.json')
    if os.path.exists(memory_path):
        with open(memory_path, 'r') as f:
            content = json.load(f)
        
        if content == test_data:
            print("✅ Memory file content matches")
        else:
            print(f"❌ Memory file content mismatch: {content}")
    else:
        print(f"❌ Memory file not found at {memory_path}")

if __name__ == "__main__":
    test_memory()
