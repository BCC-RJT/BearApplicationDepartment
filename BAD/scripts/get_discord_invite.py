import discord
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    if not client.guilds:
        print("No guilds found.")
        await client.close()
        return

    guild = client.guilds[0]
    print(f"Guild: {guild.name} ({guild.id})")
    
    # Try to find an existing invite
    try:
        invites = await guild.invites()
        if invites:
            print(f"Existing Invite: {invites[0].url}")
            await client.close()
            return
    except Exception as e:
        print(f"Could not fetch invites: {e}")

    # Try to create an invite
    try:
        # Find a suitable channel
        channel = None
        for c in guild.text_channels:
             if c.permissions_for(guild.me).create_instant_invite:
                 channel = c
                 break
        
        if channel:
            invite = await channel.create_invite(max_age=300)
            print(f"Created Invite: {invite.url}")
        else:
             print("No channel found with create_instant_invite permission.")

    except Exception as e:
         print(f"Could not create invite: {e}")
         
    await client.close()

client.run(TOKEN)
