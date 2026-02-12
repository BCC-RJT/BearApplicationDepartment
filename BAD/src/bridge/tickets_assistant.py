import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import asyncio
import json
import sys
import os
import socket # Added for Singleton Lock
import re
import traceback
from collections import deque
from datetime import datetime, timedelta

# --- Singleton Lock ---
# --- Singleton Lock ---
# prevents multiple instances from running
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 45679))
except socket.error as e:
    print(f"❌ FATAL: Another instance is already running (Port 45679 locked).")
    sys.exit(1)

# Moved to __main__ to allow testing imports

# --- Encoding Fix for Windows ---
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')
if not os.path.exists(ENV_PATH):
    ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
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

# Update to accept both ! and ?
bot = commands.Bot(command_prefix=['!', '?'], intents=intents)
bot.remove_command('help')

# --- Agent Integration ---
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src import db

try:
    from src.agent.brain import AgentBrain
    from src.agent.conversation_manager import ConversationManager
    brain = AgentBrain()
    conversation_manager = ConversationManager()
    print("🧠 Agent Brain & Conversation Manager Intergrated")
    
    # Initialize DB (and run migrations) - Moved outside try/except
    # db.init_db() # Moved below
except ImportError as e:
    print(f"⚠️ Warning: Agent components import failed: {e}")
    brain = None
    brain = None
    conversation_manager = None

# consistently init DB
db.init_db()

from src.bridge import archiver
import shutil
from src.bridge.dashboard_view import UnifiedDashboardView
from src.bridge.archive_view import ArchiveDashboardView

# --- Views ---


# --- Views ---
class RestoreView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="🔄 Restore Ticket", style=discord.ButtonStyle.success, custom_id="restore_ticket_btn")
    async def restore_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # 1. Update DB
        # Defaulting to active if restored
        db.update_ticket_status(interaction.channel.id, 'active')
        
        # 2. Move to Incoming/Active Categories
        # Try finding INCOMING first, then defaults
        guild = interaction.guild
        category = guild.get_channel(INCOMING_TICKETS_ID)
        if not category:
             category = discord.utils.get(guild.categories, name="📨 Incoming Tickets")
        if not category:
            # Fallback to active
            category = guild.get_channel(ACTIVE_TICKETS_ID)
            
        if category:
            await interaction.channel.edit(category=category)
            await interaction.followup.send("✅ Ticket restored to active duty.")
        else:
            await interaction.followup.send("✅ Ticket restored (could not move category).")
            
        # 3. Disable button
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

class ConfirmDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = False

    @discord.ui.button(label="🗑️ Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

class EscalateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Select user(s) to escalate to...", min_values=1, max_values=1, custom_id="escalate_select")
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        member = select.values[0]
        
        # Logic from original escalate command
        # Check permissions/context
        if not (interaction.channel.name.startswith("ticket-") or interaction.channel.name.startswith("incoming-")):
            await interaction.response.send_message("⚠️ This can only be used in ticket channels.", ephemeral=True)
            return

        await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
        await interaction.response.send_message(f"🚨 Ticket escalated to {member.mention}.")
        
        # Optional: Disable after use or keep active? Plan said "Optional: Disable".
        # Let's disable for cleanliness.
        select.disabled = True
        await interaction.message.edit(view=self)





class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.select(custom_id="dashboard_jump", placeholder="🚀 Jump to a ticket...", min_values=1, max_values=1, options=[discord.SelectOption(label="Loading...", value="0")])
    async def jump_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        channel_id = select.values[0]
        if channel_id == "0":
            await interaction.response.send_message("❌ No ticket selected.", ephemeral=True)
            return
            
        channel = interaction.guild.get_channel(int(channel_id))
        if channel:
             await interaction.response.send_message(f"🚀 **Jump to**: {channel.mention}", ephemeral=True)
        else:
             await interaction.response.send_message("❌ Channel not found.", ephemeral=True)

    @discord.ui.select(custom_id="dashboard_role_switch", placeholder="View Mode", min_values=1, max_values=1, options=[discord.SelectOption(label="Loading...", value="User")])
    async def role_switch_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Delegate to UnifiedDashboardView logic
        # We need to reconstruct the view because this is a persistent handler catching the interaction
        from src.bridge.dashboard_view import UnifiedDashboardView
        # Pass the global callback for ticket creation
        view = UnifiedDashboardView(interaction.user, create_ticket_callback=global_create_ticket_callback)
        
        # Override role with selection
        try:
            selected_role = select.values[0]
            view.current_role = selected_role
            view.update_components()
            
            embed = await view.generate_embed(interaction.guild)
            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.defer() # Acknowledge if not already done by edit/defer in view? 
            # Note: message.edit doesn't defer. We should defer first or after?
            # switch_role_callback in dashboard_view defers first.
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Failed to switch view: {e}", ephemeral=True)
            else:
                print(f"Failed to switch view: {e}")

    @discord.ui.button(label="🔄 Refresh Dashboard", style=discord.ButtonStyle.secondary, custom_id="dashboard_refresh")
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if we are refreshing a Unified Dashboard (by checking footer or title)
        is_unified = False
        if interaction.message.embeds:
            footer_text = interaction.message.embeds[0].footer.text or ""
            if "Viewing as" in footer_text:
                is_unified = True
                
        if is_unified:
             # Rebuild Unified View
             # Note: We use interaction.user as the viewer. 
             # Technically if a manager refreshes a user's view, it might switch to manager view, which is intended behavior (context awareness).
             from src.bridge.dashboard_view import UnifiedDashboardView # Ensure import availability
             
             # Pass callback if User Role (or generally)
             view = UnifiedDashboardView(interaction.user, create_ticket_callback=global_create_ticket_callback)
             embed = await view.generate_embed(interaction.guild)
             await interaction.message.edit(embed=embed, view=view)
        else:
             # Legacy/Manager Dashboard
             view = create_dashboard_view(interaction.guild)
             embed = generate_dashboard_embed(interaction.guild)
             await interaction.message.edit(embed=embed, view=view)

    @discord.ui.button(label="📢 Announce Queue", style=discord.ButtonStyle.primary, custom_id="dashboard_announce")
    async def announce_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        stats = db.get_ticket_stats()
        await interaction.channel.send(f"📢 **Status Update**: We currently have **{stats['total_open']}** open tickets ({stats['unassigned']} unassigned).")
        await interaction.response.defer()

def create_dashboard_view(guild):
    """Helper to create a DashboardView with populated select options."""
    view = DashboardView()
    stats = db.get_ticket_stats()
    tickets = stats['active_list'][:25] # Limit to 25 for select menu
    
    options = []
    for t in tickets:
        title = t['title'] or "No Title"
        label = f"#{t['id']} {title[:50]}" 
        emoji = "🔴" if t['urgency'] and ("High" in t['urgency'] or "10" in t['urgency']) else "🟢"
        if not t['channel_id']: continue
        
        desc = f"User: {t['user_name']}"
        options.append(discord.SelectOption(label=label, value=str(t['channel_id']), description=desc, emoji=emoji))
    
    # Find the select component
    for child in view.children:
        if isinstance(child, discord.ui.Select) and child.custom_id == "dashboard_jump":
            if options:
                child.options = options
                child.disabled = False
            else:
                child.options = [discord.SelectOption(label="No active tickets", value="0")]
                child.disabled = True
            break
            
    # Remove the role_switch_select from Legacy View (it's only for Unified View handling)
    for child in view.children:
        if isinstance(child, discord.ui.Select) and child.custom_id == "dashboard_role_switch":
            view.remove_item(child)
            break
            
    return view

def is_ticket_channel(channel):
    """Checks if the channel is a valid ticket channel (by Name and Category)."""
    if not hasattr(channel, "name"):
        return False
        
    # Check Name Pattern
    if not (channel.name.startswith("ticket-") or channel.name.startswith("incoming-")):
        return False
        
    # Check Category (Enforcement)
    # We restrict to known Ticket Categories or None (for Drafts)
    # If a channel named 'ticket-foo' is in 'General' category, it will return False.
    valid_categories = [
        MANAGER_INBOX_ID, 
        INCOMING_TICKETS_ID, 
        ACTIVE_TICKETS_ID, 
        BLOCKED_ESCALATED_ID, 
        CLOSED_ARCHIVES_ID
    ]
    
    # Filter out 0 (not set)
    valid_categories = [c for c in valid_categories if c != 0]
    
    if channel.category_id is None:
        # Allow uncategorized for Drafts (until they are moved)
        return True
        
    if valid_categories and channel.category_id not in valid_categories:
        # It has a category, but it's NOT a ticket category
        return False
        
    return True

def generate_dashboard_embed(guild):
    """Generates the dashboard embed based on current stats."""
    stats = db.get_ticket_stats()
    
    embed = discord.Embed(title="🎛️ Manager Command Center", color=discord.Color.dark_theme())
    embed.description = f"**Active Overview**\nTotal Open: `{stats['total_open']}`\nUnassigned: `{stats['unassigned']}`\nHigh Priority: `{stats['urgent']}`"
    
    # Active List
    tickets = stats['active_list']
    if tickets:
        list_str = ""
        for t in tickets[:10]: # Limit to 10
            # Format: #ID - <#ChannelID> ...
            assigned_text = "Unassigned"
            if t['assigned_to']:
                member = guild.get_member(int(t['assigned_to']))
                assigned_text = member.display_name if member else "Unknown"
            
            # Use channel link if ID exists
            chan_link = f"<#{t['channel_id']}>" if t['channel_id'] else "#unknown"
            
            title = t['title'] or "No Title"
            list_str += f"**#{t['id']}** {chan_link}\n└ 📂 {title} | 👤 {t['user_name']} | 👮 `{assigned_text}`\n"
        
        if len(tickets) > 10:
            list_str += f"\n...and {len(tickets)-10} more."
            
        embed.add_field(name="📋 Active Tickets (Top 10)", value=list_str or "No active tickets.", inline=False)
    else:
        embed.add_field(name="📋 Active Tickets", value="No active tickets found.", inline=False)
        
    embed.set_footer(text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    return embed

class EditTicketModal(discord.ui.Modal, title="Edit Ticket Details"):
    def __init__(self, current_title, current_urgency, current_desc, brain, conversation_manager, original_view):
        super().__init__()
        self.brain = brain
        self.conversation_manager = conversation_manager
        self.original_view = original_view
        
        self.ticket_title = discord.ui.TextInput(
            label="Ticket Title",
            default=current_title,
            max_length=100
        )
        self.ticket_urgency = discord.ui.TextInput(
            label="Urgency (1-10 or description)",
            default=current_urgency,
            max_length=50
        )
        self.ticket_desc = discord.ui.TextInput(
            label="Description",
            default=current_desc,
            style=discord.TextStyle.paragraph,
            max_length=2000
        )

        self.add_item(self.ticket_title)
        self.add_item(self.ticket_urgency)
        self.add_item(self.ticket_desc)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() # Acknowledge
        
        # 1. Update the Proposal View's data
        self.original_view.title = self.ticket_title.value
        self.original_view.urgency = self.ticket_urgency.value
        self.original_view.description = self.ticket_desc.value
        
        # 2. Update the Embed
        embed = discord.Embed(title="📝 Draft Ticket (Edited)", color=discord.Color.gold())
        embed.add_field(name="Title", value=self.original_view.title, inline=False)
        embed.add_field(name="Urgency", value=self.original_view.urgency, inline=True)
        embed.add_field(name="Description", value=self.original_view.description, inline=False)
        embed.set_footer(text=f"Edited by {interaction.user.display_name}")
        
        await interaction.message.edit(embed=embed, view=self.original_view)
        
        # 3. Inject into Brain Memory so it knows the context changed
        if self.conversation_manager:
            system_note = (
                f"[System Event] User manually edited the ticket draft.\n"
                f"New Title: {self.original_view.title}\n"
                f"New Urgency: {self.original_view.urgency}\n"
                f"New Description: {self.original_view.description}"
            )
            self.conversation_manager.add_user_message(interaction.channel.id, system_note)
            
            # Optional: Trigger a "Thinking" pass? 
            # Not strictly necessary if we just wait for the user to say "Looks good" or "Thanks".
            # But the prompt says "With each response... offer a new proposed ticket".
            # Here we just updated the EXISTING proposal in place, which is better UX than spamming new ones.

class ProposalView(discord.ui.View):
    def __init__(self, title, urgency, description, brain=None, conversation_manager=None):
        super().__init__(timeout=None)
        self.title = title
        self.urgency = urgency
        self.description = description
        self.brain = brain
        self.conversation_manager = conversation_manager

    @discord.ui.button(label="✅ Accept & Submit", style=discord.ButtonStyle.green, custom_id="submit_ticket_btn")
    async def submit_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        channel = interaction.channel
        guild = interaction.guild
        
        # 1. Update DB Details & Status
        db.update_ticket_details(channel.id, self.title, self.description, self.urgency)
        db.update_ticket_status(channel.id, 'active')

        # 2. Move to Incoming/Active Categories
        # Try finding INCOMING first, then defaults
        category = guild.get_channel(INCOMING_TICKETS_ID)
        if not category:
             category = discord.utils.get(guild.categories, name="📨 Incoming Tickets")
        if not category:
             # Fallback to Inbox or Manager Inbox
             category = guild.get_channel(MANAGER_INBOX_ID)
        
        if not category:
             category = discord.utils.get(guild.categories, name="Tickets Inbox")
        if not category:
             category = discord.utils.get(guild.categories, name="Ticket Inbox")
        
        if category:
            await channel.edit(category=category)
        
        # 2. Rename (remove 'incoming-')
        if channel.name.startswith("incoming-"):
            new_name = channel.name.replace("incoming-", "ticket-")
            await channel.edit(name=new_name)

        # 3. Ping Staff
        staff_role = discord.utils.get(guild.roles, name="Staff") or discord.utils.get(guild.roles, name="Manager")
        mention = staff_role.mention if staff_role else "@here"
        
        # New Embed with Final Details
        embed = discord.Embed(title=f"🎫 {self.title}", description=self.description, color=discord.Color.green())
        embed.add_field(name="Urgency", value=self.urgency)
        embed.add_field(name="Submitted By", value=interaction.user.mention)
        
        # Determine Time of Day
        from datetime import datetime
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "have a great morning!"
        elif 12 <= current_hour < 17:
            greeting = "have a great afternoon!"
        else:
            greeting = "have a great evening!"

        # Send User-Requested Confirmation
        await channel.send(
            f"📨 **Ticket Created!** {mention}\n"
            f"Great! I've created the ticket for you and added you to our queue. Watch here for progress.\n"
            f"{greeting.capitalize()}", 
            embed=embed
        )
        
        # 4. Disable buttons and Cleanup
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        # 5. Tell Brain it's done (Optional)
        if self.conversation_manager:
             self.conversation_manager.add_user_message(channel.id, "[System Event] Ticket Submitted.")

    @discord.ui.button(label="✏️ Edit Manually", style=discord.ButtonStyle.secondary, custom_id="edit_ticket_btn")
    async def edit_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Open the Modal
        modal = EditTicketModal(self.title, self.urgency, self.description, self.brain, self.conversation_manager, self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🗑️ Discard", style=discord.ButtonStyle.danger, custom_id="discard_ticket_btn")
    async def discard_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Ask for confirmation or just do it? User said "If the user discards the ticket it should be filed under the closed archives category."
        
        await interaction.response.defer()
        channel = interaction.channel
        guild = interaction.guild
        
        # 0. Update DB
        db.update_ticket_status(channel.id, 'closed')

        # 1. Move to Closed Archives
        category = guild.get_channel(CLOSED_ARCHIVES_ID)
        if not category:
             category = discord.utils.get(guild.categories, name="🗄️ Closed Archives")
        if not category:
             category = discord.utils.get(guild.categories, name="Archives") # Fallback
             
        if category:
            await channel.edit(category=category)
            await channel.send("🗑️ Ticket discarded and moved to archives.")
        else:
            await channel.send("🗑️ Ticket discarded. (Archive category not found, so simply closing).")
            # Maybe delete? 
            # User instruction: "If the user discards the ticket it should be filed under the closed archives category."
            
        # 2. Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        # 3. Stop conversation?
        # "Once the user creates the ticket the chat mode should be turned off."
        # If discarded, we probably also want to stop the bot from replying further?
        # We can do this by just not having the bot reply to the "System Event" or just let it be.

class InterviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Keeping this for backward compatibility if needed, using ProposalView for new flow



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
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        try:
            # 1. Create DB Record to get ID
            ticket_id = db.create_ticket_record("pending", guild.id, user.id, user.name)
            
            # Format: ticket-BAD-001 (or just ticket-1)
            # User request: "BAD-0001" style numbering might be good for display, but channel names usually keep it simple or use the ID.
            # Let's go with ticket-{id}-{user}
            channel_name = f"ticket-{ticket_id}-{user.name}"
            # Sanitize - Strictly alphanumeric and dashes
            channel_name = re.sub(r'[^a-z0-9\-_]', '', channel_name.replace(" ", "-").lower())

            # Find Initial Category (Tickets Inbox) or None (Draft)
            # User workflow: Draft -> Assistant -> Submit -> Inbox
            # So start with None (Uncategorized)
            channel = await guild.create_text_channel(channel_name, category=None, position=0, overwrites=overwrites)
            
            # Update DB with actual channel ID
            # We created it with "pending" because we didn't have the channel ID yet, or we can just update it now.
            # Actually, create_ticket_record takes channel_id. 
            # Strategy: Create channel first? No, we want ID for the name.
            # Strategy: Create DB record with dummy channel_id, then update it.
            
            # Re-doing the flow for atomic safety:
            # 1. Create DB record -> Get ID
            # 2. Create Channel with ID
            # 3. Update DB record with valid Channel ID
            
            db.update_ticket_status(str(channel.id), 'draft') # optimizing to just use update logic or raw sql if needed
            # We need a way to update the channel_id for the record we just created.
            # Let's hack it: The DB schema has channel_id as non-primary.
            # We can execute a direct update here or add a function. 
            # For now, let's just use raw cursor or add a helper.
            # Simpler: Create channel with temp name, THEN rename? No, that's ugly.
            
            # Let's add a `update_ticket_channel_id(ticket_pk, new_channel_id)` to db.py?
            # Or just use the `ticket_id` returned.
            
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("UPDATE tickets SET channel_id = ? WHERE id = ?", (str(channel.id), ticket_id))
            conn.commit()
            conn.close()
            
            # Start Conversation
            if conversation_manager:
                conversation_manager.start_new_conversation(channel.id)
                # We let the bot logic generate the greeting based on the new system prompt
                # But we trigger it by simulating a join event or just having the bot speak first?
                # Actually, the brain needs a trigger. Let's force a "hello" from the bot.
                greeting_part_1 = f"Hey {user.mention}! I'm your Ticket Assistant. I'm here to help get this sorted for you."
                
                embed_controls = discord.Embed(
                    title="Ticket Controls",
                    description="If you created this by mistake, just hit the button below to discard it.",
                    color=discord.Color.red()
                )
                
                # Message 0: Controls (First)
                await channel.send(embed=embed_controls, view=TicketControlView())

                # Message 1: Greeting
                await channel.send(content=greeting_part_1)
                
                # Message 2: The Question
                greeting_part_2 = "So, what's going on? In a few words, just tell me what the issue is, what you're expecting to happen, and when you need this done by."
                await channel.send(content=greeting_part_2)

                # Record both in conversation history
                conversation_manager.add_bot_message(channel.id, greeting_part_1)
                conversation_manager.add_bot_message(channel.id, greeting_part_2)
            
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
            # Log to file
            try:
                with open("ticket_errors.log", "a") as f:
                    f.write(f"[{datetime.now()}] Error creating ticket:\n")
                    traceback.print_exc(file=f)
                    f.write("\n")
            except:
                pass

# --- Global Callback for Dashboard ---
async def global_create_ticket_callback(interaction: discord.Interaction):
    """Wrapper to allow UnifiedDashboardView to trigger TicketView logic."""
    view = TicketView()
    # Pass None as button since the logic doesn't use it
    await view.create_ticket(interaction, None)

# --- Background Tasks & Events ---

@tasks.loop(minutes=5)
async def check_ticket_panel():
    """Periodically checks if the Ticket Panel is present in #tickets."""
    print("🔎 Checking Ticket Panel status...")
    await bot.wait_until_ready()
    
    # Try using cache first
    guilds_to_check = bot.guilds
    
    # If cache empty, try explicit fetch
    if not guilds_to_check:
        print(f"⚠️ Cache empty. Attempting API fetch...")
        try:
             guilds_to_check = []
             async for g in bot.fetch_guilds(limit=5):
                 guilds_to_check.append(g)
        except Exception as e:
             print(f"❌ API Fetch failed: {e}")
             return

    if not guilds_to_check:
        print("❌ No guilds found (Cache & API empty).")
        return

    for guild_ref in guilds_to_check:
        # fetch_guilds returns Guild objects with limited data, need full object
        try:
            guild = await bot.fetch_guild(guild_ref.id)
            # print(f"   Checking Guild: {guild.name}")
            await process_guild_tickets(guild)
        except Exception as e:
            print(f"   ❌ Failed to process guild {guild_ref.id}: {e}")

async def process_guild_tickets(guild):
    # Ensure channels are cached or fetched
    try:
        channels = await guild.fetch_channels()
        channel = discord.utils.get(channels, name="tickets")
    except Exception as e:
        print(f"   ⚠️ Channel fetch failed: {e}")
        return

    if channel and isinstance(channel, discord.TextChannel):
        # print(f"   ✅ Found #tickets ({channel.id})")
        try:
            # Check recent history
            panel_exists = False
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "📬 Support Tickets":
                    panel_exists = True
                    break
            
            # Enforce Permissions (Always)
            bot_member = guild.me
            if not bot_member:
                try:
                    bot_member = await guild.fetch_member(bot.user.id)
                except Exception as e:
                    print(f"   ⚠️ Could not fetch bot member: {e}")
                    return

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                bot_member: discord.PermissionOverwrite(send_messages=True)
            }
            # Only update if current overwrites differ (to save API calls) - simplified: just update
            # But await channel.edit might be rate limited if called too often.
            # Let's check if it matches first? 
            # For now, just applying it is safer to ensure it sticks.
            if channel.overwrites_for(guild.default_role).send_messages is not False:
                 print(f"🔒 Locking down #{channel.name} permissions...")
                 await channel.edit(overwrites=overwrites)

            if not panel_exists:
                print(f"📦 Auto-Deploying Ticket Panel to #{channel.name} in {guild.name}")
                embed = discord.Embed(
                    title="📬 Support Tickets",
                    description="Click the button below to open a private ticket with the staff.",
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed, view=TicketView())
            # else:
            #     print(f"   ✅ Panel OK.")
        except Exception as e:
            print(f"⚠️ Failed to auto-deploy panel: {e}")
    else:
        # print(f"   ❌ Channel #tickets not found in {guild.name}")
        pass

@tasks.loop(hours=24)
async def check_and_archive_tickets():
    """Archives closed tickets that exceed retention policy."""
    print("🧹 Running Automated Ticket Archival...")
    await bot.wait_until_ready()
    
    try:
        closed_tickets = db.get_closed_tickets()
        
        # Policy: Keep max 50 AND max 7 days old
        # archive if (index >= 50) OR (age > 7 days) (whichever is less kept -> stricter policy wins)
        
        archived_count = 0
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for i, ticket in enumerate(closed_tickets):
            should_archive = False
            
            # Check 1: Count limit (Keep only top 50)
            if i >= 50:
                should_archive = True
            
            # Check 2: Age limit (Keep only < 7 days)
            if not should_archive:
                closed_at_str = ticket['closed_at']
                if closed_at_str:
                    try:
                        # SQLite CURRENT_TIMESTAMP is 'YYYY-MM-DD HH:MM:SS'
                        closed_at = datetime.strptime(closed_at_str, "%Y-%m-%d %H:%M:%S")
                        if closed_at < cutoff_date:
                            should_archive = True
                    except ValueError:
                        print(f"⚠️ Could not parse date for ticket {ticket.get('channel_id')}: {closed_at_str}")
                        pass
            
            if should_archive:
                channel_id = ticket['channel_id']
                if not channel_id:
                    continue
                    
                channel_id = int(channel_id)
                
                # Archive Data First
                try:
                    channel = bot.get_channel(channel_id)
                    if channel:
                         print(f"   💾 Saving archive data for {channel.name}...")
                         archive_path = await archiver.archive_ticket(channel)
                         
                         # Update DB first
                         db.mark_ticket_archived(channel_id)
                         db.update_archive_path(channel_id, archive_path)
                         
                         # Delete Channel
                         await channel.delete(reason="Automated Archival: Retention Policy")
                         print(f"   🗑️ Archived & Deleted channel {channel.name} ({channel.id})")
                         archived_count += 1
                    else:
                         print(f"   ⚠️ Channel {channel_id} not found, marking archived in DB.")
                         db.mark_ticket_archived(channel_id)

                except Exception as e:
                    print(f"   ⚠️ Failed to archive channel {channel_id}: {e}")
                
        if archived_count > 0:
            print(f"✅ Archival Complete. Archived {archived_count} tickets.")
            
    except Exception as e:
        print(f"❌ Archival Failed: {e}")

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} is online (v2.0 - Active Ticket Workflow)')
    print(f'   ID: {bot.user.id}')
    
    # Register Persistent Views
    bot.add_view(TicketView())
    bot.add_view(NewTicketView())
    bot.add_view(ProposalView("", "", "")) # Register class, arguments don't matter for persistence check
    bot.add_view(DiscardView())
    bot.add_view(TicketControlView())
    bot.add_view(RestoreView())
    bot.add_view(EscalateView())
    # bot.add_view(BlockUserView()) # Removed

    bot.add_view(DashboardView())
    print(f'   Ticket Views Registered.')

    # Sync Slash Commands
    try:
        synced = await bot.tree.sync()
        print(f"   Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"   ⚠️ Failed to sync slash commands: {e}")

    # Update Nickname
    for guild in bot.guilds:
        try:
            if guild.me.nick != "Ticket Assistant":
                print(f"Updating nickname in {guild.name} to 'Ticket Assistant'...")
                await guild.me.edit(nick="Ticket Assistant")
        except:
            pass
            
    # Start Background Task
    if not check_ticket_panel.is_running():
        check_ticket_panel.start()
        
    if not check_and_archive_tickets.is_running():
        check_and_archive_tickets.start()

@bot.tree.command(name='setup_tickets', description="Deploys the Ticket Creation Panel (Admin).")
@commands.has_permissions(administrator=True)
async def setup_tickets_slash(interaction: discord.Interaction):
    """Deploys the Ticket Creation Panel to the current channel."""
    embed = discord.Embed(
        title="📬 Support Tickets",
        description="Click the button below to open a private ticket with the staff.",
        color=discord.Color.blue()
    )
    # Lock down channel permissions
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(send_messages=False),
        interaction.guild.me: discord.PermissionOverwrite(send_messages=True)
    }
    await interaction.channel.edit(overwrites=overwrites)

    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Ticket Panel deployed.", ephemeral=True)

class AssignView(discord.ui.View):
    def __init__(self, mode="assign"):
        super().__init__(timeout=60)
        self.mode = mode
        
    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Select user(s)...", min_values=1, max_values=1)
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        member = select.values[0]
        
        if not (interaction.channel.name.startswith("ticket-") or interaction.channel.name.startswith("incoming-")):
            await interaction.response.send_message("⚠️ This can only be used in ticket channels.", ephemeral=True)
            return

        await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
        
        if self.mode == "assign":
             await interaction.response.send_message(f"✅ {member.mention} has been assigned to this ticket.")
             
             # Move to Active Category
             try:
                 category = interaction.guild.get_channel(ACTIVE_TICKETS_ID)
                 if category and interaction.channel.category_id != ACTIVE_TICKETS_ID:
                     await interaction.channel.edit(category=category)
                     # Update DB
                     db.update_ticket_status(interaction.channel.id, 'active')
             except Exception as e:
                 print(f"Failed to move to active: {e}")
                 
        else:
             await interaction.response.send_message(f"🚨 Ticket escalated to {member.mention}.")
             
             # Move to Escalated Category
             try:
                 category = interaction.guild.get_channel(BLOCKED_ESCALATED_ID)
                 if category and interaction.channel.category_id != BLOCKED_ESCALATED_ID:
                     await interaction.channel.edit(category=category)
                     db.update_ticket_status(interaction.channel.id, 'escalated')
             except Exception as e:
                 print(f"Failed to move to escalated: {e}")
        
        # Disable after use
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

@bot.command(name='assign')
async def assign_ticket(ctx, member: discord.Member = None):
    """Assigns a member. Usage: !assign or !assign @user"""
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
        await ctx.send("⚠️ This command only works in ticket channels.")
        return

    if member:
        # Classic mode
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
        await ctx.send(f"✅ {member.mention} has been assigned to this ticket.")
        
        # Move to Active Category
        try:
            category = ctx.guild.get_channel(ACTIVE_TICKETS_ID)
            if category and ctx.channel.category_id != ACTIVE_TICKETS_ID:
                await ctx.channel.edit(category=category)
                # Update DB
                # Update DB
                db.update_ticket_status(ctx.channel.id, 'active')
                db.update_ticket_assignment(ctx.channel.id, member.id)
        except Exception as e:
             print(f"Failed to move to active: {e}")

    else:
        # Menu mode
        await ctx.send("Select a user to assign:", view=AssignView(mode="assign"))

@bot.command(name='add')
async def add_helper(ctx, member: discord.Member = None):
    """Alias for assign."""
    await assign_ticket(ctx, member)

@bot.command(name='escalate')
async def escalate_ticket(ctx, member: discord.Member = None):
    """Escalates the ticket. Usage: !escalate or !escalate @user"""
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
        await ctx.send("⚠️ This command only works in ticket channels.")
        return

    if member:
        # Classic mode
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
        await ctx.send(f"🚨 Ticket escalated to {member.mention}.")
        
        # Move to Escalated Category
        try:
            category = ctx.guild.get_channel(BLOCKED_ESCALATED_ID)
            if category and ctx.channel.category_id != BLOCKED_ESCALATED_ID:
                await ctx.channel.edit(category=category)
                db.update_ticket_status(ctx.channel.id, 'escalated')
        except Exception as e:
             print(f"Failed to move to escalated: {e}")
             
    else:
        # Menu mode
        await ctx.send("Select a user to escalate to:", view=AssignView(mode="escalate"))

@bot.command(name='return')
async def return_ticket(ctx):
    """Returns the ticket to the queue (unassigns and moves to Inbox)."""
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
        await ctx.send("⚠️ This command only works in ticket channels.")
        return

    # 1. Determine Target Category (Inbox)
    category = ctx.guild.get_channel(MANAGER_INBOX_ID)
    if not category:
         category = discord.utils.get(ctx.guild.categories, name="Tickets Inbox")
    if not category:
         category = discord.utils.get(ctx.guild.categories, name="Ticket Inbox")

    if not category:
        await ctx.send("⚠️ Could not find Inbox category to return the ticket to.")
        return

    await ctx.send("🔄 Returning ticket to queue...")

    # 2. Move Channel
    try:
        if ctx.channel.category_id != category.id:
            await ctx.channel.edit(category=category)
    except Exception as e:
        await ctx.send(f"⚠️ Failed to move channel: {e}")
        return

    # 3. Update Status
    # We keep it 'active' since it's just unassigned but still open.
    # If there was a 'blocked' status, we are clearing it.
    db.update_ticket_status(ctx.channel.id, 'active')
    db.update_ticket_assignment(ctx.channel.id, None)

    # 4. Remove User Assignment (Overwrite)
    # This removes the explicit permission overwrite for the command invoker,
    # falling back to their role permissions (Staff/Manager).
    try:
        await ctx.channel.set_permissions(ctx.author, overwrite=None)
        await ctx.send(f"✅ Ticket returned to {category.name} and unassigned from you.")
    except Exception as e:
        print(f"Failed to remove permissions for {ctx.author}: {e}")
        await ctx.send(f"✅ Ticket returned to {category.name}.")

@bot.command(name='unassign')
async def unassign_ticket(ctx):
    """Alias for return."""
    await return_ticket(ctx)





@bot.command(name='abandon')
async def abandon_ticket_cmd(ctx):
    """Abandons the ticket in its current state and archives it."""
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
        await ctx.send("⚠️ This command only works in ticket channels.")
        return
    
    await ctx.send("🏚️ Abandoning ticket...")

    # Update DB
    db.update_ticket_status(ctx.channel.id, 'closed')

    # Archive
    try:
        archive_path = await archiver.archive_ticket(ctx.channel)
        db.update_archive_path(ctx.channel.id, archive_path)
    except Exception as e:
        await ctx.send(f"⚠️ Failed to save archive: {e}")

    # Move to Archives
    category = ctx.guild.get_channel(CLOSED_ARCHIVES_ID)
    if not category:
            category = discord.utils.get(ctx.guild.categories, name="🗄️ Closed Archives")
    if not category:
            category = discord.utils.get(ctx.guild.categories, name="Archives")

    if category:
        await ctx.channel.edit(category=category, sync_permissions=True)
        await ctx.send("🏚️ Ticket abandoned and moved to archives.")
    else:
        await ctx.send("🏚️ Ticket abandoned (Archive category not found).")

@bot.command(name='delete')
@commands.has_permissions(manage_channels=True)
async def delete_ticket_cmd(ctx):
    """Deletes a ticket entirely."""
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
         await ctx.send("⚠️ This command only works in ticket channels.")
         return

    view = ConfirmDeleteView()
    msg = await ctx.send("⚠️ **Are you sure?** This will permanently delete the ticket and channel (No Archive).", view=view)
    await view.wait()
    
    if view.value:
        await ctx.send("🗑️ Deleting ticket...")
        # DB Update
        db.update_ticket_status(ctx.channel.id, 'deleted')
        # Delete Channel
        await ctx.channel.delete(reason=f"Ticket Deleted by {ctx.author.display_name}")
    else:
        await ctx.send("❌ Delete cancelled.")

@bot.command(name='archive', aliases=['tickets'])
async def archive_command(ctx):
    """View the ticket archive dashboard."""
    # Check if user is staff (to view all)
    is_staff = False
    staff_role_names = ["Staff", "Support", "Admin", "Moderator", "Manager"]
    if hasattr(ctx.author, "roles"):
        for role in ctx.author.roles:
             if role.name in staff_role_names:
                 is_staff = True
                 break
    
    # Create view
    view = ArchiveDashboardView(ctx.author.id, show_all=is_staff)
    embed = await view.generate_embed(ctx.guild)
    
    await ctx.send(embed=embed, view=view)

@bot.command(name='close')
async def close_ticket_cmd(ctx):
    """Closes ticket with a resolved state, saves and sends a transcript."""
    # 1. Verify channel is a ticket channel
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
        await ctx.send("⚠️ This command only works in ticket channels.")
        return

    await ctx.send("🔒 Closing ticket...")

    # 2. Update DB
    db.update_ticket_status(ctx.channel.id, 'closed')

    # 3. Archive Ticket Data
    try:
        archive_path = await archiver.archive_ticket(ctx.channel)
        db.update_archive_path(ctx.channel.id, archive_path)
    except Exception as e:
        await ctx.send(f"⚠️ Failed to save archive: {e}")
        archive_path = None

    # 4. DM the User (Transcript)
    ticket_data = db.get_ticket(ctx.channel.id)
    target_user = None
    
    if ticket_data and ticket_data['user_id']:
        try:
             user_id = int(ticket_data['user_id'])
             target_user = ctx.guild.get_member(user_id)
        except:
             pass

    if target_user and archive_path:
        html_file = os.path.join(archive_path, "transcript.html")
        if os.path.exists(html_file):
            try:
                await target_user.send(
                    f"Your ticket **{ctx.channel.name}** has been closed. You can view the transcript attached.",
                    file=discord.File(html_file)
                )
                await ctx.send(f"✅ Transcript sent to {target_user.mention}.")
            except discord.Forbidden:
                 await ctx.send(f"⚠️ Could not DM transcript to {target_user.mention} (DMs closed).")
            except Exception as eobj:
                 await ctx.send(f"⚠️ Failed to send transcript: {eobj}")
    else:
        if not target_user:
             await ctx.send("⚠️ Could not identify ticket owner.")

    # 5. Move to Archives
    try:
        category = ctx.guild.get_channel(CLOSED_ARCHIVES_ID)
        if not category:
                category = discord.utils.get(ctx.guild.categories, name="🗄️ Closed Archives")
        if not category:
                category = discord.utils.get(ctx.guild.categories, name="Archives")
                
        if category:
            await ctx.channel.edit(category=category, sync_permissions=True)
            await ctx.send("🗄️ Ticket moved to archives.")
            
            if target_user:
                 await ctx.channel.set_permissions(target_user, send_messages=False, read_messages=True)
                 
        else:
            await ctx.send("⚠️ Archive category not found. Ticket remains open (but marked closed in DB).")
            
    except Exception as e:
        await ctx.send(f"⚠️ Failed to move ticket to archives: {e}")
        print(f"❌ Failed to move ticket {ctx.channel.name}: {e}")

@bot.tree.command(name='restore', description="Restores a ticket from archive.")
@commands.has_permissions(manage_channels=True)
async def restore_ticket_slash(interaction: discord.Interaction, ticket_id: int):
    """Restores a ticket from archive. Usage: /restore <ticket_id>"""
    await interaction.response.defer()
    
    await interaction.followup.send(f"🔄 Attempting to restore Ticket #{ticket_id}...")
    try:
        # Pass interaction as context-like object or modify archiver
        # We need an object that has guild, user, etc. interaction has them.
        
        # NOTE: archiver.restore_ticket_from_archive expects 'ctx' (with .send), we need to adapt or ensure archiver supports it.
        # Let's inspect archiver.restore_ticket_from_archive signature in a moment if this fails, but usually we can patch it.
        # Assuming archiver uses `ctx.guild`, `ctx.send`. 
        # Interaction has `interaction.guild`. `interaction.followup.send`.
        # We might need a wrapper or update archiver (which we can't see easily right now without another tool call).
        # Let's assume we can mock a context or that I should update archiver.
        # For now, I'll assume archiver might struggle with interaction unless I wrap it.
        
        # Helper Class to mimic Context for legacy functions
        class ContextWrapper:
            def __init__(self, inter):
                self.guild = inter.guild
                self.author = inter.user
                self.user = inter.user
                self.send = inter.followup.send
                
        ctx_mock = ContextWrapper(interaction)

        new_channel = await archiver.restore_ticket_from_archive(ctx_mock, ticket_id)
        if isinstance(new_channel, str): # Error message
             await interaction.followup.send(new_channel)
        else:
             await interaction.followup.send(f"✅ Ticket restored: {new_channel.mention}")
             
    except Exception as e:
        await interaction.followup.send(f"❌ Restoration failed: {e}")
        import traceback
        traceback.print_exc()

@bot.command(name='history')
async def history_cmd(ctx, member: discord.Member = None):
    """Shows ticket history for a user."""
    target = member or ctx.author
    tickets = db.get_user_tickets(target.id)
    
    if not tickets:
        await ctx.send(f"No ticket history found for {target.display_name}.")
        return

    embed = discord.Embed(title=f"Ticket History: {target.display_name}", color=discord.Color.blurple())
    
    # Show last 10
    for t in tickets[:10]:
        status_emoji = "🟢" if t['status'] == 'active' else "🔴" if t['status'] == 'closed' else "⚫"
        created = t['created_at'].split(" ")[0] # Just date
        embed.add_field(
            name=f"#{t['id']} {t['title']} ({created})",
            value=f"Status: {status_emoji} {t['status']}\nID: {t['id']}",
            inline=False
        )
        
    await ctx.send(embed=embed)

@bot.tree.command(name='view_archive', description="Retrieves the transcript for an archived ticket.")
async def view_archive_slash(interaction: discord.Interaction, ticket_id: int):
    """Retrieves the transcript for an archived ticket."""
    path = db.get_archive_path(ticket_id)
    if not path:
        await interaction.response.send_message(f"❌ No archive found for Ticket #{ticket_id}.", ephemeral=True)
        return
        
    html_file = os.path.join(path, "transcript.html")
    if os.path.exists(html_file):
        await interaction.response.send_message(f"📄 Transcript for Ticket #{ticket_id}:", file=discord.File(html_file), ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ Archive directory exists but transcript is missing.", ephemeral=True)

# Dashboard Command (Strictly Slash now)

@bot.tree.command(name="archive", description="View the ticket archive dashboard")
async def archive_slash(interaction: discord.Interaction):
    """View the ticket archive dashboard."""
    # Check if user is staff (to view all)
    is_staff = False
    staff_role_names = ["Staff", "Support", "Admin", "Moderator", "Manager"]
    if hasattr(interaction.user, "roles"):
        for role in interaction.user.roles:
             if role.name in staff_role_names:
                 is_staff = True
                 break
    
    # Create view
    view = ArchiveDashboardView(interaction.user.id, show_all=is_staff)
    embed = await view.generate_embed(interaction.guild)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="dashboard", description="Opens your personal Unified Dashboard (Private)")
async def dashboard_slash(interaction: discord.Interaction):
    """Opens the Unified Dashboard (User, Helper, Manager) privately."""
    # Pass the global callback
    view = UnifiedDashboardView(interaction.user, create_ticket_callback=global_create_ticket_callback)
    embed = await view.generate_embed(interaction.guild)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Slash commands for close/history removed to enforce Prefix-only for Ticket Commands


@bot.tree.command(name="tickethelp", description="Displays the list of user commands.")
async def help_slash(interaction: discord.Interaction):
    """Displays the list of user commands."""
    embed = discord.Embed(title="Ticket User Help", description="Commands available to all users.", color=discord.Color.blue())
    
    embed.add_field(name="/dashboard", value="Opens your personal ticket dashboard.", inline=False)
    embed.add_field(name="!close", value="Closes ticket with a resolved state, saves and sends a transcript.", inline=False)
    embed.add_field(name="!abandon", value="Abandons the ticket in its current state and archives it.", inline=False)
    embed.add_field(name="!delete", value="Deletes a ticket entirely (Confirm Required).", inline=False)
    embed.add_field(name="/tickethelp", value="Shows this message.", inline=False)
    embed.add_field(name="Note", value="Staff/Admins: Use /commands for full command list.", inline=False)

    embed.set_footer(text="Prefixes: ! or ?")
    await interaction.response.send_message(embed=embed, ephemeral=True)

class RestoreIDModal(discord.ui.Modal, title="Restore Ticket"):
    def __init__(self):
        super().__init__()
        self.ticket_id = discord.ui.TextInput(label="Ticket ID", placeholder="123", min_length=1)
        self.add_item(self.ticket_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            tid = int(self.ticket_id.value)
            
            # Helper Class to mimic Context for legacy functions
            class ContextWrapper:
                def __init__(self, inter):
                    self.guild = inter.guild
                    self.author = inter.user
                    self.user = inter.user
                    self.send = inter.followup.send
            
            ctx_mock = ContextWrapper(interaction)
            await interaction.followup.send(f"🔄 Attempting to restore Ticket #{tid}...")
            
            new_channel = await archiver.restore_ticket_from_archive(ctx_mock, tid)
            if isinstance(new_channel, str): 
                 await interaction.followup.send(new_channel)
            else:
                 await interaction.followup.send(f"✅ Ticket restored: {new_channel.mention}")
                 
        except ValueError:
            await interaction.followup.send("❌ Invalid Ticket ID (Must be specific number).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Restoration failed: {e}", ephemeral=True)

class ArchiveIDModal(discord.ui.Modal, title="View Archive"):
    def __init__(self):
        super().__init__()
        self.ticket_id = discord.ui.TextInput(label="Ticket ID", placeholder="123", min_length=1)
        self.add_item(self.ticket_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            tid = int(self.ticket_id.value)
            path = db.get_archive_path(tid)
            if not path:
                await interaction.response.send_message(f"❌ No archive found for Ticket #{tid}.", ephemeral=True)
                return
                
            html_file = os.path.join(path, "transcript.html")
            if os.path.exists(html_file):
                await interaction.response.send_message(f"📄 Transcript for Ticket #{tid}:", file=discord.File(html_file), ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ Archive directory exists but transcript is missing.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid Ticket ID.", ephemeral=True)


class CommandsView(discord.ui.View):
    def __init__(self, is_ticket, user, guild):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        
        # Add buttons based on context
        if is_ticket:
            # Ticket Context
            self.add_button("🔒 Close", discord.ButtonStyle.success, "cmd_quick_close", self.close_cb)
            
            # Staff Checks 
            is_staff = any(r.name.lower() in ["staff", "support", "manager", "admin"] for r in user.roles)
            if is_staff or user.guild_permissions.manage_channels:
                self.add_button("👮 Assign", discord.ButtonStyle.secondary, "cmd_quick_assign", self.assign_cb)
                self.add_button("🚨 Escalate", discord.ButtonStyle.secondary, "cmd_quick_escalate", self.escalate_cb)
                self.add_button("↩️ Return", discord.ButtonStyle.secondary, "cmd_quick_return", self.return_cb)
                self.add_button("🏚️ Abandon", discord.ButtonStyle.danger, "cmd_quick_abandon", self.abandon_cb)
            
            # Everyone
            self.add_button("📜 History", discord.ButtonStyle.primary, "cmd_quick_history", self.history_cb)
            # self.add_button("🎛️ Dashboard", discord.ButtonStyle.primary, "cmd_quick_dash", self.dash_cb)

        else:
            # Management Context
            self.add_button("🎛️ Dashboard", discord.ButtonStyle.primary, "cmd_quick_dash", self.dash_cb)
            self.add_button("📜 History", discord.ButtonStyle.secondary, "cmd_quick_history", self.history_cb)
            
            # Admin/Manager
            # if user.guild_permissions.ban_members:
            #     self.add_button("🚫 Block User", discord.ButtonStyle.danger, "cmd_quick_block", self.block_cb)
            
            if user.guild_permissions.manage_channels:
                self.add_button("🔄 Restore", discord.ButtonStyle.secondary, "cmd_quick_restore", self.restore_cb)
                self.add_button("📂 View Archive", discord.ButtonStyle.secondary, "cmd_quick_archive", self.archive_cb)
                



    def add_button(self, label, style, custom_id, callback):
        # We append a unique ID or use generic. Using generic is fine if ephemeral.
        btn = discord.ui.Button(label=label, style=style, custom_id=custom_id)
        btn.callback = callback
        self.add_item(btn)

    async def close_cb(self, interaction: discord.Interaction):
        await interaction.response.defer() # Not ephemeral, we want to act on the channel
        channel = interaction.channel
        guild = interaction.guild
        
        db.update_ticket_status(channel.id, 'closed')
        
        # Archive
        try:
             archive_path = await archiver.archive_ticket(channel)
             db.update_archive_path(channel.id, archive_path)
        except Exception as e:
             await interaction.followup.send(f"⚠️ Archive failed: {e}", ephemeral=True)

        category = guild.get_channel(CLOSED_ARCHIVES_ID)
        if not category: category = discord.utils.get(guild.categories, name="🗄️ Closed Archives")
        if not category: category = discord.utils.get(guild.categories, name="Archives")

        if category:
            await channel.edit(category=category)
            await channel.send("✅ Ticket resolved and moved to archives.", view=RestoreView())
        else:
            await channel.send("✅ Ticket resolved.", view=RestoreView())
        
        await interaction.followup.send("✅ Ticket Closed.", ephemeral=True)

    async def assign_cb(self, interaction: discord.Interaction):
        await interaction.response.send_message("Select a user to assign:", view=AssignView(mode="assign"), ephemeral=True)

    async def escalate_cb(self, interaction: discord.Interaction):
        await interaction.response.send_message("Select a user to escalate to:", view=AssignView(mode="escalate"), ephemeral=True)

    async def return_cb(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel = interaction.channel
        guild = interaction.guild
        
        category = guild.get_channel(MANAGER_INBOX_ID)
        if not category: category = discord.utils.get(guild.categories, name="Tickets Inbox")
        if not category: category = discord.utils.get(guild.categories, name="Ticket Inbox")
        
        if category:
            await channel.edit(category=category)
            
        db.update_ticket_status(channel.id, 'active')
        db.update_ticket_assignment(channel.id, None)
        
        try:
            await channel.set_permissions(interaction.user, overwrite=None)
        except:
            pass
            
        await interaction.followup.send("✅ Ticket returned to queue.", ephemeral=True)
        await channel.send(f"🔄 Ticket returned to {category.name if category else 'Queue'}.")

    async def abandon_cb(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel = interaction.channel
        guild = interaction.guild
        
        db.update_ticket_status(channel.id, 'closed')
        try:
            archive_path = await archiver.archive_ticket(channel)
            db.update_archive_path(channel.id, archive_path)
        except: pass
        
        category = guild.get_channel(CLOSED_ARCHIVES_ID)
        if not category: category = discord.utils.get(guild.categories, name="🗄️ Closed Archives")
        if not category: category = discord.utils.get(guild.categories, name="Archives")
        
        if category:
            await channel.edit(category=category)
            await channel.send("🏚️ Ticket abandoned and moved to archives.", view=RestoreView())
        else:
            await channel.send("🏚️ Ticket abandoned.", view=RestoreView())
            
        await interaction.followup.send("🏚️ Ticket Abandoned.", ephemeral=True)

    async def history_cb(self, interaction: discord.Interaction):
        tickets = db.get_user_tickets(interaction.user.id)
        if not tickets:
            await interaction.response.send_message("No ticket history found for you.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Ticket History: {interaction.user.display_name}", color=discord.Color.blurple())
        for t in tickets[:10]:
            status_emoji = "🟢" if t['status'] == 'active' else "🔴" if t['status'] == 'closed' else "⚫"
            created = t['created_at'].split(" ")[0]
            embed.add_field(name=f"#{t['id']} {t['title']} ({created})", value=f"Status: {status_emoji} {t['status']}", inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def dash_cb(self, interaction: discord.Interaction):
        view = UnifiedDashboardView(interaction.user)
        embed = await view.generate_embed(interaction.guild)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)



    async def restore_cb(self, interaction: discord.Interaction):
         await interaction.response.send_modal(RestoreIDModal())

    async def archive_cb(self, interaction: discord.Interaction):
         await interaction.response.send_modal(ArchiveIDModal())






@bot.tree.command(name='commands', description="Displays interactive command list.")
async def commands_slash(interaction: discord.Interaction):
    """Displays the list of available commands based on the current channel."""
    is_ticket = is_ticket_channel(interaction.channel)
    
    view = CommandsView(is_ticket, interaction.user, interaction.guild)
    
    if is_ticket:
        embed = discord.Embed(title="🎫 Ticket Commands", description="Click a button below to execute a command.", color=discord.Color.blue())
        # We can list them too if we want, but the buttons are self-explanatory.
        # Let's keep a brief list for clarity.
        embed.add_field(name="Available Actions", value="• Close Ticket\n• Assign / Escalate\n• Return to Queue\n• Abandon (Archive)\n• View History", inline=False)
    else:
        embed = discord.Embed(title="🛠️ Management Commands", description="Click a button below to execute a command.", color=discord.Color.red())
        embed.add_field(name="Available Actions", value="• Dashboard\n• History\n• Restore / View Archive", inline=False)
    
    embed.set_footer(text="Interactive Command Menu")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Auto-clean #tickets channel to prevent accidental posting
    if message.channel.name == "tickets":
        try:
            await message.delete()
        except Exception:
            pass
        return

    # Process commands first
    if message.content.startswith(tuple(bot.command_prefix)):
        await bot.process_commands(message)
        return

    # Check if in a ticket channel
    if is_ticket_channel(message.channel):
        # Check if conversation manager is active
        # Check if conversation manager is active and ticket is NOT yet submitted
        if conversation_manager and brain:
            # Check DB status
            status = db.get_ticket_status(message.channel.id)
            if status != 'active': # Only chat if not active (meaning still pending/draft)
                # Add user message to history
                conversation_manager.add_user_message(message.channel.id, message.content)
            
                async with message.channel.typing():
                    # Define Actions (for context, updated structure)
                    available_actions = [
                        "propose_ticket | <Title> | <Urgency> | <Description>",
                        "close_ticket"
                    ]

                    # Prepare Message with Attachments
                    user_message_content = message.content
                    if message.attachments:
                        attachment_list = "\n".join([f"<Attachment: {a.url}>" for a in message.attachments])
                        user_message_content += f"\n\n[System Note: User uploaded files]\n{attachment_list}"

                    # Think
                    thought = await brain.think(
                        user_message=user_message_content,
                        available_actions=available_actions, 
                        history=conversation_manager.get_history(message.channel.id), 
                        mode="ticket_assistant"
                    )
                    
                    # Check for Actions
                    actions = thought.get("actions", [])
                    reply = thought.get("reply", "")
                    proposal_handled = False
                    
                    # Execute Actions
                    for action in actions:
                        if "close_ticket" in action:
                            await message.channel.send(content="🔒 Closing ticket as requested...")
                            # In a real scenario, we might want to archive it properly
                            await message.channel.delete() 
                            return # Stop processing
                        
                        if "propose_ticket" in action:
                            # Parse: propose_ticket | Title | Urgency | Desc
                            try:
                                parts = action.split("|")
                                # parts[0] is 'propose_ticket '
                                title = parts[1].strip() if len(parts) > 1 else "Untitled"
                                urgency = parts[2].strip() if len(parts) > 2 else "Normal"
                                description = parts[3].strip() if len(parts) > 3 else "No description"
                                
                                
                                embed = discord.Embed(title="📝 Draft Ticket", color=discord.Color.gold())
                                embed.add_field(name="Title", value=title, inline=False)
                                embed.add_field(name="Urgency", value=urgency, inline=True)
                                embed.add_field(name="Description", value=description, inline=False)
                                
                                # Use the brain's reply as the content, or a default if empty
                                content_msg = reply if reply else "I have prepared this ticket based on our conversation. Is this correct?"
                                
                                await message.channel.send(
                                    content=content_msg,
                                    embed=embed,
                                    view=ProposalView(title, urgency, description, brain, conversation_manager)
                                )
                                proposal_handled = True
                                
                                # Record history since we consumed 'reply'
                                if reply:
                                    conversation_manager.add_bot_message(message.channel.id, reply)
                                    
                            except Exception as e:
                                print(f"Failed to parse propose_ticket: {e}")
                                await message.channel.send("⚠️ I tried to propose a ticket but messed up the formatting. Please tell me the details again.")

                    # Reply (only if not already consumed by proposal)
                    if reply and not proposal_handled:
                        await message.channel.send(reply)
                        conversation_manager.add_bot_message(message.channel.id, reply)

if __name__ == "__main__":
    # --- Singleton Lock ---
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 45678))
        s.listen(1) # Make it visible to netstat
    except socket.error as e:
        print(f"❌ FATAL: Another instance is already running (Port 45678 locked).")
        sys.exit(1)
        
    # --- Environment Guardrail ---
    import sys
    is_dev = "--dev" in sys.argv
    hostname = socket.gethostname()
    
    # Production VM Hostname check (adjust if VM name is different, e.g. "bad-node-01")
    # If we are NOT on the VM and NOT in dev mode, stop.
    # Assuming VM name is "instance-20250114-192736" or similar, or we check for NOT "ControllerPC"
    # Safest is to require --dev if on Windows/ControllerPC
    
    if "Controller" in hostname and not is_dev:
        print("🛑 STARTUP BLOCKED: Production bot should not run locally on ControllerPC.")
        print("   Use --dev to override if you are testing.")
        sys.exit(1)

    if not TOKEN:
        print("❌ Error: Token not found.")
    else:
        print(f"🚀 Starting {BOT_NAME} on {hostname} (Dev Mode: {is_dev})")
        bot.run(TOKEN)
