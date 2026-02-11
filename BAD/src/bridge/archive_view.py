import discord
from discord.ext import commands
from src import db
import os
import math


class SearchModal(discord.ui.Modal, title="🔍 Search Tickets"):
    query = discord.ui.TextInput(label="Search Query", placeholder="Title, User, or Description...", max_length=100)

    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.parent_view.search_query = self.query.value
        self.parent_view.page = 0
        
        embed = await self.parent_view.generate_embed(interaction.guild)
        self.parent_view.update_components()
        await interaction.message.edit(embed=embed, view=self.parent_view)

class ArchiveDashboardView(discord.ui.View):
    def __init__(self, user_id, page=0, filter_status='all', sort_desc=True, show_all=False, search_query=None, filter_urgency=None):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.page = page
        self.filter_status = filter_status # 'all', 'closed', 'archived'
        self.sort_desc = sort_desc
        self.show_all = show_all # If True, shows all tickets (admin), else only user's
        self.search_query = search_query
        self.filter_urgency = filter_urgency
        
        self.items_per_page = 10
        self.total_pages = 1 # Will be updated
        
        self.update_components()

    def update_components(self):
        # Update buttons based on state
        for child in self.children:
             if isinstance(child, discord.ui.Button):
                 if child.custom_id == "prev_page":
                     child.disabled = (self.page == 0)
                 elif child.custom_id == "first_page":
                     child.disabled = (self.page == 0)
                 elif child.custom_id == "next_page":
                     child.disabled = (self.page >= self.total_pages - 1)
                 elif child.custom_id == "last_page":
                     child.disabled = (self.page >= self.total_pages - 1)
        
    async def generate_embed(self, guild):
        offset = self.page * self.items_per_page
        
        # Determine filters
        status_filter = ['closed', 'archived'] if self.filter_status == 'all' else [self.filter_status]
        user_filter = None if self.show_all else self.user_id
        
        tickets, total_count = db.get_tickets_with_filter(
            status=status_filter,
            user_id=user_filter,
            limit=self.items_per_page,
            offset=offset,
            sort_desc=self.sort_desc,
            search_query=self.search_query,
            urgency=self.filter_urgency
        )
        
        self.total_pages = math.ceil(total_count / self.items_per_page) if total_count > 0 else 1
        
        # Ensure page is valid
        if self.page >= self.total_pages:
             self.page = max(0, self.total_pages - 1)

        embed = discord.Embed(title="🗄️ Archive Dashboard", color=discord.Color.dark_grey())
        
        msg_parts = []
        msg_parts.append(f"Viewing **{'All Tickets' if self.show_all else 'My Tickets'}**")
        msg_parts.append(f"Sorted by **{'Newest' if self.sort_desc else 'Oldest'}**")
        
        filters = []
        if self.filter_status != 'all': filters.append(f"Status: {self.filter_status}")
        if self.filter_urgency: filters.append(f"Urgency: {self.filter_urgency}")
        if self.search_query: filters.append(f"Search: '{self.search_query}'")
        
        if filters:
            msg_parts.append(f"Filters: `{', '.join(filters)}`")
            
        embed.description = " • ".join(msg_parts) + f"\nTotal Found: **{total_count}**"
        
        if tickets:
            for t in tickets:
                user_name = t.get('user_name', 'Unknown')
                date_str = t.get('created_at', 'Unknown')
                title = t.get('title') or "No Title"
                status = t.get('status', 'closed')
                urgency = t.get('urgency', '')
                
                emoji = "🔒" if status == 'archived' else "📁"
                if urgency and ("High" in urgency or "Critical" in urgency):
                    emoji = "🔴"
                elif urgency and "Medium" in urgency:
                    emoji = "🟡"

                embed.add_field(
                    name=f"{emoji} #{t['id']} {title[:40]}",
                    value=f"👤 {user_name} | 📅 {date_str}\nStatus: `{status}` | Urgency: `{urgency if urgency else 'None'}`",
                    inline=False
                )
        else:
            embed.add_field(name="No tickets found", value="Try changing your filters or search query.", inline=False)
            
        embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")
        return embed

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.secondary, custom_id="first_page", row=0)
    async def first_conn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page = 0
            embed = await self.generate_embed(interaction.guild)
            self.update_components()
            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="prev_page", row=0)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            embed = await self.generate_embed(interaction.guild)
            self.update_components()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="next_page", row=0)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            embed = await self.generate_embed(interaction.guild)
            self.update_components()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.secondary, custom_id="last_page", row=0)
    async def last_conn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page = self.total_pages - 1
            embed = await self.generate_embed(interaction.guild)
            self.update_components()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔍 Search", style=discord.ButtonStyle.primary, custom_id="search_btn", row=1)
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModal(self))

    @discord.ui.select(
        placeholder="Filter / Sort Options",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Reset All Filters", value="reset", description="Clear all search and filters"),
            discord.SelectOption(label="Sort: Newest First", value="sort_new", description="Sort by date descending"),
            discord.SelectOption(label="Sort: Oldest First", value="sort_old", description="Sort by date ascending"),
            discord.SelectOption(label="Status: Closed Only", value="filter_closed", description="Show only closed (not archived)"),
            discord.SelectOption(label="Status: Archived Only", value="filter_archived", description="Show only fully archived"),
            discord.SelectOption(label="Urgency: High/Critical", value="filter_high", description="Show High/Critical urgency"),
            discord.SelectOption(label="Urgency: Medium", value="filter_medium", description="Show Medium urgency"),
            discord.SelectOption(label="View: All Tickets (Admin)", value="view_all", description="Show everyone's tickets"),
            discord.SelectOption(label="View: My Tickets", value="view_mine", description="Show only my tickets"),
        ],
        custom_id="archive_filter",
        row=2
    )
    async def filter_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        
        if val == "reset":
            self.search_query = None
            self.filter_urgency = None
            self.filter_status = 'all'
            self.sort_desc = True
            # Keep view_all/mine setting? Maybe reset to default behavior (mine unless admin forcing?)
            # Let's keep the current scope (mine/all) to avoid annoyance
        elif val == "sort_new":
            self.sort_desc = True
        elif val == "sort_old":
            self.sort_desc = False
        elif val == "filter_closed":
            self.filter_status = "closed"
        elif val == "filter_archived":
            self.filter_status = "archived"
        elif val == "filter_high":
            self.filter_urgency = "High" # Partial match logic in DB handles "High" vs "Cr_High" etc.
        elif val == "filter_medium":
            self.filter_urgency = "Medium"
        elif val == "view_all":
            self.show_all = True
        elif val == "view_mine":
            self.show_all = False
            
        self.page = 0
        embed = await self.generate_embed(interaction.guild)
        self.update_components()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔢 Select Ticket by ID", style=discord.ButtonStyle.secondary, custom_id="select_ticket_btn", row=1)
    async def select_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Open Modal to enter ID
        await interaction.response.send_modal(TicketLookupModal())

