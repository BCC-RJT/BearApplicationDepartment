import discord
import os
import asyncio
from dotenv import load_dotenv

load_dotenv('../.env')
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    guild = client.guilds[0]
    channel = discord.utils.get(guild.text_channels, name="project-intake")
    
    if channel:
        messages = [msg async for msg in channel.history(limit=5)]
        if messages:
            print(f"FOUND_MESSAGES: {len(messages)}")
            for m in messages:
                print(f" - {m.author.name}: {m.content} (Embeds: {len(m.embeds)})")
        else:
            print("NO_MESSAGES")
    else:
        print("CHANNEL_NOT_FOUND")

    await client.close()

client.run(TOKEN)
