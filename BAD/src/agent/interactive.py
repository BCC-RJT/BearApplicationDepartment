import asyncio
import sys
import os
import json
import time
import subprocess

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

from src.agent.brain import AgentBrain

# Load Actions Configuration
ACTIONS_CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config', 'actions.json')

def load_actions():
    if os.path.exists(ACTIONS_CONFIG_FILE):
        with open(ACTIONS_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

async def run_script(action_name, args=None):
    """Executes a configured action script."""
    actions_config = load_actions()
    action_config = actions_config.get(action_name)
    
    if not action_config:
        return f"❌ Unknown action: {action_name}"

    script_rel_path = action_config.get("script")
    script_path = os.path.join(PROJECT_ROOT, script_rel_path)
    
    if not os.path.exists(script_path):
        return f"❌ Script not found: {script_path}"

    interpreter = action_config.get("interpreter", "bash")
    use_sudo = action_config.get("sudo", False)
    
    cmd = []
    if use_sudo:
        cmd.append("sudo")
    
    if interpreter:
        if interpreter in ["python", "python3"]:
            cmd.append(sys.executable)
        else:
            cmd.append(interpreter)

    cmd.append(script_path)
    
    if args:
        cmd.extend(args)

    try:
        # Run in PROJECT_ROOT to ensure relative paths in scripts work as expected
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=PROJECT_ROOT
        )
        
        stdout, stderr = await process.communicate()
        
        output = stdout.decode().strip()
        error_output = stderr.decode().strip()
        
        if error_output:
            output += f"\nstderr:\n{error_output}"
            
        return output
    except Exception as e:
        return f"❌ Error running script '{action_name}': {str(e)}"

async def main():
    print("🤖 Agent Session Started. Type 'exit' to quit.")
    brain = AgentBrain()
    
    # Simple history buffer for this session
    history = []
    
    available_actions = load_actions()
    print(f"DEBUG: Loaded {len(available_actions)} actions.")
    
    while True:
        try:
            # Read input from stdin
            if sys.stdin.isatty():
                user_input = input("You: ")
            else:
                user_input = sys.stdin.readline()
                if not user_input:
                    break
                user_input = user_input.strip()
                print(f"You: {user_input}")

            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("Session ending...")
                break
            
            # --- Turn Loop for Autonomy ---
            # Allow the agent to think multiple times if it wants to execute actions
            max_turns = 5 
            current_turn = 0
            
            # Input for the first turn is the user message
            # For subsequent turns, input is the feedback from actions
            current_input = user_input
            
            while current_turn < max_turns:
                current_turn += 1
                
                # If it's not the first turn, we are in an autonomous loop
                # We should append the previous system output to history before thinking
                if current_turn > 1:
                     # History already updated with system output in previous iteration
                     pass
                else:
                    # First turn: User message
                    history.append(f"User: {current_input}")

                response = await brain.think(
                    user_message=current_input if current_turn == 1 else "Continue based on the action output.",
                    available_actions=available_actions,
                    history=history,
                    mode="default"
                )
                
                reply = response.get("reply")
                actions = response.get("actions", [])
                execute_now = response.get("execute_now", False)
                
                # Print Reply
                if reply:
                    print(f"🤖 {reply}")
                    history.append(f"Bot: {reply}")
                
                # Execution Logic
                if actions:
                    # If execute_now is True, we execute and loop
                    # If execute_now is False, we ask for permission (interactive mode means we stop and wait for user)
                    
                    if execute_now:
                        print(f"⚡ Autonomously Executing: {actions}")
                        
                        # Execute all actions
                        outputs = []
                        for action_str in actions:
                            parts = action_str.split()
                            name = parts[0]
                            args = parts[1:] if len(parts) > 1 else []
                            
                            output = await run_script(name, args)
                            print(f"📝 Output of {name}:\n{output}")
                            outputs.append(f"Action '{name}' Output:\n{output}")
                        
                        # Add to history and loop
                        feedback = "\n".join(outputs)
                        history.append(f"System: {feedback}")
                        
                        # Continue loop to let brain analyze output
                        continue
                        
                    else:
                        print(f"⚡ Proposed Actions (Requires Approval): {actions}")
                        print("ℹ️  To approve, type 'yes' (simulated for now, actually we just stop and wait for next user input).")
                        # In this simple interactive script, we don't have a complex approval flow within the loop.
                        # We just break and let the user respond.
                        # If the user wants to approve, they would say "yes, do it" in the NEXT turn.
                        break
                
                # If no actions, or we are done executing/replying, break the autonomous loop
                break
                
            # Keep history manageable
            if len(history) > 20:
                history = history[-20:]
                
        except KeyboardInterrupt:
            print("\nSession interrupted.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
