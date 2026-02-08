import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from BAD.src.agent.brain import AgentBrain

import asyncio

async def test_memory():
    print("🧠 Testing Memory Recall...")
    
    # Initialize Brain
    brain = AgentBrain()
    
    # Mock Actions
    actions = {
        "remember": {
            "description": "Remember/recall info. Args: set <category> <key> <value>",
            "category": "utility"
        }
    }

    # Test 1: Simple Fact
    print("\nTest 1: Simple Fact...")
    prompt = "Please remember that my favorite color is blue."
    print(f"User: {prompt}")
    
    response = await brain.think(prompt, actions, history=[])
    print(f"Response: {json.dumps(response, indent=2)}")
    
    if "remember" in str(response) and "blue" in str(response):
        print("✅ PASS: Correctly identified 'remember' action.")
    else:
        print("❌ FAIL: Did not use 'remember' action.")

    # Test 3: Complex Sentence
    print("\nTest 3: Complex Sentence...")
    prompt = "I have a new server called 'web-prod' at 10.0.0.5, please remember that."
    print(f"User: {prompt}")
    
    response = await brain.think(prompt, actions, history=[])
    print(f"Response: {json.dumps(response, indent=2)}")
    
    if "remember" in str(response) and "10.0.0.5" in str(response):
         print("✅ PASS: Correctly identified 'remember' action.")
    else:
         print("⚠️ WARN: Might have failed complex sentence parsing. Check output.")

    # Test 4: Tricky Quoting
    print("\nTest 4: Tricky Quoting...")
    prompt = "Remember that the alias for 'list' is 'ls -la'."
    print(f"User: {prompt}")
    
    response = await brain.think(prompt, actions, history=[])
    print(f"Response: {json.dumps(response, indent=2)}")
    
    # We expect something like: remember set preferences list_alias "ls -la"
    # or just the unquoted string
    if "remember set" in str(response) and "ls -la" in str(response):
         print("✅ PASS: Correctly identified 'remember' action for quoted value.")
    else:
         print("❌ FAIL: Failed quote handling.")

if __name__ == "__main__":
    asyncio.run(test_memory())
