import discord
import asyncio
import os
from dotenv import load_dotenv

# Setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Try to find the actual repo root
candidate_root = os.path.dirname(PROJECT_ROOT) # Default parent
if os.path.isdir(os.path.join(candidate_root, ".git")):
    REPO_ROOT = candidate_root
elif os.path.isdir(os.path.join(candidate_root, "BearApplicationDepartment")):
    REPO_ROOT = os.path.join(candidate_root, "BearApplicationDepartment")
else:
    REPO_ROOT = PROJECT_ROOT

ENV_PATH = os.path.join(REPO_ROOT, '.env')
if not os.path.exists(ENV_PATH):
     ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
     
print(f"Loading .env from: {ENV_PATH}")
load_dotenv(ENV_PATH)

TOKEN = os.getenv('TICKET_ASSISTANT_TOKEN') or os.getenv('ARCHITECT_TOKEN') or os.getenv('DISCORD_TOKEN')
GUILD_ID = None # Optional: Set if bot is in multiple guilds, otherwise it picks the first one

if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found in environment.")
    exit(1)

intents = discord.Intents.default()
# intents.guilds = True # Default includes guilds

client = discord.Client(intents=intents)

TARGET_CATEGORY = "B.A.D. OPERATIONS"
TARGET_CHANNEL = "antigravity-net"
WEBHOOK_NAME = "Antigravity Uplink"

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    
    # 1. Select Guild
    guild = client.guilds[0]
    print(f"Targeting Guild: {guild.name} ({guild.id})")

    # 2. Find/Create Category
    category = discord.utils.get(guild.categories, name=TARGET_CATEGORY)
    if not category:
        print(f"Creating Category: {TARGET_CATEGORY}...")
        category = await guild.create_category(TARGET_CATEGORY)
    else:
        print(f"Category '{TARGET_CATEGORY}' exists.")

    # 3. Find/Create Channel
    channel = discord.utils.get(guild.text_channels, name=TARGET_CHANNEL, category=category)
    if not channel:
        print(f"Creating Channel: {TARGET_CHANNEL}...")
        # Permissions: Default (Visible to everyone or restrict as needed)
        # For now, let's keep it visible so users can see the cross-talk
        channel = await guild.create_text_channel(TARGET_CHANNEL, category=category)
        print(f"✅ Channel Created: {channel.mention} (ID: {channel.id})")
        print(f"👉 ACTION: Add ANTIGRAVITY_CHANNEL_ID={channel.id} to your .env")
    else:
        print(f"Channel '{TARGET_CHANNEL}' exists (ID: {channel.id}).")

    # 4. Find/Create Webhook
    webhooks = await channel.webhooks()
    webhook = discord.utils.get(webhooks, name=WEBHOOK_NAME)
    
    if not webhook:
        print(f"Creating Webhook: {WEBHOOK_NAME}...")
        webhook = await channel.create_webhook(name=WEBHOOK_NAME)
        print("✅ Webhook Created!")
    else:
        print(f"Webhook '{WEBHOOK_NAME}' exists.")

    print("\n--- CONFIGURATION DETAILS ---")
    print(f"Channel ID: {channel.id}")
    print(f"Webhook URL: {webhook.url}")
    print("-----------------------------")
    print(f"👉 ACTION: Add ANTIGRAVITY_WEBHOOK_URL={webhook.url} to your .env in ALL environments.")

    await client.close()

try:
    client.run(TOKEN)
except Exception as e:
    print(f"❌ Error running client: {e}")
