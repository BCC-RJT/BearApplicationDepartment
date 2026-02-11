
import discord
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('ARCHITECT_TOKEN') or os.getenv('DISCORD_TOKEN')
CLOSED_ARCHIVES_ID = int(os.getenv('TICKET_ARCHIVES_ID', '0'))

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    
    category = client.get_channel(CLOSED_ARCHIVES_ID)
    if not category:
        print(f"Category ID {CLOSED_ARCHIVES_ID} not found directly. Searching guilds...")
        for guild in client.guilds:
            cat = discord.utils.get(guild.categories, name="🗄️ Closed Archives")
            if cat:
                category = cat
                print(f"Found category by name in guild: {guild.name}")
                break
    
    if category:
        print(f"Category: {category.name} (ID: {category.id})")
        print(f"Channel Count: {len(category.channels)}")
        if len(category.channels) >= 50:
            print("❌ WARNING: Category is FULL (50 channels).")
        else:
            print("✅ Category is not full.")
    else:
        print("❌ Closed Archives category not found.")
        
    await client.close()

client.run(TOKEN)
