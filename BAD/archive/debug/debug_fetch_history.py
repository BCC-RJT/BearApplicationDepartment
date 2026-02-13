import discord
import os
import asyncio
from dotenv import load_dotenv

# Load env from current directory (BAD/.env)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1470492715878973573 # #antigravity-net from HANDOVER

if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found in .env")
    exit(1)

config = discord.Intents.default()
config.message_content = True
client = discord.Client(intents=config)

@client.event
async def on_ready():
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Logged in as {client.user}\n")
        f.write("--- Visible Channels ---\n")
        
        found = False
        for guild in client.guilds:
            f.write(f"Guild: {guild.name} ({guild.id})\n")
            for channel in guild.text_channels:
                f.write(f" - #{channel.name} ({channel.id})\n")
                if channel.id == CHANNEL_ID:
                    found = True
        f.write("------------------------\n")

        if not found:
            f.write(f"❌ TARGET CHANNEL {CHANNEL_ID} NOT FOUND IN CACHE.\n")
        else:
            try:
                channel = client.get_channel(CHANNEL_ID)
                f.write(f"--- History for #{channel.name} ---\n")
                async for msg in channel.history(limit=10):
                    f.write(f"[{msg.created_at.strftime('%H:%M')}] {msg.author.name}: {msg.content}\n")
                    if msg.embeds:
                        f.write(f"  [Embed]: {msg.embeds[0].title} - {msg.embeds[0].description}\n")
                f.write("-----------------------------------\n")
            except Exception as e:
                f.write(f"❌ Error fetching history: {e}\n")
    
    await client.close()

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"❌ Client Error: {e}")
