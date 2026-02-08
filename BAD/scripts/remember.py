import os
import sys
import json
import argparse

# Path to memory file
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = os.path.join(PROJECT_ROOT, 'config', 'memory.json')

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"preferences": {}, "facts": {}}
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"preferences": {}, "facts": {}}

def save_memory(data):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def set_memory(args):
    data = load_memory()
    category = args.category # preferences or facts
    key = args.key
    value = " ".join(args.value)
    
    if category not in data:
        data[category] = {}
        
    data[category][key] = value
    save_memory(data)
    print(f"✅ Remembered: {category}.{key} = {value}")

def get_memory(args):
    data = load_memory()
    category = args.category
    key = args.key
    
    if category in data and key in data[category]:
        print(data[category][key])
    else:
        print(f"❌ Unknown memory: {category}.{key}")

def list_memory(args):
    data = load_memory()
    print(json.dumps(data, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Manage Bot Memory")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Set
    parser_set = subparsers.add_parser('set', help='Remember a value')
    parser_set.add_argument('category', choices=['preferences', 'facts'], help='Category')
    parser_set.add_argument('key', help='Key')
    parser_set.add_argument('value', nargs='+', help='Value')

    # Get
    parser_get = subparsers.add_parser('get', help='Recall a value')
    parser_get.add_argument('category', choices=['preferences', 'facts'], help='Category')
    parser_get.add_argument('key', help='Key')

    # List
    parser_list = subparsers.add_parser('list', help='List all memory')

    args = parser.parse_args()

    if args.command == 'set':
        set_memory(args)
    elif args.command == 'get':
        get_memory(args)
    elif args.command == 'list':
        list_memory(args)

if __name__ == "__main__":
    main()
