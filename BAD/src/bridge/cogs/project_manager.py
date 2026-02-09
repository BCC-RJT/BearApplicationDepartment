import discord
from discord.ext import commands
import asyncio
import json

class ProjectManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets = {} # {channel_id: {"state": "...", "history": []}}

    # Listener removed to prevent BADbot from auto-joining tickets
    # @commands.Cog.listener()
    # async def on_guild_channel_create(self, channel):
    #     pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channel_id = message.channel.id
        
        # Check if this is a ticket channel even if we missed the create event (e.g. restart)
        if channel_id not in self.tickets and message.channel.name.startswith("ticket-"):
             self.tickets[channel_id] = {"state": "INIT", "history": []}

        if channel_id not in self.tickets:
            return

        ticket = self.tickets[channel_id]
        state = ticket["state"]
        content = message.content.strip()

        if state == "INIT":
            if "plan" in content.lower() and "project" in content.lower():
                ticket["state"] = "GATHERING"
                await message.channel.send("Awesome! 🚀 **Tell me about the project.**\n\nWhat are we building? Who is it for? Any specific tech stack?\n\n(Type **'Generate Plan'** when you are done describing it.)")

        elif state == "GATHERING":
            if "generate plan" in content.lower():
                ticket["state"] = "PLANNING"
                await self.generate_project_plan(message.channel)
            else:
                ticket["history"].append(f"User: {content}")

        elif state == "REVIEW":
            if "approve" in content.lower():
                ticket["state"] = "APPROVED"
                await self.create_project_structures(message.channel)
            elif "refine" in content.lower():
                ticket["state"] = "GATHERING"
                await message.channel.send("Okay, what else should I know?")

    async def generate_project_plan(self, channel):
        ticket = self.tickets[channel.id]
        history = ticket["history"]
        
        await channel.send("🧠 **Thinking...** Drafting a master plan.")
        
        user_request = "\n".join(history)
        
        try:
            if not hasattr(self.bot, 'brain') or not self.bot.brain:
                await channel.send("❌ Error: My Brain is missing.")
                return

            response = await self.bot.brain.think(
                user_message=f"Create a comprehensive implementation plan for this project request:\n{user_request}",
                available_actions={},
                history=[],
                mode="architect"
            )
            
            reply = response.get("reply", "No plan generated.")
            
            # Simple chunking
            if len(reply) > 2000:
                for i in range(0, len(reply), 2000):
                    await channel.send(reply[i:i+2000])
            else:
                await channel.send(reply)
            
            embed = discord.Embed(
                title="✅ Approve Plan?",
                description="Type **'Approve'** to create channels.\nType **'Refine'** to add more details.",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
            ticket["state"] = "REVIEW"
                
        except Exception as e:
            await channel.send(f"❌ Planning failed: {e}")
            ticket["state"] = "GATHERING"

    async def create_project_structures(self, channel):
        guild = channel.guild
        try:
            # Simple check for project name in history or ask Brain to name it
            # For now, let's use the ticket name or ask user. 
            # To accept user input for name would require another state.
            # Let's just default to "New Project" + Timestamp or last message?
            # Better: Ask Brain to extract a name.
            
            project_name = f"Project-{channel.name}" 
            
            category = await guild.create_category(project_name)
            await guild.create_text_channel("discussion", category=category)
            await guild.create_text_channel("tasks", category=category)
            await guild.create_text_channel("docs", category=category)
            
            await channel.send(f"🚀 **{project_name}** initialized! Check the new category.")
        except Exception as e:
            await channel.send(f"❌ Creation failed: {e}")

async def setup(bot):
    await bot.add_cog(ProjectManager(bot))
