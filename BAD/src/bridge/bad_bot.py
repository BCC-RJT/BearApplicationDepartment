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
# REPO_ROOT calculation
# Local: .../BearApplicationDepartment/BAD/src/bridge
# VM: /home/Headsprung/BAD/src/bridge (BAD is sibling to BearApplicationDepartment? or standalone?)

# Try to find the actual repo root
candidate_root = os.path.dirname(PROJECT_ROOT) # Default parent
if os.path.isdir(os.path.join(candidate_root, ".git")):
    REPO_ROOT = candidate_root
elif os.path.isdir(os.path.join(candidate_root, "BearApplicationDepartment")):
    # VM Structure: ~/BAD and ~/BearApplicationDepartment
    REPO_ROOT = os.path.join(candidate_root, "BearApplicationDepartment")
else:
    # Fallback to PROJECT_ROOT or current dir, but warn
    print("⚠️ Warning: Could not find git root. Defaulting REPO_ROOT to PROJECT_ROOT.")
    REPO_ROOT = PROJECT_ROOT

ENV_PATH = os.path.join(REPO_ROOT, '.env')
# Fallback for .env if not found in REPO (e.g. if running in detached BAD)
if not os.path.exists(ENV_PATH):
     ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# Add project root to path to import src modules
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.bridge.session_manager import SessionManager

# Setup Logging
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
TEST_BOT_USER_ID = int(os.getenv('TEST_BOT_USER_ID', '0'))


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
    
    # Initialize state
    bot.is_env_synced = False
    
    # Force nickname update to match branding
    for guild in bot.guilds:
        try:
            await guild.me.edit(nick="BADbot")
            print(f"DEBUG: Updated nickname in {guild.name} to BADbot")
        except Exception as e:
            print(f"⚠️ Failed to update nickname in {guild.name}: {e}")

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
        
        # 2a. Check for Test Bot (Impersonation)
        if ctx.author.id == TEST_BOT_USER_ID:
            # Guardrail: Only allow in specific channels
            if ctx.channel.id != AGENT_CHANNEL_ID:
                print(f"⛔ Test Bot attempted access in unauthorized channel: {ctx.channel.name}")
                return False
            logger.info(f"🧪 Test Bot Authorized (Impersonating Admin) in {ctx.channel.name}")
            return True

        # 3. Check for Authorized Role
        if isinstance(ctx.author, discord.Member):
            if any(role.name == AUTHORIZED_ROLE for role in ctx.author.roles):
                return True

        # 4. Deny Access
        logger.warning(f"⛔ Unauthorized access attempt by {ctx.author.name} ({ctx.author.id})")
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
        # Ensure we run in the REPO_ROOT so git commands work
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=REPO_ROOT
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
    # Debug: Log all messages
    print(f"DEBUG: Message from {message.author} ({message.author.id}): {message.content}")

    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Allow Test Bot to bypass "ignore bots" rule
    is_test_bot = (message.author.id == TEST_BOT_USER_ID)

    # Process commands first (starts with '!')
    if message.content.startswith('!'):
        if is_test_bot:
            # Manually permit bot to run command
            ctx = await bot.get_context(message)
            if ctx.valid:
                print(f"DEBUG: Invoking command for Test Bot: {ctx.command}")
                await bot.invoke(ctx)
            else:
                print("DEBUG: Invalid command context for Test Bot")
        else:
            await bot.process_commands(message)
        return

    # 1. Check for Active Session (Highest Priority)
    if session_manager.has_active_session(message.channel.id):
        # Forward message to the active process
        success = await session_manager.send_input(message.channel.id, message.content)
        if not success:
            await message.add_reaction("❌")
        return

    # Natural Language Manager (No Session Active)
    if message.channel.id == AGENT_CHANNEL_ID and bot.brain:
        # Check permissions
        if message.author.id != ADMIN_USER_ID and message.author.id != TEST_BOT_USER_ID and not any(role.name == AUTHORIZED_ROLE for role in getattr(message.author, 'roles', [])):
             return # Ignore unauthorized users

        async with message.channel.typing():
            # Add user message to history
            history.append(f"User: {message.content}")
            
            # Determine context
            sync_status = "Environment Synced" if getattr(bot, "is_env_synced", False) else "Environment NOT Synced"
            
            status_context = {
                "active_sessions": list(session_manager.sessions.keys()),
                "sync_status": sync_status,
                "pending_plans": [
                    {
                        "id": msg_id,
                        "plan": plan["actions"], 
                        "status": plan["status"],
                        "author": plan["author_id"]
                    } for msg_id, plan in pending_plans.items()
                ]
            }
            
            # ReAct Loop (Simplified for Manager)
            executed_actions = set()
            for turn in range(3):
                print(f"DEBUG: Turn {turn}")
                try:
                    thought = await bot.brain.think(
                        user_message=message.content,
                        available_actions=ACTIONS, 
                        history=list(history), 
                        status_context=status_context,
                        mode="manager"
                    )
                except Exception as e:
                    print(f"ERROR: Brain think failed: {e}")
                    await message.channel.send(f"❌ Brain malfunction: {e}")
                    break
                
                print(f"DEBUG: Brain Thought:\n{json.dumps(thought, indent=2)}")
                
                reply = thought.get("reply", "")
                actions = thought.get("actions", [])
                execute_now = thought.get("execute_now", False)

                # Prioritize executing actions if 'execute_now' is true (for manager this is usually command invocation)
                if execute_now and actions:
                    if actions[0] in executed_actions:
                         break
                    executed_actions.add(actions[0])
                    
                    if reply:
                        await message.channel.send(reply)

                    # Execute the command
                    action_str = actions[0]
                    # Check for internal bot commands
                    if "open" in action_str:
                         ctx = await bot.get_context(message)
                         await bot.invoke(bot.get_command("open"))
                    elif "kickoff" in action_str:
                         ctx = await bot.get_context(message)
                         await bot.invoke(bot.get_command("kickoff"))
                    elif "dashboard" in action_str:
                         ctx = await bot.get_context(message)
                         await bot.invoke(bot.get_command("dashboard"))
                    elif "sessions" in action_str:
                         ctx = await bot.get_context(message)
                         await bot.invoke(bot.get_command("sessions"))
                    elif "close" in action_str:
                         ctx = await bot.get_context(message)
                         await bot.invoke(bot.get_command("close"))
                    else:
                        # Fallback to run_script
                        await message.channel.send(f"🔄 Running **{action_str}**...")
                        parts = action_str.split()
                        res = await run_script(parts[0], parts[1:] if len(parts)>1 else [])
                        await message.channel.send(res)
                        history.append(f"System: Action '{action_str}' output:\n{res}")

                    continue

                # Just Reply
                if reply:
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

