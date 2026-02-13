import discord
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1470492715878973573

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    try:
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            print(f"Could not find channel with ID {CHANNEL_ID}")
            # Try fetching it if it's not in cache
            try:
                channel = await client.fetch_channel(CHANNEL_ID)
                print(f"Fetched channel: {channel.name}")
            except Exception as e:
                print(f"Failed to fetch channel: {e}")
                await client.close()
                return

        print(f"Accessing channel: {channel.name}")
        
        print("--- Message History ---")
        async for message in channel.history(limit=50):
            print(f"[{message.created_at}] {message.author}: {message.content}")
            if message.embeds:
                print(f"  [Embed]: {message.embeds[0].title} - {message.embeds[0].description}")
        print("-----------------------")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables.")
    else:
        client.run(TOKEN)
