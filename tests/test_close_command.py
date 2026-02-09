import discord
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TEST_BOT_TOKEN = os.getenv('TEST_BOT_TOKEN')
AGENT_CHANNEL_ID = int(os.getenv('AGENT_CHANNEL_ID'))

if not TEST_BOT_TOKEN:
    print("❌ Error: TEST_BOT_TOKEN not found in .env")
    exit(1)

if not AGENT_CHANNEL_ID:
    print("❌ Error: AGENT_CHANNEL_ID not found in .env")
    exit(1)

# Initialize Test Bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'TestBot connected as {client.user}')
    channel = client.get_channel(AGENT_CHANNEL_ID)
    if not channel:
        print(f"❌ Error: Could not find channel {AGENT_CHANNEL_ID}")
        await client.close()
        return

    print("Sending !close command to antigravity-vm...")
    # Send !close with a message to verify argument passing
    await channel.send("!close Automated Test Closing Session")
    print("Command sent successfully.")

@client.event
async def on_message(message):
    # Only listen to the main bot in the agent channel
    if message.author == client.user:
        return
    
    if message.channel.id != AGENT_CHANNEL_ID:
        return

    print(f"Received message from {message.author}: {message.content}")

    # Check for success indicators
    if "Session Closed" in message.content:
        print("✅ PASS: 'Session Closed' message received.")
        await client.close()
    
    # Check for failure
    if "Session Close Failed" in message.content:
        print("❌ FAIL: 'Session Close Failed' message received.")
        await client.close()

async def main():
    async with client:
        await client.start(TEST_BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted.")
