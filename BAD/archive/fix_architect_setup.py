import discord
import os
from dotenv import load_dotenv
import asyncio

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')

load_dotenv(ENV_PATH)

# Use the Architect Token to get its own ID for the invite link
TOKEN = os.getenv('ARCHITECT_TOKEN')
ARCHITECT_CHANNEL_ID = int(os.getenv('PLANNING_CHANNEL_ID', '0'))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    
    # 1. Rename Channel
    try:
        channel = client.get_channel(ARCHITECT_CHANNEL_ID)
        if channel:
            await channel.edit(name="pre-project-planning")
            print(f"✅ Renamed channel to #pre-project-planning")
        else:
            print(f"⚠️ Could not find channel {ARCHITECT_CHANNEL_ID} to rename.")
    except Exception as e:
        print(f"❌ Error renaming channel: {e}")

    # 2. Generate Invite Link
    # Scopes: bot
    # Permissions: Read Messages, Send Messages, Embed Links, Attach Files, Read Message History
    # Integer: 3072 (View Channels + Send Messages) + 32768 (Attach Files) + 65536 (Read History) = 99392?
    # Safer to just use standard text permissions: 68608
    # (View Channels, Send Messages, Read Message History)
    
    app_info = await client.application_info()
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={app_info.id}&permissions=68608&scope=bot"
    
    print(f"\n🔗 **INVITE LINK**: {invite_url}\n")
    
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
