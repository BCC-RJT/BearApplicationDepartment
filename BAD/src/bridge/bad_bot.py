import os
import discord
from github import Github
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')

# Initialize GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Initialize Discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!idea'):
        try:
            # Parse the message content
            content = message.content[len('!idea'):].strip()
            if '|' in content:
                title, body = content.split('|', 1)
                title = title.strip()
                body = body.strip()
            else:
                title = content
                body = "No description provided."

            # Create GitHub Issue
            issue = repo.create_issue(title=title, body=body, labels=["triage"])
            
            # Reply to Discord
            await message.channel.send(f"✅ Issue #{issue.number} Created: {issue.html_url} - ready for Antigravity processing.")
            
        except Exception as e:
            await message.channel.send(f"❌ Error creating issue: {str(e)}")

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GITHUB_TOKEN or not REPO_NAME:
        print("Error: meaningful environment variables are missing.")
    else:
        client.run(DISCORD_TOKEN)
