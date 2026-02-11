import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import asyncio
import json
import sys
import os
import socket # Added for Singleton Lock
from collections import deque

# --- Singleton Lock ---
# prevents multiple instances from running
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 45678))
except socket.error as e:
    print(f"❌ FATAL: Another instance is already running (Port 45678 locked).")
    sys.exit(1)

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

# --- Views ---

class ProposalView(discord.ui.View):
    def __init__(self, title, urgency, description):
        super().__init__(timeout=None)
        self.title = title
        self.urgency = urgency
        self.description = description

    @discord.ui.button(label="✅ Approve & Submit", style=discord.ButtonStyle.green, custom_id="submit_ticket_btn")
    async def submit_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        channel = interaction.channel
        guild = interaction.guild
        
        # 1. Move to Manager Inbox
        category = guild.get_channel(MANAGER_INBOX_ID)
        if not category:
             category = discord.utils.get(guild.categories, name="Manager Inbox")
        
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
        
        await channel.send(f"📨 **Ticket Submitted!** {mention} A new ticket is ready for review.", embed=embed)
        
        # 4. Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
    @discord.ui.button(label="📝 Add/Refine Info", style=discord.ButtonStyle.secondary, custom_id="edit_ticket_btn")
    async def edit_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("To edit, simply type what you want to change in the chat (e.g. 'Change context to...').", ephemeral=True)

    @discord.ui.button(label="🗑️ Abandon", style=discord.ButtonStyle.danger, custom_id="abandon_ticket_btn")
    async def abandon_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Abandoning ticket and deleting channel...", ephemeral=True)
        await asyncio.sleep(1)
        await interaction.channel.delete()

class InterviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Keeping this for backward compatibility if needed, using ProposalView for new flow

class NewTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🗑️ Discard Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_assistant:discard_new")
    async def discard_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Discarding ticket...", ephemeral=True)
        try:
            await interaction.channel.delete()
        except Exception as e:
            await interaction.followup.send(f"❌ Error discarding ticket: {e}", ephemeral=True)

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
            channel_name = f"incoming-{user.name}"
            channel = await guild.create_text_channel(channel_name, category=None, position=0, overwrites=overwrites)
            
            # Start Conversation
            if conversation_manager:
                conversation_manager.start_new_conversation(channel.id)
                
                # [NEW] Send Control Panel + Greeting Atomic
                greeting = "Hello! I am your Ticket Assistant. How can I help you today?"
                embed = discord.Embed(title="Ticket Controls", description="Use the button below to discard this ticket if created by mistake.", color=discord.Color.red())
                
                await channel.send(content=greeting, embed=embed, view=NewTicketView())
                conversation_manager.add_bot_message(channel.id, greeting)
            
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

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} is online (v2.0 - Active Ticket Workflow)')
    print(f'   ID: {bot.user.id}')
    
    # Register Persistent Views
    bot.add_view(TicketView())
    bot.add_view(NewTicketView())
    bot.add_view(ProposalView("", "", "")) # Register class, arguments don't matter for persistence check
    print(f'   Ticket Views Registered.')

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

@bot.command(name='setup_tickets')
async def setup_tickets(ctx):
    """Deploys the Ticket Creation Panel to the current channel."""
    embed = discord.Embed(
        title="📬 Support Tickets",
        description="Click the button below to open a private ticket with the staff.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete() # cleanup command

@bot.command(name='assign')
async def assign_ticket(ctx, member: discord.Member):
    """Assigns a member to the current ticket channel."""
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
        await ctx.send("⚠️ This command only works in ticket channels.")
        return

    await ctx.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
    await ctx.send(f"✅ {member.mention} has been assigned to this ticket.")

@bot.command(name='add')
async def add_helper(ctx, member: discord.Member):
    """Alias for assign."""
    await assign_ticket(ctx, member)

@bot.command(name='escalate')
async def escalate_ticket(ctx, member: discord.Member):
    """Escalates the ticket to a specific member (adds them)."""
    # In future we could move the ticket to a 'High Priority' category
    await assign_ticket(ctx, member)
    await ctx.send(f"🚨 Ticket escalated to {member.mention}.")

@bot.command(name='abandon')
async def abandon_ticket_cmd(ctx):
    """Abandons and deletes the current ticket channel."""
    if not (ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("incoming-")):
        return
    
    await ctx.send("🗑️ Abandoning ticket...")
    await asyncio.sleep(2)
    await ctx.channel.delete()

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
                
                # Execute Actions
                for action in actions:
                    if "close_ticket" in action:
                        await message.channel.send("🔒 Closing ticket as requested...")
                        # In a real scenario, we might want to archive it properly
                        await message.channel.delete() 
                        return # Stop processing
                    
                    if "propose_ticket" in action:
                        # Parse: propose_ticket | Title | Urgency | Desc
                        try:
                            parts = action.split("|")
                            # parts[0] is 'propose_ticket '
                            title = parts[1].strip()
                            urgency = parts[2].strip()
                            description = parts[3].strip()
                            
                            embed = discord.Embed(title="📋 Ticket Proposal", color=discord.Color.gold())
                            embed.add_field(name="Title", value=title, inline=False)
                            embed.add_field(name="Urgency", value=urgency, inline=True)
                            embed.add_field(name="Description", value=description, inline=False)
                            
                            await message.channel.send(
                                content="I have prepared this ticket based on our conversation. Is this correct?",
                                embed=embed,
                                view=ProposalView(title, urgency, description)
                            )
                        except Exception as e:
                            print(f"Failed to parse propose_ticket: {e}")
                            await message.channel.send("⚠️ I tried to propose a ticket but messed up the formatting. Please tell me the details again.")

                # Reply
                reply = thought.get("reply", "")
                if reply:
                    await message.channel.send(reply)
                    conversation_manager.add_bot_message(message.channel.id, reply)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: Token not found.")
    else:
        bot.run(TOKEN)
