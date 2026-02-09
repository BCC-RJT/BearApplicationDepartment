import discord
import os
import asyncio
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # BAD
REPO_ROOT = os.path.dirname(PROJECT_ROOT) # BearApplicationDepartment
ENV_PATH = os.path.join(REPO_ROOT, '.env')

if not os.path.exists(ENV_PATH):
    print(f"⚠️ .env not found at {ENV_PATH}, trying {PROJECT_ROOT}")
    ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

load_dotenv(ENV_PATH)

TOKEN = os.getenv('DISCORD_TOKEN') # Using BADbot to trigger the command
if not TOKEN:
    print("❌ DISCORD_TOKEN not found.")
    exit(1)

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    # Wait for guilds to be ready
    while not client.guilds:
        print("Waiting for guilds...")
        await asyncio.sleep(1)

    guild = client.guilds[0]
    print(f"Guild: {guild.name}")
    
    # Create a temp channel to test the panel
    channel_name = "ticket-panel-test"
    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        await existing.delete()
    
    channel = await guild.create_text_channel(channel_name)
    print(f"Created {channel.name}")
    
    # Send command (Architect Bot must be running)
    print("Sending ?setup_tickets...")
    await asyncio.sleep(2)
    await channel.send("?setup_tickets")
    
    print("✅ Command sent. Please check the channel to see if the Panel appeared.")
    await client.close()

client.run(TOKEN)
