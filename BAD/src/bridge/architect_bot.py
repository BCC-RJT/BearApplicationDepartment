import os
import discord
from discord.ext import commands, tasks
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

# Standardized Token
ARCHITECT_TOKEN = os.getenv('PROJECT_PLANNER_TOKEN') or os.getenv('ARCHITECT_TOKEN')
if not ARCHITECT_TOKEN:
    print("⚠️ PROJECT_PLANNER_TOKEN not found. Falling back to DISCORD_TOKEN.")
    ARCHITECT_TOKEN = os.getenv('DISCORD_TOKEN')

# If not set, it won't listen anywhere specific (or we could enforce it)
PLANNING_CHANNEL_ID = int(os.getenv('PLANNING_CHANNEL_ID', '0'))
ADMIN_USER_ID = int(os.getenv('DISCORD_ALLOWED_USER_ID', '0'))

# Initialize Discord
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True # Required for guild cache
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



# Ticket Workflow Configuration
MANAGER_INBOX_ID = int(os.getenv('TICKET_MANAGER_INBOX_ID', '1470455385231200337'))
INCOMING_TICKETS_ID = int(os.getenv('TICKET_INCOMING_ID', '0')) # Will try to find/create if 0
ACTIVE_TICKETS_ID = int(os.getenv('TICKET_ACTIVE_ID', '1470455386313326839'))
BLOCKED_ESCALATED_ID = int(os.getenv('TICKET_BLOCKED_ID', '1470455387017707611'))
CLOSED_ARCHIVES_ID = int(os.getenv('TICKET_ARCHIVES_ID', '1470455388317941871'))

# --- Ticket System ---

@bot.event
async def on_ready():
    print(f'📐 Project Planner is online as {bot.user} (v3.2 - Core Planning Only)')
    print(f'   ID: {bot.user.id}')
    print(f'   Primary Planning Channel ID: {PLANNING_CHANNEL_ID}')
    
    # Reset Identity 
    for guild in bot.guilds:
        try:
            old_nick = guild.me.nick
            if old_nick != "Project Planner":
                await guild.me.edit(nick="Project Planner")
        except:
            pass

    sys.stdout.flush()
    print("Architect Bot: on_ready triggered")



# Ticket setup removed from Architect Bot

@bot.event
async def on_guild_channel_create(channel):
    # Legacy logic removed. We now create channels directly via button.
    pass

@bot.event
async def on_guild_channel_update(before, after):
    # Legacy redirect logic removed.
    pass


# --- Ticket Commands ---

@bot.group(name='ticket', invoke_without_command=True)
async def ticket_cmd(ctx):
    """Ticket workflow commands."""
    await ctx.send("Usage: `?ticket [active|block|close]`")

async def move_ticket_helper(ctx, category_id, category_name):
    if not ctx.channel.name.lower().startswith("ticket-"):
        await ctx.send("❌ This command can only be used in ticket channels.")
        return

    try:
        category = ctx.guild.get_channel(category_id)
        if not category:
            await ctx.send(f"❌ Category not found: {category_name} (ID: {category_id})")
            return
        
        await ctx.channel.edit(category=category)
        await ctx.send(f"✅ Moved to **{category_name}**")
    except Exception as e:
        await ctx.send(f"❌ Failed to move ticket: {e}")

@ticket_cmd.command(name='active')
async def ticket_active(ctx):
    """Moves ticket to Active."""
    await move_ticket_helper(ctx, ACTIVE_TICKETS_ID, "⚡ Active Tickets")

@ticket_cmd.command(name='block')
async def ticket_block(ctx):
    """Moves ticket to Blocked."""
    await move_ticket_helper(ctx, BLOCKED_ESCALATED_ID, "⛔ Blocked / Escalated")

@ticket_cmd.command(name='close')
async def ticket_close(ctx):
    """Moves ticket to Archives, saves transcript, and locks it."""
    category_id = CLOSED_ARCHIVES_ID
    category_name = "🗄️ Closed Archives"
    
    if not ctx.channel.name.lower().startswith("ticket-"):
        await ctx.send("❌ This command can only be used in ticket channels.")
        return

    try:
        category = ctx.guild.get_channel(category_id)
        if not category:
            await ctx.send(f"❌ Category not found: {category_name} (ID: {category_id})")
            return

        # Generate Transcript
        await ctx.send("📝 Generating transcript...")
        try:
            messages = [msg async for msg in ctx.channel.history(limit=None, oldest_first=True)]
            transcript = []
            for msg in messages:
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                transcript.append(f"[{timestamp}] {msg.author.name}: {msg.content}")
                if msg.attachments:
                    for att in msg.attachments:
                        transcript.append(f"    [Attachment] {att.url}")
            
            transcript_content = "\n".join(transcript)
            file_name = f"transcript-{ctx.channel.name}.txt"
            
            # Create a temporary file
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(transcript_content)
            
            # Send file to channel
            await ctx.send(file=discord.File(file_name))
            os.remove(file_name) # Cleanup
            
        except Exception as e:
            print(f"❌ [Ticket] Transcript failed: {e}")
            await ctx.send(f"⚠️ Failed to generate transcript: {e}")

        # Archive Channel
        await ctx.channel.edit(category=category, sync_permissions=True)
        await ctx.send(f"✅ Moved to **{category_name}** & Permissions Locked.")
    except Exception as e:
        await ctx.send(f"❌ Failed to close ticket: {e}")

=======
# Listener removed to prevent potential conflicts
@bot.event
async def on_guild_channel_create(channel):
        print(f"Architect Bot: New channel detected: {channel.name} (ID: {channel.id})")
        sys.stdout.flush()
>>>>>>> origin/main

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
    if hasattr(channel, "name") and channel.name.lower().startswith("ticket-"):
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
