
import discord
import os
import asyncio
from dotenv import load_dotenv

# Load env to get credentials
load_dotenv()
TOKEN = os.getenv('TEST_BOT_TOKEN')
CHANNEL_ID = os.getenv('AGENT_CHANNEL_ID')

if not TOKEN or not CHANNEL_ID:
    print("❌ Error: Missing TEST_BOT_TOKEN or AGENT_CHANNEL_ID")
    exit(1)

CHANNEL_ID = int(CHANNEL_ID)

class TestClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_complete = asyncio.Event()

    async def on_ready(self):
        print(f"🧪 Test Bot Logged in as {self.user}")
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Error: Channel not found.")
            await self.close()
            return

        print(f"🚀 Sending test command to {channel.name}...")
        await channel.send("!bad list")

    async def on_message(self, message):
        # Ignore self
        if message.author == self.user:
            return

        # Check for response from target bot (BAD Bridge Bot)
        if message.channel.id == CHANNEL_ID:
            print(f"📥 Received Response from {message.author}: {message.content}")
            if "System Online" in message.content:
                print("✅ SUCCESS: Bot responded with Status.")
            else:
                print("⚠️ Warning: Unexpected response.")
            
            await self.close()

intents = discord.Intents.default()
intents.message_content = True
client = TestClient(intents=intents)

try:
    client.run(TOKEN)
except Exception as e:
    print(f"❌ Execution Error: {e}")
