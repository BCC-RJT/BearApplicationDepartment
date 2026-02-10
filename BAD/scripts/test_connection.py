import discord
import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
if not os.path.exists(ENV_PATH):
    # Try one level up
    ENV_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), '.env')

print(f"Loading .env from: {ENV_PATH}")
load_dotenv(ENV_PATH)

TOKEN = os.getenv('DISCORD_TOKEN')
print(f"Token Loaded: {'Yes' if TOKEN else 'No'}")

class TestClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print(f'Guilds in cache: {len(self.guilds)}')
        async for guild in self.fetch_guilds(limit=5):
            print(f'Fetched Guild: {guild.name} ({guild.id})')
        await self.close()

intents = discord.Intents.default()
# intents.guilds = True # Default behavior
client = TestClient(intents=intents)
client.run(TOKEN)
