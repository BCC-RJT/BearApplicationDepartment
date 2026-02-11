
import discord
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
# Try to find .env file by walking up the directory tree or using specific paths
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(repo_root, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

TOKEN = os.getenv('ARCHITECT_TOKEN') or os.getenv('DISCORD_TOKEN')
TARGET_CATEGORY_ID = 1470455385231200337
NEW_NAME = "Tickets Inbox"

if not TOKEN:
    print("Error: TOKEN not found.")
    exit(1)

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    # Find the category
    category = client.get_channel(TARGET_CATEGORY_ID)
    
    if category:
        print(f"Found Category: {category.name} (ID: {category.id})")
        if category.name != NEW_NAME:
            try:
                await category.edit(name=NEW_NAME)
                print(f"✅ Renamed category to '{NEW_NAME}'")
            except Exception as e:
                print(f"❌ Failed to rename: {e}")
        else:
            print(f"ℹ️ Category is already named '{NEW_NAME}'")
    else:
        print(f"❌ Category with ID {TARGET_CATEGORY_ID} not found.")
        # Try finding by name "Manager Inbox" in case ID is wrong (though we confirmed ID)
        for guild in client.guilds:
            cat = discord.utils.get(guild.categories, name="Manager Inbox")
            if cat:
                 print(f"Found 'Manager Inbox' with ID {cat.id}. Renaming...")
                 await cat.edit(name=NEW_NAME)
                 print(f"✅ Renamed category to '{NEW_NAME}'")
            
            cat_emoji = discord.utils.get(guild.categories, name="📨 Manager Inbox")
            if cat_emoji:
                 print(f"Found '📨 Manager Inbox' with ID {cat_emoji.id}. Renaming...")
                 await cat_emoji.edit(name=NEW_NAME)
                 print(f"✅ Renamed category to '{NEW_NAME}'")

    await client.close()

client.run(TOKEN)
