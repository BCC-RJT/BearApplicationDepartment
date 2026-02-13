
import discord
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('AGENT_CHANNEL_ID')

if not TOKEN or not CHANNEL_ID:
    print("❌ Error: Missing env vars")
    exit(1)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(int(CHANNEL_ID))
    if channel:
        print(f"Sending trigger message to {channel.name}...")
        await channel.send("Wake up, Antigravity!")
        print("✅ Message sent.")
    else:
        print("❌ Channel not found.")
    
    await client.close()

client.run(TOKEN)
