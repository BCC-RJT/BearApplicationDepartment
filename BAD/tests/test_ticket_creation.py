import discord
import asyncio
import os
from dotenv import load_dotenv

# Load env same as bot
current_dir = os.path.dirname(os.path.abspath(__file__)) # BAD/tests
project_root = os.path.dirname(current_dir) # BAD
repo_root = os.path.dirname(project_root) # BearApplicationDepartment
env_path = os.path.join(repo_root, '.env')

if not os.path.exists(env_path):
    print(f"⚠️ .env not found at {env_path}, trying {project_root}")
    env_path = os.path.join(project_root, '.env')

load_dotenv(env_path)

# Use DISCORD_TOKEN (BADbot) for the tester client to observe ArchitectBot
# This prevents token conflict since we will run ArchitectBot as the main process
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ DISCORD_TOKEN not found.")
    exit(1)

MANAGER_INBOX_ID = 1470455385231200337

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (Observer/Tester)')
    guild = client.guilds[0] # Assume first guild
    print(f"Testing in Guild: {guild.name}")

    # 1. Create Ticket
    print("Creating test ticket channel...")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    # Create in a random category or None first
    try:
        channel = await guild.create_text_channel("ticket-auto-test", overwrites=overwrites)
        print(f"Created {channel.name} (ID: {channel.id})")
    except Exception as e:
        print(f"❌ Failed to create channel: {e}")
        await client.close()
        return
    
    # 2. Wait for Bot to move it
    print("Waiting 10s for workflow to trigger...")
    await asyncio.sleep(10)
    
    # 3. Check Category
    try:
        # Re-fetch channel to get updated cache
        # Note: In discord.py, guild.get_channel gets from cache. 
        # We might need to fetch_channel to hit validation.
        channel = await client.fetch_channel(channel.id)

        if channel.category and channel.category.id == MANAGER_INBOX_ID:
            print("✅ SUCCESS: Channel moved to Manager Inbox.")
        else:
            cat_name = channel.category.name if channel.category else "None"
            cat_id = channel.category.id if channel.category else "None"
            print(f"❌ FAILURE: Channel is in '{cat_name}' ({cat_id}), expected Manager Inbox ({MANAGER_INBOX_ID}).")
            if cat_id == "None":
                 print("   (Bot might not be running or failed to move)")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
    
    # 4. Cleanup
    print("Cleaning up...")
    try:
        await channel.delete()
        print("Channel deleted.")
    except:
        print("Failed to delete channel (already deleted?)")

    print("Test Complete.")
    await client.close()

client.run(TOKEN)
