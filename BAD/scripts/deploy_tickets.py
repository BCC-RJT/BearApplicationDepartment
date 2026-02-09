import discord
import os
import asyncio
from dotenv import load_dotenv

# Load .env
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
intents.guilds = True # Required to find channels
client = discord.Client(intents=intents)

TARGET_CHANNEL = "tickets"

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    # Wait for guilds via fetch to bypass cache issues
    try:
        guilds = [g async for g in client.fetch_guilds(limit=1)]
        if not guilds:
             print("❌ No guilds found via fetch.")
             await client.close()
             return
        
        guild_preview = guilds[0]
        print(f"Found Guild: {guild_preview.name} (ID: {guild_preview.id})")
        
        # Fetch full guild object to access channels
        guild = await client.fetch_guild(guild_preview.id)
        
        # Find #tickets channel
        # fetch_guild returns a Guild object, but channels might not be cached?
        # Use fetch_channels()
        channels = await guild.fetch_channels()
        channel = discord.utils.get(channels, name=TARGET_CHANNEL)
        
        if channel:
            print(f"✅ Found #{TARGET_CHANNEL} ({channel.id})")
            # To send message, we need a TextChannel object. fetch_channels returns GuildChannel
            # which is fine.
            if isinstance(channel, discord.TextChannel):
                 print("Sending ?setup_tickets...")
                 await channel.send("?setup_tickets")
                 print("✅ Command sent.")
            else:
                 print(f"❌ #{TARGET_CHANNEL} is not a text channel.")
        else:
            print(f"❌ Channel #{TARGET_CHANNEL} not found online.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    await client.close()

client.run(TOKEN)
