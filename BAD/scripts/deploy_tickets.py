import discord
import os
import asyncio
from dotenv import load_dotenv

# Load .env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # BAD
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

if not os.path.exists(ENV_PATH):
    # Try one level up
    ENV_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), '.env')
    print(f"⚠️ .env not found in BAD, trying {ENV_PATH}")

load_dotenv(ENV_PATH)

TOKEN = os.getenv('ARCHITECT_TOKEN') or os.getenv('DISCORD_TOKEN') # Try Architect (Assistant) first
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
    
    # Wait for cache
    await asyncio.sleep(3)
    
    # Try using cache first
    guilds = client.guilds
    if not guilds:
        print("⚠️ Cache empty, trying fetch...")
        try:
             guilds = [g async for g in client.fetch_guilds(limit=1)]
        except Exception as e:
             print(f"❌ Guild fetch failed: {e}")
             await client.close()
             return

    if not guilds:
         print("❌ No guilds found via cache or fetch.")
         await client.close()
         return
    
    guild_preview = guilds[0]
    print(f"Found Guild: {guild_preview.name} (ID: {guild_preview.id})")
    
    try:
        # Fetch full guild object to access channels
        guild = await client.fetch_guild(guild_preview.id) # Use preview ID

        # Find #tickets channel
        channels = await guild.fetch_channels()
        channel = discord.utils.get(channels, name=TARGET_CHANNEL)
        
        if channel:
            print(f"✅ Found #{TARGET_CHANNEL} ({channel.id})")
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
