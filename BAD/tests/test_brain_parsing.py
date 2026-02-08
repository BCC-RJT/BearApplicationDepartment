import json
import re

def extract_json(text):
    """
    Proposed robust extraction logic to replace the simple one in brain.py
    """
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON block
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Try to find just the first { and last }
    # This is risky if there are multiple JSONs, but usually we want the outer one
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            potential_json = text[start:end+1]
            return json.loads(potential_json)
    except json.JSONDecodeError:
        pass

    return None

def test_parsing():
    test_cases = [
        ('{"key": "value"}', {"key": "value"}),
        ('```json\n{"key": "value"}\n```', {"key": "value"}),
        ('Here is the json:\n```json\n{"key": "value"}\n```', {"key": "value"}),
        ('Some text {"key": "value"} end text', {"key": "value"}),
        ('Double braces {{ "key": "value" }}', None), # Should fail or need specific handling, likely invalid JSON
    ]

    print("Running JSON Parsing Tests...")
    for i, (input_str, expected) in enumerate(test_cases):
        result = extract_json(input_str)
        status = "✅" if result == expected else f"❌ (Expected {expected}, got {result})"
        print(f"Test {i+1}: {status}")

if __name__ == "__main__":
    test_parsing()
