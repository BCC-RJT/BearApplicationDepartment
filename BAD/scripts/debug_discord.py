import discord
import os
import asyncio
from dotenv import load_dotenv

# Load .env
load_dotenv('.env')
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('AGENT_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f'❌ Channel {CHANNEL_ID} not found!')
        await client.close()
        return

    print(f'✅ Channel {channel.name} found.')
    try:
        await channel.send("🔍 DEBUG: I can send messages.")
        print("✅ Message sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print(f"📩 Received message: {message.content} from {message.author}")
    if message.content == "!ping":
        await message.channel.send("Pong!")
        print("✅ Replied to ping.")
        await client.close()

async def main():
    await client.start(TOKEN)

if __name__ == '__main__':
    from discord.ext import commands
    # Just run the client
    try:
        client.run(TOKEN)
    except KeyboardInterrupt:
        pass
