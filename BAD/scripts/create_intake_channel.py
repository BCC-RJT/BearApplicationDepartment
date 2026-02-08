import discord
import os
import asyncio
from dotenv import load_dotenv

# Load env from current directory (assumed repo root)
load_dotenv('.env')

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    # improved logic: find the first guild
    if not client.guilds:
        print("No guilds found.")
        await client.close()
        return

    guild = client.guilds[0]
    print(f"Operating on guild: {guild.name}")
    
    existing = discord.utils.get(guild.text_channels, name="project-intake")
    if existing:
        print(f"Channel #project-intake already exists: {existing.id}")
    else:
        try:
            category = discord.utils.get(guild.categories, name="B.A.D. OPERATIONS")
            if not category:
                category = await guild.create_category("B.A.D. OPERATIONS")
            
            new_channel = await guild.create_text_channel("project-intake", category=category)
            print(f"Created channel: {new_channel.name} ({new_channel.id})")
            await new_channel.send(
                "**🎟️ Project Intake**\n"
                "Please configure the **Ticket Tool** panel in this channel.\n"
                "1. Run the Ticket Tool setup command (e.g. `$setup` or via dashboard).\n"
                "2. When a user opens a ticket, `architect_bot` will automatically join the new channel."
            )
        except Exception as e:
            print(f"Error creating channel: {e}")

    await client.close()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found.")
    else:
        client.run(TOKEN)
