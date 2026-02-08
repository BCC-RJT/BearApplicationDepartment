#!/usr/bin/env python3
import time
import sys

def type_print(text):
    """Simulates typing effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.02)
    print("")

def main():
    print("🤖 Agent Activated. Initializing...")
    time.sleep(1)
    
    type_print("Hello! I am the Dummy Agent running on the VM.")
    type_print("I am ready to help you with your project.")
    
    print("First, what is the name of this project? > ")
    name = sys.stdin.readline().strip()
    type_print(f"Ah, '{name}'. Sounds ambitious!")
    
    print("Should we start with [Design] or [Code]? > ")
    mode = sys.stdin.readline().strip()
    if mode.lower() == "design":
        type_print("Okay, opening the whiteboard...")
        for i in range(3):
            print(f"Drawing schematics... {i+1}/3")
            time.sleep(1)
        type_print("Design complete! (Not really, I'm a dummy).")
    elif mode.lower() == "code":
        type_print("Firing up the compiler...")
        for i in range(5):
             print(f"Compiling... {i*20}%")
             time.sleep(0.5)
        type_print("Build successful!")
    else:
        type_print("I don't understand that mode. terminating.")
        return

    type_print("Session finished. Goodbye!")

if __name__ == "__main__":
    main()
