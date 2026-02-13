
import discord
print("DEBUG: Script started...")
import os
import asyncio
from dotenv import load_dotenv
# Load environment variables
# Try to find .env file by walking up the directory tree or using specific paths
current_dir = os.path.dirname(os.path.abspath(__file__))
# Expected location: BearApplicationDepartment/.env (2 levels up from BAD/scripts?)
# valid path: BAD/scripts/list_discord_categories.py
# parent: BAD/scripts
# parent: BAD
# parent: BearApplicationDepartment -> this is where .env is

repo_root = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(repo_root, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from {env_path}")
else:
    # Fallback to default behavior (current dir)
    load_dotenv()
    print("Loaded .env from current directory (or default search).")

TOKEN = os.getenv('TICKET_ASSISTANT_TOKEN') or os.getenv('ARCHITECT_TOKEN') or os.getenv('DISCORD_TOKEN')
token_source = "TICKET_ASSISTANT_TOKEN" if os.getenv('TICKET_ASSISTANT_TOKEN') else ("ARCHITECT_TOKEN" if os.getenv('ARCHITECT_TOKEN') else "DISCORD_TOKEN")
print(f"Using token from: {token_source}")


if not TOKEN:
    print("Error: DISCORD_TOKEN not found in environment variables.")
    exit(1)

# Set up intents
intents = discord.Intents.default()
# We need guilds intent to access guild structure
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    
    if not client.guilds:
        print("No guilds found. Make sure the bot is invited to a server.")
    
    for guild in client.guilds:
        print(f"\nServer: {guild.name} (ID: {guild.id})")
        print("-" * 40)
        
        categories = guild.categories
        
        if not categories:
            print("  No categories found.")
        else:
            # Sort categories by position
            categories.sort(key=lambda x: x.position)
            
            for category in categories:
                print(f"  Category: {category.name}")
                print(f"    ID: {category.id}")
                print(f"    Channels: {len(category.channels)}")
                
    await client.close()

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"Error running bot: {e}")
