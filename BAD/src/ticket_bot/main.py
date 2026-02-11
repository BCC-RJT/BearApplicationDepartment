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

class NewTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Discard Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_bot:discard_new")
    async def discard_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Discarding ticket...", ephemeral=True)
        try:
            # Remove from DB
            interaction.client.db.delete_ticket(interaction.channel.id)
            # Delete channel
            await interaction.channel.delete()
        except Exception as e:
            await interaction.followup.send(f"❌ Error discarding ticket: {e}", ephemeral=True)

class TicketBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
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
        self.add_view(NewTicketView()) # Register discard view

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        try:
            await self.user.edit(username="Ticket Assistant")
        except Exception as e:
            print(f"Failed to update username: {e}")
        await self.ensure_categories()

    async def ensure_categories(self):
        """Ensures that the necessary categories exist in the guild."""
        for guild in self.guilds:
            for key, name in self.categories.items():
                category = discord.utils.get(guild.categories, name=name)
                if not category:
                    try:
                        category = await guild.create_category(name)
                        print(f"Created category: {name}")
                    except Exception as e:
                        print(f"Failed to create category {name}: {e}")
                
                if category:
                    self.category_cache[key] = category

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
        # Send control panel first
        embed = discord.Embed(title="Ticket Controls", description="Use the button below to discard this ticket if created by mistake.", color=discord.Color.red())
        await channel.send(embed=embed, view=NewTicketView())

        # Send greeting
        await channel.send(f"Hello {user.mention}! I'm the **Ticket Assistant**. Please describe your issue briefly.")
        return channel


class TicketProposalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Accept Proposal", style=discord.ButtonStyle.success, custom_id="ticket_bot:accept")
    async def accept_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # 1. Update Status
        interaction.client.db.update_ticket_status(interaction.channel.id, "open")
        
        # 2. Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        # 3. Finalize
        embed = discord.Embed(title="🎫 Official Ticket Created", description="This ticket has been accepted and added to the Manager Inbox.", color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        
        # 4. Notify (Optional) - could ping a role here

    @discord.ui.button(label="✏️ Edit Details", style=discord.ButtonStyle.secondary, custom_id="ticket_bot:edit")
    async def edit_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please type the additional details or corrections below. I will update the proposal.", ephemeral=True)

    @discord.ui.button(label="🗑️ Discard", style=discord.ButtonStyle.danger, custom_id="ticket_bot:discard_prop")
    async def discard_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Discarding ticket...", ephemeral=True)
        try:
            interaction.client.db.delete_ticket(interaction.channel.id)
            await interaction.channel.delete()
        except:
            pass

class TicketBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        # Add guild members intent if needed for permissions, but usually default covers basics
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
        self.add_view(NewTicketView()) # Register discard view
        self.add_view(TicketProposalView()) # Register proposal view

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        try:
            await self.user.edit(username="Ticket Assistant")
        except Exception as e:
            print(f"Failed to update username: {e}")
        await self.ensure_categories()

    async def ensure_categories(self):
        """Ensures that the necessary categories exist in the guild."""
        for guild in self.guilds:
            for key, name in self.categories.items():
                category = discord.utils.get(guild.categories, name=name)
                if not category:
                    try:
                        category = await guild.create_category(name)
                        print(f"Created category: {name}")
                    except Exception as e:
                        print(f"Failed to create category {name}: {e}")
                
                if category:
                    self.category_cache[key] = category

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
        # Send control panel first
        embed = discord.Embed(title="Ticket Controls", description="Use the button below to discard this ticket if created by mistake.", color=discord.Color.red())
        await channel.send(embed=embed, view=NewTicketView())

        # Send greeting
        await channel.send(f"Hello {user.mention}! I'm the **Ticket Assistant**. Please describe your issue briefly.")
        return channel

    async def on_message(self, message):
        # Ignore self
        if message.author == self.user:
            return

        # Check for commands
        await self.process_commands(message)
        
        # If command was processed, we might want to skip AI logic? 
        # But for now, let's assume commands start with prefix and we return inside process_commands? 
        # No, process_commands doesn't return value.
        if message.content.startswith(self.command_prefix):
            return

        # Check if this channel is a ticket in 'setup' mode
        ticket = self.db.get_ticket_by_channel(message.channel.id) # returns tuple or None
        if not ticket:
            return
            
        # ticket schema: ticket_id, channel_id, user_id, user_name, helper_id, status...
        # status is index 5
        status = ticket[5]
        
        if status != 'setup':
            return
            
        # It is a setup ticket. Invoke AI.
        async with message.channel.typing():
            # Build History
            # We want the last N messages to give context.
            history_msgs = [msg async for msg in message.channel.history(limit=20, oldest_first=True)]
            
            history = []
            for msg in history_msgs:
                if msg.content: # Skip empty messages (uploads etc)
                    role = "model" if msg.author == self.user else "user"
                    # Exclude the very last message if it's the one we just received?
                    # logic: 'history' arg in gemini is past turns. 'user_input' is current turn.
                    if msg.id == message.id:
                        continue
                    history.append({"role": role, "parts": [msg.content]})
            
            response_text = await get_ai_response(history, message.content)
            
            # Parse
            is_ready, data, clean_text = parse_ticket_data(response_text)
            
            if is_ready and data:
                # Create Proposal Embed
                embed = discord.Embed(title="Ticket Proposal", description="I have gathered the following details. Please review.", color=discord.Color.blue())
                embed.add_field(name="Issue Type", value=data.get("issue_type", "N/A"), inline=True)
                embed.add_field(name="Priority", value=data.get("priority", "N/A"), inline=True)
                embed.add_field(name="Description", value=data.get("description", "N/A"), inline=False)
                embed.add_field(name="Expected Outcome", value=data.get("expected_outcome", "N/A"), inline=False)
                
                await message.channel.send(content=clean_text, embed=embed, view=TicketProposalView())
            else:
                await message.channel.send(clean_text)

bot = TicketBot()

@bot.command()
async def setup_support(ctx):
    """Posts the persistent 'Open Ticket' message."""
    await ctx.send("To open a support ticket, click the button below:", view=TicketView())

@bot.command()
async def open(ctx):
    """Starts the ticket flow (Testing command)."""
    await bot.create_ticket_channel(ctx.author)

# ... on_message is now in class ...

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
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(TOKEN)
