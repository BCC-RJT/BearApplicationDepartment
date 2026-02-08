import discord
import os
from dotenv import load_dotenv
import asyncio

# Setup Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')

load_dotenv(ENV_PATH)

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', '0')) # Optional, or find first

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    
    # Find Guild
    guild = None
    if GUILD_ID:
        guild = client.get_guild(GUILD_ID)
    
    if not guild:
        # Default to the first guild
        if client.guilds:
            guild = client.guilds[0]
        else:
            print("❌ No guilds found.")
            await client.close()
            return

    print(f"Operating in Guild: {guild.name}")

    # Create Category
    category_name = "B.A.D. OPERATIONS"
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        print(f"Creating Category: {category_name}")
        category = await guild.create_category(category_name)
    
    # Create Channel
    channel_name = "mission-control"
    channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
    
    if not channel:
        print(f"Creating Channel: {channel_name}")
        # Permissions: Private
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
            # Cannot add user explicitly easily without ID, but Admin usually has access
        }
        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        print(f"✅ Channel Created.")
    else:
        print(f"⚠️ Channel already exists.")
    
    print(f"CHANNEL_ID: {channel.id}")
    
    await client.close()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found.")
    else:
        client.run(TOKEN)
