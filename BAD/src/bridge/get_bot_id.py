import discord
import os
from dotenv import load_dotenv

# Setup
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"BOT_ID:{client.user.id}")
    await client.close()

client.run(TOKEN)
