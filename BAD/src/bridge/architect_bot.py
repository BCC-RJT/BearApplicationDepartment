import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
from collections import deque
import asyncio

# Paths
# architect_bot.py -> bridge -> src -> BAD
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# repo root -> BearApplicationDepartment
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')

# Load environment variables
load_dotenv(ENV_PATH)

ARCHITECT_TOKEN = os.getenv('ARCHITECT_TOKEN')
if not ARCHITECT_TOKEN:
    print("⚠️ ARCHITECT_TOKEN not found. Falling back to DISCORD_TOKEN.")
    ARCHITECT_TOKEN = os.getenv('DISCORD_TOKEN')

# If not set, it won't listen anywhere specific (or we could enforce it)
PLANNING_CHANNEL_ID = int(os.getenv('PLANNING_CHANNEL_ID', '0'))
ADMIN_USER_ID = int(os.getenv('DISCORD_ALLOWED_USER_ID', '0'))

# Initialize Discord
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Required to see members in channels
bot = commands.Bot(command_prefix='?', intents=intents)

# Integrate Agent Brain
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from src.agent.brain import AgentBrain
    brain = AgentBrain()
except ImportError as e:
    print(f"⚠️ Warning: AgentBrain import failed: {e}")
    brain = None

# Conversational History
history = deque(maxlen=20)

@bot.event
async def on_ready():
    print(f'📐 Project Planner is online as {bot.user}')
    print(f'   Primary Planning Channel ID: {PLANNING_CHANNEL_ID}')
    print(f'   Ready to manage tickets.')
    sys.stdout.flush()

@bot.event
async def on_guild_channel_create(channel):
    """Detects new ticket channels and joins them."""
    print(f"DEBUG: Channel Created Event: {channel.name} (ID: {channel.id}, Type: {channel.type})")
    
    if isinstance(channel, discord.TextChannel) and channel.name.startswith("ticket-"):
        print(f"DEBUG: Detected new ticket channel: {channel.name}")
        # Wait a bit for permissions to settle
        await asyncio.sleep(2) 
        try:
            greeting = (
                "**Project Planner (Architect) connected.**\n"
                "I am here to help you design your project ecosystem.\n"
                "Describe your feature or requirement, and I will help you plan it.\n"
                "When finished, run `?workflow` to generate the implementation plan."
            )
            await channel.send(greeting)
        except Exception as e:
            print(f"❌ Error sending greeting to {channel.name}: {e}")

# Tools
def read_file(path_arg):
    try:
        path_arg = path_arg.strip().strip("'").strip('"')
        full_path = os.path.abspath(os.path.join(REPO_ROOT, path_arg))
        if not full_path.startswith(REPO_ROOT):
             return "❌ Error: Access denied. Path must be within the repository."
        if not os.path.exists(full_path):
             return f"❌ Error: File not found: {path_arg}"
        if os.path.isdir(full_path):
             return f"❌ Error: {path_arg} is a directory. Use list_files instead."
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"❌ Error reading file: {e}"

def list_files(path_arg="."):
    try:
        path_arg = path_arg.strip().strip("'").strip('"')
        full_path = os.path.abspath(os.path.join(REPO_ROOT, path_arg))
        if not full_path.startswith(REPO_ROOT):
             return "❌ Error: Access denied."
        if not os.path.exists(full_path):
             return f"❌ Error: Path not found: {path_arg}"
        
        items = []
        for item in os.listdir(full_path):
            p = os.path.join(full_path, item)
            kind = "DIR" if os.path.isdir(p) else "FILE"
            items.append(f"[{kind}] {item}")
        return "\n".join(items) if items else "(Empty Directory)"
    except Exception as e:
        return f"❌ Error listing files: {e}"

ARCHITECT_TOOLS = [
    {"name": "read_file", "description": "Reads the content of a file. Usage: read_file path/to/file"},
    {"name": "list_files", "description": "Lists files in a directory. Usage: list_files path/to/dir"}
]

def is_authorized_channel(channel):
    # Allow dedicated planning channel OR any ticket-* channel
    if channel.id == PLANNING_CHANNEL_ID:
        return True
    if hasattr(channel, "name") and channel.name.startswith("ticket-"):
        return True
    return False

