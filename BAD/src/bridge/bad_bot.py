import os
import subprocess
import json
import time
import datetime
import discord
from discord.ext import tasks, commands
from github import Github
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))
JANITOR_CHANNEL_ID = int(os.getenv('JANITOR_CHANNEL_ID', '0'))
AUTHORIZED_ROLE = "BAD_Officer"

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HEARTBEAT_FILE = os.path.join(PROJECT_ROOT, 'logs', 'heartbeat.json')
LEDGER_FILE = os.path.join(PROJECT_ROOT, 'config', 'resource_ledger.json')

# Initialize GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Initialize Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

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

async def run_janitor_script():
    """Helper function to run the janitor script and return output."""
    try:
        # Script path
        script_path = "/home/headsprung/BAD/scripts/janitor.sh"
        
        result = subprocess.run(
            ["sudo", script_path], 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nstderr:\n{result.stderr}"
        
        # Truncate if too long (limit is 2000 chars)
        if len(output) > 1900:
            output = output[:1900] + "\n...(truncated)"

        if result.returncode == 0:
            return f"✅ **Cleanup Successful**\n```{output}```"
        else:
            return f"⚠️ **Cleanup Failed** (Exit Code: {result.returncode})\n```{output}```"

    except Exception as e:
        return f"❌ Error running script: {str(e)}"

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    # Start the scheduled tasks
    if not scheduled_janitor.is_running():
        scheduled_janitor.start()
    if not heartbeat_task.is_running():
        heartbeat_task.start()

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
    if JANITOR_CHANNEL_ID == 0:
        print("Warning: JANITOR_CHANNEL_ID not set. Skipping scheduled cleanup.")
        return

    channel = bot.get_channel(JANITOR_CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel with ID {JANITOR_CHANNEL_ID}")
        return

    print("⏰ Starting scheduled janitor sweep...")
    await channel.send("⏰ **Daily Janitor Cycle Initiated**...")
    
    report = await run_janitor_script()
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
    await ctx.send("available commands: cleanup, status, cost")

@bad.command(name='cleanup')
@authorized_only()
async def cleanup(ctx):
    await ctx.send("🧹 Janitor script started... please wait.")
    report = await run_janitor_script()
    await ctx.send(report)

# --- BAD Integration ---
import sys
# Add parent directory to path to import db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

# --- End BAD Integration ---

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GITHUB_TOKEN or not REPO_NAME:
        print("Error: meaningful environment variables are missing.")
    else:
        bot.run(DISCORD_TOKEN)