@bot.command(name='kickoff')
@authorized_only()
async def kickoff_cmd(ctx):
    """Starts a new interactive agent session."""
    
    # Ensure environment is synced (optional check, or just warn)
    if not getattr(bot, "is_env_synced", False):
        await ctx.send("⚠️ **Environment NOT Synced**\nIt is recommended to run `!open` first to ensure code is up to date.")
    
    script_path = os.path.join(PROJECT_ROOT, "src", "agent", "interactive.py")
    if not os.path.exists(script_path):
        await ctx.send(f"❌ Error: Agent script not found at `{script_path}`")
        return

    cmd = f"python3 {script_path}"
    
    success, msg = await session_manager.start_session(
        ctx.channel.id, 
        cmd, 
        lambda text: ctx.send(f"🤖 {text}"), 
        lambda code: ctx.send(f"🛑 Session ended with code {code}.")
    )
    
    await ctx.send(msg)

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


@bot.command(name='reset')
@authorized_only()
async def reset_cmd(ctx):
    """Resets the conversation history."""
    history.clear()
    await ctx.send("🧹 **Memory Wiped.** Conversation history has been cleared.")

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

@bot.command(name='open')
@authorized_only()
async def open_session_cmd(ctx):
    """Runs the session opening checklist and prepares for an agent session."""
    
    # 1. Run Session Start Script
    status_msg = await ctx.send("🔄 **Initiating Session Start Protocol...**\nRunning checklist and syncing environment...")
    
    report = await run_script("session_start")
    
    # Check for failure in report content (simple heuristic since run_script returns string)
    # Ideally run_script would return a structured object, but current impl returns a string.
    # The string contains "Exit Code: X".
    
    success = "Exit Code: 0" in report
    
    if not success:
        await ctx.send(f"❌ **Session Start Failed**\n{report}\n\n**Action Required**: Fix the issues above (e.g., commit changes) and try `!open` again.")
        return

    # 2. Success - Ready
    bot.is_env_synced = True
    await ctx.send(f"✅ **Environment Synced**\n{report}")
    await ctx.send("🎯 **Session Ready**\nYou can now start working or launch an agent with `!kickoff`.")

@bot.command(name='close')
@authorized_only()
async def close_session_cmd(ctx, *, message: str = ""):
    """Runs the session closing checklist and commits work."""
    
    await ctx.send("🔄 **Initiating Session End Protocol...**\nChecking for changes and committing...")
    
    # 1. Run Session End Script
    args = [message] if message else []
    report = await run_script("session_end", args)
    
    # Check for success
    success = "Exit Code: 0" in report
    
    if not success:
         await ctx.send(f"❌ **Session Close Failed**\n{report}")
         return

    # 2. Success
    await ctx.send(f"✅ **Session Closed**\n{report}")

