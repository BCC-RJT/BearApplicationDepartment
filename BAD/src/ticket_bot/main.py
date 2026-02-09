from drive_service import DriveService

import discord
from discord.ext import commands
import os
import datetime
from dotenv import load_dotenv
import asyncio
from database import DatabaseManager
from ai_handler import get_ai_response, parse_ticket_data

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="ticket_bot:open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # We need to call the bot's create_ticket_channel logic. 
        # Since this is a View, we can access the bot via interaction.client if it's the bot instance, 
        # or we need to pass the bot to the view. interaction.client is the bot.
        
        await interaction.response.defer(ephemeral=True)
        # Check if user already has a ticket? (Optional)
        
        # Create channel
        bot = interaction.client
        channel = await bot.create_ticket_channel(interaction.user)
        
        await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)

class TicketBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.db = DatabaseManager()
        self.categories = {
            "manager": "📨 Manager Inbox",
            "active": "⚡ Active Tickets",
            "blocked": "⛔ Blocked / Escalated",
            "closed": "🗄️ Closed Archives"
        }
        self.category_cache = {}

    async def setup_hook(self):
        print("Bot is starting up...")
        self.add_view(TicketView()) # Register persistent view

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.ensure_categories()

    # ... ensure_categories ...

    async def create_ticket_channel(self, user):
        """Creates a private channel for the user to start the interview."""
        guild = user.guild
        category = self.category_cache.get("manager") # Fallback
        
        # Permissions: User can see, Everyone else cannot
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel_name = f"ticket-{user.name[:10]}"
        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        
        # Register in DB
        self.db.create_ticket(channel.id, channel.id, user.id, user.name)
        
        # Send greeting
        await channel.send(f"Hello {user.mention}! I'm the Support Bot. Please describe your issue briefly.")
        return channel

bot = TicketBot()

@bot.command()
async def setup_support(ctx):
    """Posts the persistent 'Open Ticket' message."""
    await ctx.send("To open a support ticket, click the button below:", view=TicketView())

@bot.command()
async def open(ctx):
    """Starts the ticket flow (Testing command)."""
    await bot.create_ticket_channel(ctx.author)

# ... on_message ...

# ... assign, add, block ...

@bot.command()
async def close(ctx, *, note: str = "No closing note provided."):
    """Closes the ticket and archives it."""
    
    # Generate Transcript
    messages = [message async for message in ctx.channel.history(limit=500, oldest_first=True)]
    transcript = f"Transcript for {ctx.channel.name}\nClosing Note: {note}\nDate: {datetime.date.today()}\n\n"
    
    attachment_urls = []
    
    for msg in messages:
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        transcript += f"[{timestamp}] {msg.author.name}: {msg.content}\n"
        if msg.attachments:
            for att in msg.attachments:
                transcript += f"  [ATTACHMENT]: {att.url}\n"
                attachment_urls.append(att.url) # Todo: Download locally if needed for full archive
    
    # Upload to Drive
    drive_service = DriveService(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
    ticket = bot.db.get_ticket_by_channel(ctx.channel.id)
    
    drive_link = "Drive Upload Failed or Skipped"
    if ticket:
        ticket_id = ticket[0] # channel_id as ticket_id for now
        user_name = ticket[3]
        
        # We need to download attachments to upload them? 
        # DriveService.upload_ticket_folder expects paths. 
        # For MVP, let's just upload transcript. Attachments require downloading.
        
        # Simple local download for attachments (if any)
        # Skipping attachment download for speed in MVP, just logging URLs in transcript.
        
        result = drive_service.upload_ticket_folder(ticket_id, user_name, transcript)
        if result:
             drive_link = result
    
    # Move to Closed Archives
    category = bot.category_cache.get("closed")
    if category:
        await ctx.channel.edit(category=category, sync_permissions=True) 
    
    # Set Read-Only
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    if ticket:
        user_id = ticket[2]
        member = ctx.guild.get_member(user_id)
        if member:
            await ctx.channel.set_permissions(member, send_messages=False, read_messages=True)

    bot.db.close_ticket(ctx.channel.id)
    await ctx.send(f"🗄️ Ticket Closed.\nNote: {note}\nArchive: {drive_link}")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(TOKEN)
