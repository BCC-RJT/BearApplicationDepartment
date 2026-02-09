import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import asyncio
import json
import sys
import os
from collections import deque

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')
load_dotenv(ENV_PATH)

# Bot Identity
BOT_NAME = "Tickets Assistant"
TOKEN = os.getenv('ARCHITECT_TOKEN') or os.getenv('DISCORD_TOKEN')

# Server Identification (for Multi-Server Archiving)
SERVER_ID_FLAG = os.getenv('SERVER_ID', 'BAD-MAIN') # Default to BAD-MAIN if not set

# Ticket Categories (Fallbacks for BAD)
MANAGER_INBOX_ID = int(os.getenv('TICKET_MANAGER_INBOX_ID', '0'))
INCOMING_TICKETS_ID = int(os.getenv('TICKET_INCOMING_ID', '0')) 
ACTIVE_TICKETS_ID = int(os.getenv('TICKET_ACTIVE_ID', '0'))
BLOCKED_ESCALATED_ID = int(os.getenv('TICKET_BLOCKED_ID', '0'))
CLOSED_ARCHIVES_ID = int(os.getenv('TICKET_ARCHIVES_ID', '0'))

# Configuration
PLANNING_CHANNEL_ID = int(os.getenv('PLANNING_CHANNEL_ID', '0'))

# Initialize Discord
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True 
# intents.members = True # Disabled to prevent crash if not enabled in Portal

bot = commands.Bot(command_prefix='?', intents=intents)

# --- Agent Integration ---
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from src.agent.brain import AgentBrain
    from src.agent.conversation_manager import ConversationManager
    brain = AgentBrain()
    conversation_manager = ConversationManager()
    print("🧠 Agent Brain & Conversation Manager Intergrated")
except ImportError as e:
    print(f"⚠️ Warning: Agent components import failed: {e}")
    brain = None
    conversation_manager = None

# --- Views ---

class InterviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Submit Ticket", style=discord.ButtonStyle.green, custom_id="confirm_ticket_btn")
    async def confirm_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        channel = interaction.channel
        guild = interaction.guild
        
        # 1. Move to Manager Inbox
        # Dynamic fetch or fallback
        category = guild.get_channel(MANAGER_INBOX_ID)
        if not category:
             category = discord.utils.get(guild.categories, name="Manager Inbox")
        
        if category:
            await channel.edit(category=category)
        else:
            await channel.send("⚠️ Manager Inbox not found. Leaving channel here.")

        # 2. Rename (remove 'incoming-')
        if channel.name.startswith("incoming-"):
            new_name = channel.name.replace("incoming-", "ticket-")
            await channel.edit(name=new_name)

        # 3. Ping Staff
        # (Ideally fetch role ID from env, hardcoding/searching for now)
        staff_role = discord.utils.get(guild.roles, name="Staff") or discord.utils.get(guild.roles, name="Manager")
        mention = staff_role.mention if staff_role else "@here"
        
        await channel.send(f"📨 **Ticket Submitted!** {mention} A new ticket is ready for review.")
        
        # 4. Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
    @discord.ui.button(label="🚫 Cancel", style=discord.ButtonStyle.red, custom_id="cancel_ticket_btn")
    async def cancel_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Deleting ticket...", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Notify user immediately (ephemeral)
        await interaction.response.send_message("Creating your ticket, please wait...", ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        
        # Create Private Channel
        # We want the ticket to be at the very top of the server, so we use no category and position=0
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        try:
            channel_name = f"incoming-{user.name}"
            channel = await guild.create_text_channel(channel_name, category=None, position=0, overwrites=overwrites)
            
            # Send Interview Message
            embed = discord.Embed(
                title="📝 Ticket Interview",
                description=(
                    f"Hello {user.mention}!\n\n"
                    "I am the **Ticket Assistant**. Please describe your issue below, and I will help you get it sorted.\n\n"
                    "When you are ready for staff to review, click **Submit Ticket**."
                ),
                color=discord.Color.gold()
            )
            await channel.send(content=f"{user.mention}", embed=embed, view=InterviewView())
            
            # Start Conversation
            if conversation_manager:
                conversation_manager.start_new_conversation(channel.id)
                conversation_manager.add_bot_message(channel.id, "Hello! I am your Ticket Assistant. How can I help you today?")
            
            # Delete the "Thinking..." / "Creating..." message so it doesn't linger
            try:
                await interaction.delete_original_response()
            except discord.NotFound:
                pass # Already deleted
                
            print(f"🎫 [Ticket] Created incoming ticket for {user.name} ({channel.id})")

        except Exception as e:
            # If fail, try to edit the ephemeral message to show error
            try:
                await interaction.edit_original_response(content=f"❌ Failed to create ticket: {e}")
            except:
                pass
            print(f"❌ [Ticket] Creation failed: {e}")

# --- Background Tasks ---

@tasks.loop(minutes=5)
async def check_ticket_panel():
    """Periodically checks if the Ticket Panel is present in #tickets."""
    print("🔎 Checking Ticket Panel status...")
    await bot.wait_until_ready()
    await asyncio.sleep(5) # Allow cache to populate
    
    # Try using cache first
    guilds_to_check = bot.guilds
    print(f"DEBUG: Found {len(guilds_to_check)} guilds in cache.")
    if not guilds_to_check:
        try:
             guilds_to_check = []
             async for g in bot.fetch_guilds(limit=5):
                 guilds_to_check.append(g)
        except: pass

    if not guilds_to_check:
        print("❌ No guilds found.")
        return

    for guild_ref in guilds_to_check:
        try:
            guild = await bot.fetch_guild(guild_ref.id)
            await process_guild_tickets(guild)
        except Exception as e:
            print(f"   ❌ Failed to process guild {guild_ref.id}: {e}")

async def process_guild_tickets(guild):
    # Ensure channels are cached or fetched
    try:
        channels = await guild.fetch_channels()
        channel = discord.utils.get(channels, name="tickets")
    except: return

    if channel and isinstance(channel, discord.TextChannel):
        try:
            panel_exists = False
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "📬 Support Tickets":
                    panel_exists = True
                    break
            
            if not panel_exists:
                print(f"📦 Auto-Deploying Ticket Panel to #{channel.name} in {guild.name}")
                embed = discord.Embed(
                    title="📬 Support Tickets",
                    description="Click the button below to open a private ticket with the staff.",
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed, view=TicketView())
        except Exception as e:
            print(f"⚠️ Failed to auto-deploy panel: {e}")

# --- Commands ---

@bot.group(name='ticket', invoke_without_command=True)
async def ticket_cmd(ctx):
    """Ticket workflow commands."""
    await ctx.send("Usage: `?ticket [active|block|close]`")

@ticket_cmd.command(name='close')
async def ticket_close(ctx):
    """Moves ticket to Archives, saves transcript, and locks it."""
    if not ctx.channel.name.lower().startswith("ticket-"):
        await ctx.send("❌ This command can only be used in ticket channels.")
        return

    # Find Archive Category
    category = ctx.guild.get_channel(CLOSED_ARCHIVES_ID)
    if not category:
        category = discord.utils.get(ctx.guild.categories, name="Closed Archives")

    # Generate Transcript
    await ctx.send("📝 Generating transcript...")
    try:
        messages = [msg async for msg in ctx.channel.history(limit=None, oldest_first=True)]
        transcript = []
        transcript.append(f"--- Server: {SERVER_ID_FLAG} ({ctx.guild.name}) ---")
        transcript.append(f"--- Ticket: {ctx.channel.name} ---")
        
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript.append(f"[{timestamp}] {msg.author.name}: {msg.content}")
            if msg.attachments:
                for att in msg.attachments:
                    transcript.append(f"    [Attachment] {att.url}")
        
        transcript_content = "\n".join(transcript)
        file_name = f"transcript-{SERVER_ID_FLAG}-{ctx.channel.name}.txt"
        
        # Create a temporary file
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(transcript_content)
        
        # Send file to channel
        await ctx.send(file=discord.File(file_name))
        os.remove(file_name) # Cleanup
        
    except Exception as e:
        print(f"❌ [Ticket] Transcript failed: {e}")
        await ctx.send(f"⚠️ Failed to generate transcript: {e}")

    # Archive Channel
    if category:
        await ctx.channel.edit(category=category, sync_permissions=True)
        await ctx.send(f"✅ Moved to **{category.name}** & Permissions Locked.")
    else:
        await ctx.send("⚠️ Archive Category not found (Check Env or creating 'Closed Archives'). Ticket closed but not moved.")

async def close_ticket_channel(channel, guild):
    """Refactored logic to close a ticket channel."""
    # Find Archive Category
    category = guild.get_channel(CLOSED_ARCHIVES_ID)
    if not category:
        category = discord.utils.get(guild.categories, name="Closed Archives")

    # Generate Transcript
    await channel.send("📝 Generating transcript...")
    try:
        messages = [msg async for msg in channel.history(limit=None, oldest_first=True)]
        transcript = []
        transcript.append(f"--- Server: {SERVER_ID_FLAG} ({guild.name}) ---")
        transcript.append(f"--- Ticket: {channel.name} ---")
        
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript.append(f"[{timestamp}] {msg.author.name}: {msg.content}")
            if msg.attachments:
                for att in msg.attachments:
                    transcript.append(f"    [Attachment] {att.url}")
        
        transcript_content = "\n".join(transcript)
        file_name = f"transcript-{SERVER_ID_FLAG}-{channel.name}.txt"
        
        # Create a temporary file
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(transcript_content)
        
        # Send file to channel
        await channel.send(file=discord.File(file_name))
        os.remove(file_name) # Cleanup
        
    except Exception as e:
        print(f"❌ [Ticket] Transcript failed: {e}")
        await channel.send(f"⚠️ Failed to generate transcript: {e}")

    # Archive Channel
    if category:
        await channel.edit(category=category, sync_permissions=True)
        await channel.send(f"✅ Moved to **{category.name}** & Permissions Locked.")
        # Mark as closed in DB
        if conversation_manager:
             active_conv = conversation_manager.get_or_create_conversation(channel.id)
             if active_conv:
                 from src import db # Lazy import to avoid circular dependency if needed or just use db directly
                 # conversation_manager.start_new_conversation only closes "old" ones. 
                 # We probably want a explicit close method in manager or just use logic here.
                 pass # For now, just moving channel is enough representation of "Closed"

    else:
        await channel.send("⚠️ Archive Category not found. Ticket closed but not moved.")

@bot.command(name='setup_tickets')
async def setup_tickets(ctx):
    """Deploys the Ticket Creation Panel manually."""
    embed = discord.Embed(
        title="📬 Support Tickets",
        description="Click the button below to open a private ticket with the staff.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete()

# --- Startup ---

@bot.event
async def on_ready():
    print(f'🤖 {BOT_NAME} is online as {bot.user} (v1.0 - Consolidated)')
    
    # Register Persistent Views
    bot.add_view(TicketView())
    bot.add_view(InterviewView())
    print(f'   Views Registered.')

    # Identity Enforcement
    if not bot.guilds:
        print("⚠️ Cache empty. Fetching guilds...")
        async for g in bot.fetch_guilds(limit=5):
            pass # Just populating cache
    
    if not bot.guilds:
        print("❌ Bot is not in any guilds.")
        print(f"🔗 Invite Link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot")
    
    for guild in bot.guilds:
        try:
            if guild.me.nick != BOT_NAME:
                print(f"🔄 Renaming to '{BOT_NAME}' in {guild.name}...")
                await guild.me.edit(nick=BOT_NAME)
        except Exception as e:
             print(f"⚠️ Failed to rename: {e}")

    # Start Background Task
    if not check_ticket_panel.is_running():
        check_ticket_panel.start()

    sys.stdout.flush()

@bot.event
async def on_guild_join(guild):
    print(f"🎉 Joined new guild: {guild.name} ({guild.id})")
    try:
        # Rename
        await guild.me.edit(nick=BOT_NAME)
        print(f"✅ Renamed to {BOT_NAME}")
        
        # Trigger Setup
        await process_guild_tickets(guild)
    except Exception as e:
        print(f"⚠️ Setup on join failed: {e}")
    if not check_ticket_panel.is_running():
        check_ticket_panel.start()

    sys.stdout.flush()

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Process commands first
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # Check if in a ticket channel
    if hasattr(message.channel, "name") and (message.channel.name.startswith("ticket-") or message.channel.name.startswith("incoming-")):
        # Check if conversation manager is active
        if conversation_manager and brain:
            # Add user message to history
            conversation_manager.add_user_message(message.channel.id, message.content)
            
            async with message.channel.typing():
                # Define Actions
                available_actions = [
                    {
                        "name": "close_ticket",
                        "description": "Closes the current ticket, archives it, and saves a transcript.",
                        "parameters": {}
                    }
                ]

                # Think
                thought = await brain.think(
                    user_message=message.content,
                    available_actions=available_actions, 
                    history=conversation_manager.get_history(message.channel.id), 
                    mode="ticket_assistant"
                )
                
                # Check for Action
                action = thought.get("action")
                if action and action.get("name") == "close_ticket":
                    await message.channel.send("🔒 Closing ticket as requested...")
                    await close_ticket_channel(message.channel, message.guild)
                    # Don't send reply if closing
                else:
                    reply = thought.get("reply", "")
                    if reply:
                        await message.channel.send(reply)
                        conversation_manager.add_bot_message(message.channel.id, reply)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: Token not found.")
    else:
        bot.run(TOKEN)