@bot.command(name='workflow')
async def workflow_cmd(ctx):
    """Generates a workflow from the current conversation."""
    if not is_authorized_channel(ctx.channel):
        return

    print(f"DEBUG: Generating workflow for {ctx.channel.name}")
    async with ctx.typing():
        # Fetch ephemeral history from this channel (up to 50 messages)
        # Note: We use actual channel history here instead of the bot's deque for a full context summary
        messages = [msg async for msg in ctx.channel.history(limit=50, oldest_first=True)]
        
        conversation_log = []
        for msg in messages:
            author = "Bot" if msg.author == bot.user else f"User ({msg.author.name})"
            conversation_log.append(f"{author}: {msg.content}")
        
        # Manually invoke brain to summarize
        if brain:
            prompt = (
                "SYSTEM: The user has requested a final 'Project Workflow' or 'Implementation Plan' based on the conversation above. "
                "Please generate a comprehensive Markdown document summarizing the plan, requirements, and next steps. "
                "Do not ask for more clarification; just do your best to summarize the current state."
            )
            
            # We treat this as a single turn 'think'
            thought = await brain.think(
                user_message=prompt,
                available_actions=[], # No tools for summary
                history=conversation_log,
                mode="architect"
            )
            
            reply = thought.get("reply", "Failed to generate workflow.")
            
            # Split and send
            if len(reply) > 1900:
                for i in range(0, len(reply), 1900):
                    await ctx.send(reply[i:i+1900])
            else:
                await ctx.send(reply)
            
            await ctx.send("✅ **Workflow Generation Complete.**")

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Process commands first (workflow, etc)
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # Filter by Channel
    if not is_authorized_channel(message.channel):
        return

    print(f"DEBUG: Received message from {message.author}: {message.content[:50]}...")
    sys.stdout.flush()

    # Architect Logic
    if brain:
        async with message.channel.typing():
            # Add user message to history (local deque)
            # Note: For the 'workflow' command we read actual chat history, 
            # but for conversation continuity we still use this deque.
            history.append(f"User: {message.content}")
            
            # ReAct Loop (Max 5 turns)
            for turn in range(5):
                print(f"DEBUG: Calling Brain (Turn {turn})...")
                sys.stdout.flush()
                
                thought = await brain.think(
                    user_message=message.content if turn == 0 else "System: Actions completed. Proceed.", 
                    available_actions=ARCHITECT_TOOLS,
                    history=list(history),
                    mode="architect"
                )
                
                # Debug
                print(f"DEBUG: Architect Thought:\n{json.dumps(thought, indent=2)}")
                sys.stdout.flush()
                
                reply = thought.get("reply", "")
                actions = thought.get("actions", [])
                
                # Execute Actions
                if actions:
                    # Notify user of action execution if reply provided
                    if reply:
                        await message.channel.send(reply)
                    
                    for action_str in actions:
                        print(f"DEBUG: Executing Action: {action_str}")
                        parts = action_str.split(maxsplit=1)
                        if not parts: continue
                        cmd = parts[0]
                        arg = parts[1] if len(parts) > 1 else "."
                        
                        output = ""
                        if cmd == "read_file":
                            output = read_file(arg)
                        elif cmd == "list_files":
                            output = list_files(arg)
                        else:
                            output = f"Unknown action: {cmd}"
                        
                        # Add Result to History
                        history.append(f"System: Action '{action_str}' Output:\n{output[:4000]}...") # Truncate large files
                    
                    continue # Loop back to 'think' with new info
                
                else:
                    # Final Reply (No more actions)
                    if reply:
                        # Chunk long replies
                        if len(reply) > 1900:
                            for i in range(0, len(reply), 1900):
                                await message.channel.send(reply[i:i+1900])
                        else:
                            await message.channel.send(reply)
                        
                        history.append(f"Planner: {reply}")
                    break

if __name__ == "__main__":
    if not ARCHITECT_TOKEN:
        print("❌ Error: ARCHITECT_TOKEN not found in .env")
    else:
        bot.run(ARCHITECT_TOKEN)
