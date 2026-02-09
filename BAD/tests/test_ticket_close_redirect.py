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

# IDs
MANAGER_INBOX_ID = 1470455385231200337
TICKET_TOOL_CLOSED_ID = 1470169997841006602
CLOSED_ARCHIVES_ID = 1470455388317941871

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (Observer/Tester)')
    guild = client.guilds[0]
    print(f"Testing in Guild: {guild.name}")

    # 1. Create Ticket
    print("Creating test ticket channel...")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    try:
        channel = await guild.create_text_channel("ticket-close-test", overwrites=overwrites)
        print(f"Created {channel.name} (ID: {channel.id})")
        
        # Wait for initial move to Inbox
        await asyncio.sleep(5)
        
        # 2. Simulate User/Bot closing ticket (Move to Ticket Tool Closed Category)
        print(f"Simulating 'Ticket Tool' close (Moving to {TICKET_TOOL_CLOSED_ID})...")
        closed_category = guild.get_channel(TICKET_TOOL_CLOSED_ID)
        if not closed_category:
             print("❌ Could not find Ticket Tool Closed Category")
             return

        await channel.edit(category=closed_category)
        print("Moved to Closed Tickets.")
        
        # 3. Wait for BADbot to Redirect
        print("Waiting 5s for BADbot to redirect...")
        await asyncio.sleep(5)
        
        # 4. Verify Final Location
        channel = await client.fetch_channel(channel.id)
        if channel.category and channel.category.id == CLOSED_ARCHIVES_ID:
            print("✅ SUCCESS: Channel redirected to Closed Archives.")
        else:
             cat_name = channel.category.name if channel.category else "None"
             print(f"❌ FAILURE: Channel is in {cat_name} ({channel.category.id if channel.category else 'None'}), expected Closed Archives.")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
    
    # 5. Cleanup
    print("Cleaning up...")
    try:
        await channel.delete()
    except:
        pass

    print("Test Complete.")
    await client.close()

client.run(TOKEN)