@bot.command(name='sessions')
@authorized_only()
async def sessions_cmd(ctx):
    """Lists all active agent sessions."""
    if not session_manager.sessions:
        await ctx.send("There are no active sessions running.")
        return

    msg = "**Active Sessions:**\n"
    for channel_id, session in session_manager.sessions.items():
        channel = bot.get_channel(channel_id)
        channel_name = channel.mention if channel else f"ID: {channel_id}"
        msg += f"- **Channel**: {channel_name} | **Command**: `{session['command']}`\n"
    
    await ctx.send(msg)

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

# --- Manager Dashboard ---

class DashboardView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        embed = create_dashboard_embed()
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Approve All Pending", style=discord.ButtonStyle.success, emoji="✅")
    async def approve_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Specific permission check for dangerous actions
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message("⛔ Only the Admin can block-approve.", ephemeral=True)
            return

        if not pending_plans:
            await interaction.response.send_message("No pending plans to approve.", ephemeral=True)
            return

        await interaction.response.send_message(f"🚀 Approving {len(pending_plans)} plans...", ephemeral=True)
        
        # We need to copy keys to avoid runtime error during iteration if size changes
        plan_ids = list(pending_plans.keys())
        
        for msg_id in plan_ids:
            if msg_id not in pending_plans: continue
            plan = pending_plans[msg_id]
            
            # Execute actions (Reusing logic from on_reaction_add - ideally should be refactored to a function)
            plan['status'] = "executing"
            
            # Log to channel that we are auto-executing
            # We try to fetch the original message to reply to it, but it might be old
            # So we just post to the interaction channel (which should be the dashboard channel)
            await self.ctx.send(f"🤖 **Batch Executing Plan {msg_id}**")
            
            for action_str in plan['actions']:
                # ... (Execution Logic Duplicated for safety/speed, or call helper)
                # For robustness in this prompt, I will call run_script directly
                parts = action_str.split()
                action_name = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                await self.ctx.send(f"🔄 Running **{action_name}** {args}...")
                res = await run_script(action_name, args)
                await self.ctx.send(res)
            
            del pending_plans[msg_id]

        # Refresh dashboard
        embed = create_dashboard_embed()
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Kill All Sessions", style=discord.ButtonStyle.danger, emoji="🛑")
    async def kill_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message("⛔ Access Denied.", ephemeral=True)
            return

        if not session_manager.sessions:
            await interaction.response.send_message("No active sessions.", ephemeral=True)
            return

        count = len(session_manager.sessions)
        await interaction.response.send_message(f"🛑 Terminating {count} sessions...", ephemeral=True)
        
        channel_ids = list(session_manager.sessions.keys())
        for cid in channel_ids:
            await session_manager.terminate_session(cid)
            await self.ctx.send(f"💀 Session in <#{cid}> terminated via Dashboard.")

        # Refresh dashboard
        embed = create_dashboard_embed()
        await interaction.message.edit(embed=embed, view=self)

def create_dashboard_embed():
    embed = discord.Embed(title="📱 B.A.D. Manager Portal", color=discord.Color.dark_theme())
    
    # 1. Active Sessions
    if session_manager.sessions:
        sessions_text = ""
        for cid, sess in session_manager.sessions.items():
            sessions_text += f"• <#{cid}>: `{sess['command']}`\n"
    else:
        sessions_text = "*No active agent sessions.*"
    embed.add_field(name="running_processes", value=sessions_text, inline=False)

    # 2. Pending Blockers
    if pending_plans:
        blockers_text = ""
        for mid, plan in pending_plans.items():
            actions = ", ".join(plan['actions'])
            blockers_text += f"• ⚠️ **Plan {mid}**: `{actions}`\n"
    else:
        blockers_text = "✅ *All clear. No blockers.*"
    embed.add_field(name="pending_approvals", value=blockers_text, inline=False)
    
    # 3. System Status
    heartbeat = "Unknown"
    if os.path.exists(HEARTBEAT_FILE):
        try:
            with open(HEARTBEAT_FILE, 'r') as f:
                data = json.load(f)
                ts = data.get("timestamp", 0)
                heartbeat = f"<t:{int(ts)}:R>"
        except: pass
        
    embed.add_field(name="system_health", value=f"Last Heartbeat: {heartbeat}\nLatency: {bot.latency*1000:.0f}ms", inline=False)
    embed.set_footer(text=f"Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")
    return embed

@bot.command(name='dashboard')
@authorized_only()
async def dashboard_cmd(ctx):
    """Opens the interactive Manager Dashboard."""
    embed = create_dashboard_embed()
    view = DashboardView(ctx)
    await ctx.send(embed=embed, view=view)

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GITHUB_TOKEN or not REPO_NAME:
        print("Error: meaningful environment variables are missing.")
    else:
        bot.run(DISCORD_TOKEN)
