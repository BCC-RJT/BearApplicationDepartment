import os
import subprocess
import discord
from discord.ext import commands
from github import Github
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))

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
        if ctx.author.id != ADMIN_USER_ID:
            print(f"⛔ Unauthorized access attempt by {ctx.author.name} ({ctx.author.id})")
            await ctx.send("⛔ Access Denied.")
            return False
        return True
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

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
    await ctx.send("available commands: cleanup")

@bad.command(name='cleanup')
@authorized_only()
async def cleanup(ctx):
    await ctx.send("🧹 Janitor script started... please wait.")
    
    # Run Janitor Script
    try:
        # sudo requires nopasswd entry in sudoers or running bot as root
        result = subprocess.run(
            ["sudo", "/BAD/scripts/janitor.sh"], 
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
            await ctx.send(f"✅ **Cleanup Successful**\n```{output}```")
        else:
            await ctx.send(f"⚠️ **Cleanup Failed** (Exit Code: {result.returncode})\n```{output}```")

    except Exception as e:
        await ctx.send(f"❌ Error running script: {str(e)}")

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GITHUB_TOKEN or not REPO_NAME:
        print("Error: meaningful environment variables are missing.")
    else:
        bot.run(DISCORD_TOKEN)
