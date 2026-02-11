
import discord
from discord.ui import View, Select, Button
import src.db as db
from datetime import datetime

class UnifiedDashboardView(View):
    def __init__(self, user, create_ticket_callback=None):
        super().__init__(timeout=None)
        self.user = user
        self.create_ticket_callback = create_ticket_callback
        self.current_role = "User" # Default
        
        # Check roles (Case insensitive check for robustness)
        role_names = [role.name.lower() for role in user.roles]
        
        # Check if user is owner
        is_owner = False
        if hasattr(user, "guild") and user.guild:
             is_owner = (user.id == user.guild.owner_id)

        self.is_staff = is_owner or any(r in ["staff", "support", "admin", "moderator", "ticketmanager", "developer"] for r in role_names)
        self.is_manager = is_owner or any(r in ["manager", "admin", "owner", "head", "ticketmanager", "developer"] for r in role_names)
        
        # Default to highest role
        if self.is_manager:
            self.current_role = "Manager"
        elif self.is_staff:
            self.current_role = "Helper"
            
        self.update_components()

    def update_components(self):
        self.clear_items()
        
        # 1. Role Switcher Select
        options = [discord.SelectOption(label="User View", value="User", emoji="👤", default=(self.current_role=="User"))]
        
        if self.is_staff:
            options.append(discord.SelectOption(label="Helper View", value="Helper", emoji="🛠️", default=(self.current_role=="Helper")))
        
        if self.is_manager:
            options.append(discord.SelectOption(label="Manager View", value="Manager", emoji="📊", default=(self.current_role=="Manager")))
            
        # Only show switcher if they have at least one other role
        if len(options) > 1:
            select = discord.ui.Select(
                placeholder=f"Current View: {self.current_role}",
                options=options,
                min_values=1, max_values=1,
                custom_id="dashboard_role_switch"
            )
            select.callback = self.switch_role_callback
            self.add_item(select)
        
        # 2. Context Specific Buttons
        if self.current_role == "User":
            # Action: Create Ticket
            btn = discord.ui.Button(label="📩 Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_btn")
            if self.create_ticket_callback:
                btn.callback = self.create_ticket_callback
            self.add_item(btn)
            
            # Action: My History
            # self.add_item(discord.ui.Button(label="📜 History", style=discord.ButtonStyle.secondary, custom_id="dash_user_history"))

        elif self.current_role == "Helper":
            # Action: Refresh
            self.add_item(discord.ui.Button(label="🔄 Refresh Queue", style=discord.ButtonStyle.primary, custom_id="dashboard_refresh"))
            
        elif self.current_role == "Manager":
            # Action: Refresh
            self.add_item(discord.ui.Button(label="🔄 Refresh Stats", style=discord.ButtonStyle.primary, custom_id="dashboard_refresh"))

    async def switch_role_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_role = interaction.data['values'][0]
        self.update_components()
        embed = await self.generate_embed(interaction.guild)
        await interaction.message.edit(embed=embed, view=self)

    async def generate_embed(self, guild):
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_footer(text=f"Viewing as {self.current_role} • {datetime.now().strftime('%H:%M')}")

        if self.current_role == "User":
            embed.title = f"👤 User Dashboard: {self.user.display_name}"
            tickets = db.get_user_tickets(self.user.id)
            active_tickets = [t for t in tickets if t['status'] not in ['closed', 'archived']]
            
            if active_tickets:
                desc = "**Your Active Tickets:**\n"
                for t in active_tickets:
                    # Resolve channel
                    channel = guild.get_channel(int(t['channel_id'])) if t['channel_id'] else None
                    if channel:
                        link = f"[{channel.name}]({channel.jump_url})"
                    else:
                        link = f"#{t['id']}"
                    
                    desc += f"• {link} - {t['title'] or 'No Title'} ({t['status']})\n"
                embed.description = desc
            else:
                embed.description = "You have no active tickets.\nNeed help? Click **Create Ticket** below."
                
        elif self.current_role == "Helper":
            embed.title = "🛠️ Helper Dashboard"
            embed.color = discord.Color.orange()
            
            # 1. Unassigned Queue
            unassigned = db.get_unassigned_tickets(limit=5)
            queue_str = ""
            if unassigned:
                for t in unassigned:
                    channel = guild.get_channel(int(t['channel_id'])) if t['channel_id'] else None
                    if channel:
                        queue_str += f"**#{t['id']}** {channel.mention} \n└ 🕒 {t['created_at']} | 🚨 {t['urgency'] or 'None'}\n"
            else:
                queue_str = "✅ Queue is clear!"
                
            embed.add_field(name="📨 Unassigned Queue (Oldest)", value=queue_str, inline=False)
            
            # 2. My Assignments
            my_tickets = db.get_assigned_tickets(self.user.id)
            mined_str = ""
            if my_tickets:
                for t in my_tickets[:5]:
                    channel = guild.get_channel(int(t['channel_id'])) if t['channel_id'] else None
                    link = channel.mention if channel else f"#{t['id']}"
                    title_str = t['title'] or 'No Title'
                    mined_str += f"• {link} - {title_str}\n"
            else:
                mined_str = "You have no active tickets assigned."
                
            embed.add_field(name="👷 Must Do (Assigned to You)", value=mined_str, inline=False)

        elif self.current_role == "Manager":
            embed.title = "📊 Manager Command Center"
            embed.color = discord.Color.dark_theme()
            
            stats = db.get_ticket_stats()
            
            embed.description = (
                f"**Overview**\n"
                f"Total Open: `{stats['total_open']}`\n"
                f"Unassigned: `{stats['unassigned']}`\n"
                f"Urgent/High: `{stats['urgent']}`"
            )
            
            # Urgent List
            tickets = stats['active_list']
            urgent_list = [t for t in tickets if t['urgency'] and ('high' in t['urgency'].lower() or '10' in t['urgency'])]
            
            urgent_str = ""
            if urgent_list:
                for t in urgent_list[:5]:
                     channel = guild.get_channel(int(t['channel_id'])) if t['channel_id'] else None
                     assigned = t['assigned_to'] or "Unassigned"
                     # If assigned, resolve name? Expensive loop? 
                     # Let's just show ID or "Assigned"
                     link = channel.mention if channel else f"#{t['id']}"
                     urgent_str += f"• {link} ({assigned})\n"
            else:
                urgent_str = "No urgent tickets."
                
            embed.add_field(name="🔥 High Priority / Urgent", value=urgent_str, inline=False)
            
        return embed
