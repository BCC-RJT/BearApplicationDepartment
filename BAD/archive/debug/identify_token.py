import discord
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def identify(token_name):
    token = os.getenv(token_name)
    if not token:
        print(f"{token_name}: Not found")
        return

    client = discord.Client(intents=discord.Intents.default())
    
    @client.event
    async def on_ready():
        print(f"Token {token_name} is User: {client.user} (ID: {client.user.id})")
        await client.close()

    try:
        await client.start(token)
    except Exception as e:
        print(f"{token_name}: Error {e}")

async def main():
    await identify('DISCORD_TOKEN')
    await identify('ARCHITECT_TOKEN')
    await identify('TEST_BOT_TOKEN')

if __name__ == "__main__":
    asyncio.run(main())
