import discord
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TEST_BOT_TOKEN = os.getenv('TEST_BOT_TOKEN')
AGENT_CHANNEL_ID = int(os.getenv('AGENT_CHANNEL_ID'))

if not TEST_BOT_TOKEN or not AGENT_CHANNEL_ID:
    print("❌ Error: Missing credentials in .env")
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

    print("Sending natural language message to antigravity-vm...")
    await channel.send("I want to fix the login bug.")
    print("Message sent.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.channel.id != AGENT_CHANNEL_ID:
        return

    print(f"Received message from {message.author}: {message.content}")

    # Check for expected guidance
    lower_content = message.content.lower()
    if "session" in lower_content and ("open" in lower_content or "kickoff" in lower_content):
        print("✅ PASS: Bot suggested opening/kickoff session.")
        await client.close()
    
    # Fail safe timeout handled by script runner usually, but we can exit if we see a wrong response?
    # For now, just print and wait for the right one.

async def main():
    async with client:
        await client.start(TEST_BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted.")
