import os
import asyncio
import json
import time
import datetime
import logging
import logging
from dotenv import load_dotenv
import discord
from discord.ext import tasks, commands
from github import Github
from collections import deque

# Paths
# bad_bot.py -> bridge -> src -> BAD
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# repo root -> BearApplicationDepartment
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')

# Add project root to path to import src modules
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.bridge.session_manager import SessionManager

# Setup Logging
LOG_FILE = os.path.join(PROJECT_ROOT, 'logs', 'bad_bot.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("BAD_BOT")

# Load environment variables
load_dotenv(ENV_PATH)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')
ADMIN_USER_ID = int(os.getenv('DISCORD_ALLOWED_USER_ID', '0'))
JANITOR_CHANNEL_ID = int(os.getenv('JANITOR_CHANNEL_ID', '0'))
AGENT_CHANNEL_ID = int(os.getenv('AGENT_CHANNEL_ID', '0'))
AUTHORIZED_ROLE = "BAD_Officer"

HEARTBEAT_FILE = os.path.join(PROJECT_ROOT, 'logs', 'heartbeat.json')
LEDGER_FILE = os.path.join(PROJECT_ROOT, 'config', 'resource_ledger.json')
ACTIONS_CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config', 'actions.json')

# Initialize GitHub
g = Github(GITHUB_TOKEN)
if REPO_NAME:
    repo = g.get_repo(REPO_NAME)
else:
    print("⚠️ Warning: REPO_NAME not set. GitHub features will be disabled.")
    repo = None

# Initialize Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load Actions Configuration
def load_actions():
    if os.path.exists(ACTIONS_CONFIG_FILE):
        with open(ACTIONS_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

ACTIONS = load_actions()

# Integrate Agent Brain
import sys
# Add project root to path to import src modules
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
try:
    from src.agent.brain import AgentBrain
    bot.brain = AgentBrain()
except ImportError as e:
    print(f"⚠️ Warning: AgentBrain import failed: {e}")
    bot.brain = None
    
# Load Cogs
async def load_extensions():
    cogs_dir = os.path.join(PROJECT_ROOT, 'src', 'bridge', 'cogs')
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await bot.load_extension(f'src.bridge.cogs.{filename[:-3]}')
                except Exception as e:
                    print(f"⚠️ Failed to load cog {filename}: {e}")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await load_extensions()
    # Start the scheduled tasks
    if not scheduled_janitor.is_running():
        scheduled_janitor.start()
    if not heartbeat_task.is_running():
        heartbeat_task.start()

# Initialize Session Manager
session_manager = SessionManager()

# Store pending plans: {message_id: {"actions": [], "status": "pending"}}
pending_plans = {}

# Conversational History
history = deque(maxlen=10)

# Authorization Decorator
def authorized_only():
    async def predicate(ctx):
        # 1. Fallback to Admin ID (Root Access)
        if ctx.author.id == ADMIN_USER_ID:
            return True
        
        # 2. Check for Authorized Role
        if isinstance(ctx.author, discord.Member):
            if any(role.name == AUTHORIZED_ROLE for role in ctx.author.roles):
                return True

        # 3. Deny Access
        print(f"⛔ Unauthorized access attempt by {ctx.author.name} ({ctx.author.id})")
        await ctx.send(f"⛔ Access Denied. You need the `{AUTHORIZED_ROLE}` role.")
        return False
    return commands.check(predicate)

@bot.event
async def on_disconnect():
    print("⚠️ Bot disconnected from Discord.")

async def run_script(action_name, args=None):
    """Generic function to run a script based on action name (Async Version)."""
    action_config = ACTIONS.get(action_name)
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
    
    # Add interpreter if needed (e.g. bash, python)
    if interpreter:
        if interpreter in ["python", "python3"]:
            cmd.append(sys.executable)
        else:
            cmd.append(interpreter)

    cmd.append(script_path)
    
    # Append any arguments
    if args:
        cmd.extend(args)

    try:
        start_time = time.time()
        
        # Async Subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        duration = time.time() - start_time
        
        output = stdout.decode().strip()
        error_output = stderr.decode().strip()
        
        if error_output:
            output += f"\nstderr:\n{error_output}"
        
        # Truncate if too long (limit is 2000 chars)
        if len(output) > 1800:
            output = output[:1800] + "\n...(truncated)"

        status_emoji = "✅" if process.returncode == 0 else "⚠️"
        footer = f"⏱️ {duration:.2f}s | Exit Code: {process.returncode}"
        
        return f"{status_emoji} **Action '{action_name}' Completed**\n```{output}```\n{footer}"

    except Exception as e:
        return f"❌ Error running script '{action_name}': {str(e)}"



@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Process commands first (starts with '!')
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    # 1. Check for Active Session (Highest Priority)
    if session_manager.has_active_session(message.channel.id):
        # Forward message to the active process
        success = await session_manager.send_input(message.channel.id, message.content)
        if not success:
            await message.add_reaction("❌")
        return

    # Handle Agent Interactions
    if message.channel.id == AGENT_CHANNEL_ID and bot.brain:
        # Check permissions (simple check for now, can be expanded)
        if message.author.id != ADMIN_USER_ID and not any(role.name == AUTHORIZED_ROLE for role in getattr(message.author, 'roles', [])):
             return # Ignore unauthorized users in agent channel

        async with message.channel.typing():
            # Add user message to history
            history.append(f"User: {message.content}")
            
            # ReAct Loop (Max 3 turns to prevent infinite loops)
            executed_actions = set()
            for turn in range(3):
                print(f"DEBUG: Turn {turn}")
                print(f"DEBUG: History before think:\n{json.dumps(list(history), indent=2)}")
                print(f"DEBUG: Processing User Message: {message.content}")
                try:
                    thought = await bot.brain.think(message.content, ACTIONS, list(history))
                except Exception as e:
                    print(f"ERROR: Brain think failed: {e}")
                    await message.channel.send(f"❌ Brain malfunction: {e}")
                    break
                
                print(f"DEBUG: Brain Thought:\n{json.dumps(thought, indent=2)}")
                
                reply = thought.get("reply", "I'm not sure what to say.")
                actions = thought.get("actions", [])
                plan_summary = thought.get("plan_summary", "")
                thought_process = thought.get("thought_process", "")
                execute_now = thought.get("execute_now", False)

                # Case 1: Execute Immediately (Safe Action)
                if execute_now and actions:
                    # Check for internal actions like 'remember'
                    if actions[0].startswith("remember"):
                        content_to_remember = actions[0].replace("remember ", "", 1)
                        if bot.brain.save_memory(json.loads(content_to_remember) if content_to_remember.startswith("{") else content_to_remember):
                           await message.channel.send("✅ I have updated my long-term memory.")
                        else:
                           await message.channel.send("❌ Failed to save memory.")
                        continue

                    if actions[0] in executed_actions:
                         print(f"DEBUG: Loop detected. Action '{actions[0]}' already executed.")
                         # Break loop to force final reply generation or stop
                         break

                    executed_actions.add(actions[0])
                    await message.channel.send(f"Wait, let me check that... (Running {actions[0]})")
                    
                    # Execute first action (typically these are single safe lookups)
                    action_str = actions[0]
                    parts = action_str.split()
                    action_name = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    
                    result = await run_script(action_name, args)
                    
                    # Add result to history
                    print(f"DEBUG: Action Output:\n{result}")
                    # Add result to history
                    print(f"DEBUG: Action Output:\n{result}")
                    history.append(f"System: Action '{action_str}' completed. Output:\n{result}\n(You must now interpret this output and provide a final answer to the user.)")
                    
                    # Loop back to think again with new info
                    continue

                # Case 2: Propose Plan (Mutating Action)
                elif actions:
                    embed = discord.Embed(
                        title="🧠 Proposed Plan",
                        description=plan_summary[:4096],
                        color=discord.Color.blue()
                    )
                    thought_process_truncated = (thought_process[:1000] + '...') if len(thought_process) > 1000 else thought_process
                    embed.add_field(name="Thinking", value=thought_process_truncated, inline=False)
                    embed.add_field(name="Actions to Execute", value=", ".join(actions), inline=False)
                    embed.set_footer(text="React with ✅ to execute this plan.")
                    
                    plan_msg = await message.channel.send(content=reply, embed=embed)
                    await plan_msg.add_reaction("✅")
                    
                    # Store plan for later execution
                    pending_plans[plan_msg.id] = {
                        "actions": actions,
                        "status": "pending",
                        "author_id": message.author.id
                    }
                    
                    # Add bot reply to history
                    history.append(f"Bot: {reply} [Proposed Plan: {plan_summary}]")
                    break

                # Case 3: Just Chat
                else:
                    await message.channel.send(reply)
                    history.append(f"Bot: {reply}")
                    break

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    message_id = reaction.message.id
    if message_id in pending_plans:
        print(f"DEBUG: Reaction {reaction.emoji} on pending plan {message_id}")
        plan = pending_plans[message_id]
        
        # Verify user allowed to execute (must be same author or admin)
        if user.id != plan['author_id'] and user.id != ADMIN_USER_ID:
            print(f"DEBUG: Unauthorized execution attempt by {user.id}")
            return

        if str(reaction.emoji) == "✅" and plan['status'] == "pending":
            plan['status'] = "executing"
            
            # Ack via update
            embed = reaction.message.embeds[0]
            embed.color = discord.Color.orange()
            embed.set_footer(text="🚀 Executing plan...")
            await reaction.message.edit(embed=embed)
            
            # Execute actions
            results = []
            for action_str in plan['actions']:
                logger.debug(f"Processing pending action: {action_str}")
                
                # Check for internal actions like 'remember'
                if action_str.startswith("remember"):
                    content_to_remember = action_str.replace("remember ", "", 1)
                    logger.debug(f"Executing 'remember' with content: {content_to_remember[:50]}...")
                    if bot.brain.save_memory(json.loads(content_to_remember) if content_to_remember.startswith("{") else content_to_remember):
                        await reaction.message.channel.send("✅ I have updated my long-term memory.")
                    else:
                        logger.error("save_memory failed")
                        await reaction.message.channel.send("❌ Failed to save memory.")
                    continue

                # Parse arguments: "action arg1 arg2"
                parts = action_str.split()
                action_name = parts[0]
                args = parts[1:] if len(parts) > 1 else []

                logger.debug(f"Running script action '{action_name}' with args: {args}")
                await reaction.message.channel.send(f"🔄 Running **{action_name}** with args: {args}...")
                res = await run_script(action_name, args)
                results.append(res)
                await reaction.message.channel.send(res)
            
            # Final update
            embed.color = discord.Color.green()
            embed.set_footer(text="✅ Plan Executed Successfully")
            await reaction.message.edit(embed=embed)
            
            # Cleanup memory
            del pending_plans[message_id]

@tasks.loop(seconds=60)
async def heartbeat_task():
    """Writes a heartbeat to a local file every 60 seconds."""
    try:
        data = {
            "timestamp": time.time(),
            "status": "online",
            "bot_user": str(bot.user)
        }
        # Ensure log directory exists
        os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
        
        with open(HEARTBEAT_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error writing heartbeat: {e}")

@heartbeat_task.before_loop
async def before_heartbeat():
    await bot.wait_until_ready()

@bot.command(name='status')
async def status_cmd(ctx):
    """Checks the system status."""
    try:
        # Check heartbeat file
        last_heartbeat = "Never"
        if os.path.exists(HEARTBEAT_FILE):
             with open(HEARTBEAT_FILE, 'r') as f:
                data = json.load(f)
                timestamp = data.get("timestamp")
                if timestamp:
                    last_heartbeat = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        await ctx.send(f"🟢 **System Online.**\nHeartbeat: {last_heartbeat}\nLast Error: None")
    except Exception as e:
        await ctx.send(f"⚠️ System Unstable: {e}")

@bot.command(name='cost')
async def cost_cmd(ctx):
    """Estimates the monthly run rate."""
    try:
        if not os.path.exists(LEDGER_FILE):
            await ctx.send("💰 **Monthly Run Rate:** Unknown (Ledger missing).")
            return

        with open(LEDGER_FILE, 'r') as f:
            ledger = json.load(f)
        
        total_cost = sum(item.get('estimated_cost_mo', 0) for item in ledger)
        resource_count = len(ledger)

        await ctx.send(f"💰 **Monthly Run Rate:** ${total_cost:.2f}\nActive Resources: {resource_count}")

    except Exception as e:
        await ctx.send(f"❌ Error calculating cost: {e}")

@tasks.loop(hours=24)
async def scheduled_janitor():
    """Runs the janitor script every 24 hours."""
    # This relies on the "cleanup" action existing in actions.json
    if "cleanup" not in ACTIONS:
        print("Warning: 'cleanup' action not configured. Skipping scheduled cleanup.")
        return

    if JANITOR_CHANNEL_ID == 0:
        print("Warning: JANITOR_CHANNEL_ID not set. Skipping scheduled cleanup.")
        return

    channel = bot.get_channel(JANITOR_CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel with ID {JANITOR_CHANNEL_ID}")
        return

    print("⏰ Starting scheduled janitor sweep...")
    await channel.send("⏰ **Daily Janitor Cycle Initiated**...")
    
    report = await run_script("cleanup")
    await channel.send(report)

@scheduled_janitor.before_loop
async def before_janitor():
    await bot.wait_until_ready()

@bot.command(name='idea')
@authorized_only()
async def idea(ctx, *, content: str):
    try:
        if '|' in content:
            title, body = content.split('|', 1)
            title = title.strip()
            body = body.strip()
        else:
            title = content
            body = "No description provided."

        # Create GitHub Issue
        issue = repo.create_issue(title=title, body=body, labels=["triage"])
        
        # Reply to Discord
        await ctx.send(f"✅ Issue #{issue.number} Created: {issue.html_url} - ready for Antigravity processing.")
        
    except Exception as e:
        await ctx.send(f"❌ Error creating issue: {str(e)}")

@bot.group(name='bad', invoke_without_command=True)
@authorized_only()
async def bad(ctx):
    """Base command group for BAD operations."""
    available_actions = ", ".join(ACTIONS.keys())
    await ctx.send(f"**B.A.D. Bot Operations**\nAvailable Actions: {available_actions}\nUsage: `!bad run <action>`")

@bad.command(name='run')
@authorized_only()
async def run_action(ctx, action_name: str):
    """Runs a configured action."""
    await ctx.send(f"🔄 Executing **{action_name}**...")
    report = await run_script(action_name)
    await ctx.send(report)

@bad.command(name='list')
@authorized_only()
async def list_actions(ctx):
    """Lists all available actions."""
    if not ACTIONS:
        await ctx.send("No actions configured.")
        return
        
    msg = "**Available Actions:**\n"
    for name, config in ACTIONS.items():
        msg += f"- **{name}**: {config.get('description', 'No description')}\n"
    await ctx.send(msg)

# Backward compatibility (optional)
@bad.command(name='cleanup')
@authorized_only()
async def cleanup(ctx):
    await run_action(ctx, "cleanup")

# --- BAD Integration ---
import sys
# Add project root to path to import src modules
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
try:
    from src import db
    # Initialize DB on startup
    db.init_db()
except ImportError as e:
    print(f"⚠️ Warning: perform_db_ops failed: {e}")

@bot.command(name='result')
async def get_result_cmd(ctx, job_id: str):
    """Retrieves the latest result link for a given Job ID."""
    try:
        res = db.get_latest_result(job_id)
        if res:
            await ctx.send(f"📂 **Result for Job {job_id}**\nLink: {res['file_url']}\nType: {res['result_type']}\nCreated: {res['created_at']}")
        else:
            await ctx.send(f"⚠️ No results found for Job ID `{job_id}`.")
    except Exception as e:
        await ctx.send(f"❌ Error fetching result: {e}")

@bot.command(name='add_result')
@authorized_only()
async def add_result_cmd(ctx, job_id: str, url: str, rtype: str = 'manual'):
    """Manually adds a result (for testing or admin use)."""
    try:
        row_id = db.add_result(job_id, url, rtype)
        await ctx.send(f"✅ Result added for Job `{job_id}` (Row ID: {row_id})")
    except Exception as e:
        await ctx.send(f"❌ Error adding result: {e}")

# --- Session Management Commands ---

@bot.command(name='kickoff')
@authorized_only()
async def kickoff_cmd(ctx, agent_name: str = "dummy"):
    """Starts an interactive agent session."""
    
    # 1. Define available agents (This could be moved to config)
    agents = {
        "dummy": f"{sys.executable} {os.path.join(PROJECT_ROOT, 'scripts', 'dummy_agent.py')}",
        # Future: "antigravity": "python3 src/agent/main.py ..."
    }
    
    command = agents.get(agent_name)
    if not command:
        await ctx.send(f"❌ Unknown agent: `{agent_name}`. Available: {', '.join(agents.keys())}")
        return

    # 2. Define Callbacks
    async def output_callback(text):
        # Chunking handled by helper if needed, simplistic for now
        if len(text) > 1900:
            text = text[:1900] + "... (truncated)"
        await ctx.send(f"🤖 `{text}`")

    async def exit_callback(code):
        await ctx.send(f"🛑 **Session Ends.** (Exit Code: {code})")

    # 3. Start Session
    success, msg = await session_manager.start_session(ctx.channel.id, command, output_callback, exit_callback)
    await ctx.send(msg)

@bot.command(name='terminate')
@authorized_only()
async def terminate_cmd(ctx):
    """Terminates the active session in this channel."""
    if not session_manager.has_active_session(ctx.channel.id):
        await ctx.send("⚠️ No active session to terminate.")
        return
    
    await ctx.send("🛑 Terminating session...")
    await session_manager.terminate_session(ctx.channel.id)
    await ctx.send("✅ Session terminated.")

# --- End BAD Integration ---

@bad.command(name='setup_agent')
@authorized_only()
async def setup_agent(ctx):
    """Creates a private channel for agent interactions."""
    guild = ctx.guild
    
    # 1. Create content category if not exists
    category_name = "B.A.D. OPERATIONS"
    category = discord.utils.get(guild.categories, name=category_name)
    
    if not category:
        category = await guild.create_category(category_name)
    
    # 2. Create private channel
    channel_name = "agent-uplink"
    existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
    
    if existing_channel:
        await ctx.send(f"⚠️ Channel {existing_channel.mention} already exists. ID: `{existing_channel.id}`")
        return

    # Permissions: Private to Bot and Admin
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }

    try:
        new_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await ctx.send(
            f"✅ **Agent Channel Created!**\n"
            f"Channel: {new_channel.mention}\n"
            f"**Action Required**: Copy this ID `{new_channel.id}` and set it as `AGENT_CHANNEL_ID` in your `.env` file, then restart the bot."
        )
    except Exception as e:
        await ctx.send(f"❌ Error creating channel: {e}")

@bad.command(name='setup_architect')
@authorized_only()
async def setup_architect(ctx, channel_name: str = "mission-control"):
    """Creates a channel for The Architect."""
    guild = ctx.guild
    category_name = "B.A.D. OPERATIONS"
    category = discord.utils.get(guild.categories, name=category_name)
    
    if not category:
        category = await guild.create_category(category_name)
    
    existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
    
    if existing_channel:
        await ctx.send(f"⚠️ Channel {existing_channel.mention} already exists. ID: `{existing_channel.id}`")
        return

    # Permissions: Private to Bot and Admin (and Architect if we had its user object, but we don't yet)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }

    try:
        new_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await ctx.send(
            f"✅ **Architect Studio Created!**\n"
            f"Channel: {new_channel.mention}\n"
            f"ID: `{new_channel.id}`\n"
            f"**Next Step**: Add `PLANNING_CHANNEL_ID={new_channel.id}` to your `.env`."
        )
    except Exception as e:
        await ctx.send(f"❌ Error creating channel: {e}")

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GITHUB_TOKEN or not REPO_NAME:
        print("Error: meaningful environment variables are missing.")
    else:
        bot.run(DISCORD_TOKEN)
