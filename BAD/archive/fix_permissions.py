import discord
import os
from dotenv import load_dotenv
import asyncio

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')

load_dotenv(ENV_PATH)

# Use BAD_BOT Token (Admin)
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('PLANNING_CHANNEL_ID', '0'))
ARCHITECT_ID = 1470100217679577099 # From OAuth URL
ADMIN_ID = int(os.getenv('DISCORD_ALLOWED_USER_ID', '0'))

intents = discord.Intents.default()
# intents.members = True # Removed to avoid privilege error
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    
    try:
        channel = await client.fetch_channel(CHANNEL_ID)
    except Exception as e:
        print(f"❌ Could not find channel {CHANNEL_ID}: {e}")
        await client.close()
        return

    print(f"Found Channel: {channel.name}")
    
    # 1. Rename if needed
    if channel.name != "pre-project-planning":
        print(f"Renaming to #pre-project-planning...")
        await channel.edit(name="pre-project-planning")
    
    guild = channel.guild

    # 2. Add Architect
    try:
        architect = await guild.fetch_member(ARCHITECT_ID)
        print(f"Adding Architect ({architect.name}) to channel...")
        await channel.set_permissions(architect, read_messages=True, send_messages=True, attach_files=True)
    except Exception as e:
        print(f"⚠️ Architect (ID {ARCHITECT_ID}) not found or error: {e}")

    # 3. Add Admin
    if ADMIN_ID:
        try:
            admin = await guild.fetch_member(ADMIN_ID)
            print(f"Adding Admin ({admin.name}) to channel...")
            await channel.set_permissions(admin, read_messages=True, send_messages=True)
        except Exception as e:
             print(f"⚠️ Admin (ID {ADMIN_ID}) not found or error: {e}")

    print("✅ Permissions Updated.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