class TicketLookupModal(discord.ui.Modal, title="Lookup Ticket"):
    ticket_id = discord.ui.TextInput(label="Ticket ID", placeholder="e.g. 12", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            t_id = int(self.ticket_id.value)
            ticket = db.get_ticket_by_id(t_id)
            
            if not ticket:
                await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
                return
                
            # Check permission (User can only view own unless staff)
            # Simplified: For now, just show it. Ideally check permissions.
            
            view = TicketDetailsView(ticket)
            embed = view.generate_embed()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid ID format.", ephemeral=True)

class TicketDetailsView(discord.ui.View):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        self.ticket = ticket
        
    def generate_embed(self):
        t = self.ticket
        embed = discord.Embed(title=f"Ticket #{t['id']}: {t.get('title', 'No Title')}", color=discord.Color.blue())
        embed.description = t.get('description', 'No description.')
        embed.add_field(name="User", value=t.get('user_name', 'Unknown'), inline=True)
        embed.add_field(name="Status", value=t.get('status', 'Unknown'), inline=True)
        embed.add_field(name="Created", value=t.get('created_at', 'Unknown'), inline=True)
        embed.add_field(name="Closed", value=t.get('closed_at', 'Unknown'), inline=True)
        
        path = t.get('archive_path')
        if path:
            embed.set_footer(text=f"Archive Path: {path}")
        else:
            embed.set_footer(text="No local archive found.")
        return embed

    @discord.ui.button(label="📂 Download Transcript", style=discord.ButtonStyle.success)
    async def download_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        path = self.ticket.get('archive_path')
        if not path or not os.path.exists(path):
             await interaction.response.send_message("❌ No archive files found for this ticket.", ephemeral=True)
             return
             
        html_path = os.path.join(path, "transcript.html")
        if os.path.exists(html_path):
            await interaction.response.send_message(
                content=f"📂 Transcript for Ticket #{self.ticket['id']}",
                file=discord.File(html_path, filename=f"ticket-{self.ticket['id']}-transcript.html"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Transcript HTML file missing.", ephemeral=True)

    @discord.ui.button(label="🔄 Restore (Create Copy)", style=discord.ButtonStyle.secondary)
    async def restore_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bridge import archiver
        await interaction.response.defer(ephemeral=True)
        
        res = await archiver.restore_ticket_from_archive(interaction, self.ticket['id'])
        
        if isinstance(res, str): # Error message
             await interaction.followup.send(res, ephemeral=True)
        else:
             await interaction.followup.send(f"✅ Ticket restored: {res.mention}", ephemeral=True)
