
import discord
import os
import asyncio
import logging
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO)

# Load existing env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ENV_FILE = ".env"

if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found in .env")
    exit(1)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    try:
        print(f"Logged in as {client.user}")
        
        if not client.guilds:
            print("❌ Bot is not in any guilds.")
            await client.close()
            return
    
        guild = client.guilds[0]
        print(f"Target Guild: {guild.name} ({guild.id})")
    
        # 1. Create Category
        category_name = "B.A.D. OPERATIONS"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            print(f"Creating category: {category_name}...")
            category = await guild.create_category(category_name)
        
        # 2. Create Channel
        channel_name = "antigravity-vm"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
        
        channel_id = None
        if existing_channel:
            print(f"✅ Channel '{channel_name}' already exists: ID {existing_channel.id}")
            channel_id = existing_channel.id
            channel = existing_channel
        else:
            print(f"Creating channel: {channel_name}...")
            # Permissions: Private to Bot (and server owner/admin by default)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            new_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
            print(f"✅ Channel created: {new_channel.id}")
            channel_id = new_channel.id
            channel = new_channel
    
        # 3. Update .env
        if channel_id:
            update_env_file(channel_id)
    
        # 4. Send Initial Message
        print(f"Sending initial message to {channel.name}...")
        await channel.send("Hello Antigravity. Are you there?")
        print("✅ Message sent.")
        
    except Exception as e:
        print(f"❌ Error in on_ready: {e}")
        import traceback
        traceback.print_exc()

    await client.close()

def update_env_file(channel_id):
    # Read current lines
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()

    # Check if key exists
    key = "AGENT_CHANNEL_ID"
    new_line = f"{key}={channel_id}\n"
    key_found = False

    with open(ENV_FILE, "w") as f:
        for line in lines:
            if line.startswith(key + "="):
                f.write(new_line)
                key_found = True
            else:
                f.write(line)
        
        if not key_found:
            # Ensure newline before appending if needed
            if lines and not lines[-1].endswith("\n"):
                f.write("\n")
            f.write(new_line)
    
    print(f"✅ Updated {ENV_FILE} with {key}={channel_id}")

client.run(TOKEN)
