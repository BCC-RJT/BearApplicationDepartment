import discord
import os
import asyncio
from dotenv import load_dotenv

# Load .env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # BAD
REPO_ROOT = os.path.dirname(PROJECT_ROOT) # BearApplicationDepartment
ENV_PATH = os.path.join(REPO_ROOT, '.env')

if not os.path.exists(ENV_PATH):
    print(f"⚠️ .env not found at {ENV_PATH}, trying {PROJECT_ROOT}")
    ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

load_dotenv(ENV_PATH)

# Use ARCHITECT_TOKEN to post as the bot itself
TOKEN = os.getenv('ARCHITECT_TOKEN')
if not TOKEN:
    print("❌ ARCHITECT_TOKEN not found.")
    exit(1)

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True 
client = discord.Client(intents=intents)

TARGET_CHANNEL = "tickets"

# Replicate the View
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass # Logic handled by main bot

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (Deployer)')
    
    # Wait for guilds via fetch 
    try:
        guilds = [g async for g in client.fetch_guilds(limit=1)]
        if not guilds:
             print("❌ No guilds found via fetch.")
             await client.close()
             return
        
        guild_preview = guilds[0]
        print(f"Found Guild: {guild_preview.name} (ID: {guild_preview.id})")
        
        guild = await client.fetch_guild(guild_preview.id)
        channels = await guild.fetch_channels()
        channel = discord.utils.get(channels, name=TARGET_CHANNEL)
        
        if channel and isinstance(channel, discord.TextChannel):
            print(f"✅ Found #{TARGET_CHANNEL} ({channel.id})")
            
            embed = discord.Embed(
                title="📬 Support Tickets",
                description="Click the button below to open a private ticket with the staff.",
                color=discord.Color.blue()
            )
            # Send the panel
            await channel.send(embed=embed, view=TicketView())
            print("✅ Panel Deployed.")
            
        else:
            print(f"❌ Channel #{TARGET_CHANNEL} not found.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    await client.close()

client.run(TOKEN)
