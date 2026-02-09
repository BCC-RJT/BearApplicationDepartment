import os
import discord
import asyncio
from dotenv import load_dotenv

# Load environment variables (mostly for channel ID)
load_dotenv('.env')

AGENT_CHANNEL_ID = int(os.getenv('AGENT_CHANNEL_ID'))
TEST_BOT_TOKEN = os.getenv('TEST_BOT_TOKEN') # Using the token from metadata/env

class TestClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.test_completed = False

    async def on_ready(self):
        print(f'TestBot connected as {self.user}')
        channel = self.get_channel(AGENT_CHANNEL_ID)
        if not channel:
            print(f"Error: Could not find channel {AGENT_CHANNEL_ID}")
            await self.close()
            return
        
        print(f"Sending !open command to {channel.name}...")
        try:
            await channel.send("!open")
            print("Command sent successfully.")
        except Exception as e:
            print(f"Failed to send command: {e}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(f"Received message from {message.author}: {message.content}")

        if "!open" in message.content:
            # Ignore our own echo if any
            return

        if "Session Ready" in message.content:
            print("✅ PASS: 'Session Ready' message received.")
            self.test_completed = True
            await self.close()
        
        if "Session Start Failed" in message.content:
            print("❌ FAIL: Session start failed reported by bot.")
            self.test_completed = True
            await self.close()

async def main():
    if not TEST_BOT_TOKEN:
        print("Error: TEST_BOT_TOKEN not set.")
        return

    client = TestClient()
    try:
        await client.start(TEST_BOT_TOKEN)
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
