import discord
import os
import sys
import asyncio

# Setup Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# Basic dotenv manual load since we might not have python-dotenv installed on fresh env, but likely do.
# Actually, let's keep it simple.
from dotenv import load_dotenv
load_dotenv(ENV_PATH)

# Using ARCHITECT_TOKEN (Project Planner) but repurposing as Ticket Assistant
TOKEN = os.getenv('ARCHITECT_TOKEN')

if not TOKEN:
    print("❌ Error: ARCHITECT_TOKEN not found.")
    exit(1)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    
    # Update Nickname to 'Ticket Assistant'
    for guild in client.guilds:
        try:
            if guild.me.nick != "Ticket Assistant":
                print(f"Updating nickname in {guild.name} to 'Ticket Assistant'...")
                await guild.me.edit(nick="Ticket Assistant")
                print("✅ Nickname updated.")
            else:
                print(f"Nickname in {guild.name} is already correct.")
        except Exception as e:
            print(f"⚠️ Failed to update nickname in {guild.name}: {e}")
            
    print("✅ Ticket Assistant Ready and Listening...")
    sys.stdout.flush()

@client.event
async def on_guild_channel_create(channel):
    # Filter for ticket channels
    if isinstance(channel, discord.TextChannel) and channel.name.startswith("ticket-"):
        print(f"🎫 New Ticket Detected: {channel.name} (ID: {channel.id})")
        
        # Wait for permissions to settle / Ticket Tool to do its thing
        await asyncio.sleep(3)
        
        try:
            greeting = (
                "**Ticket Assistant connected.**
"
                "I am here to help. Only one ticket open at a time, please."
            )
            await channel.send(greeting)
            print(f"✅ Greeting sent to {channel.name}")
        except Exception as e:
            print(f"❌ Failed to send greeting to {channel.name}: {e}")
        
        sys.stdout.flush()

if __name__ == "__main__":
    client.run(TOKEN)
