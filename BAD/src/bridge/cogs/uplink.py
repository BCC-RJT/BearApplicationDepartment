import discord
from discord.ext import commands, tasks
import os
import io
import socket
import platform
import datetime

class UplinkCog(commands.Cog, name="Antigravity Uplink"):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = int(os.getenv('ANTIGRAVITY_CHANNEL_ID', '0'))
        self.webhook_url = os.getenv('ANTIGRAVITY_WEBHOOK_URL')
        self.hostname = socket.gethostname()
        self.uplink.start() # Start the heartbeat loop

    def cog_unload(self):
        self.uplink.stop()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"📡 Uplink System Online: {self.hostname}")
        # Initial Announcement
        await self.announce_presence("🟢 Online / Ready")

    async def announce_presence(self, status_text):
        if not self.channel_id:
            return

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            # Try fetching if not in cache
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except:
                print(f"⚠️ Uplink Channel {self.channel_id} not found.")
                return

        embed = discord.Embed(
            title=f"📡 Node Signal: {self.hostname}",
            description=status_text,
            color=discord.Color.green() if "Online" in status_text else discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Identity", value=self.bot.user.name, inline=True)
        embed.add_field(name="IP/Host", value=self.hostname, inline=True)
        
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Failed to send uplink signal: {e}")

    @tasks.loop(minutes=5)
    async def uplink(self):
        """Heartbeat Cycle (Breathing)"""
        if not self.channel_id:
            return
            
        print("🫀 Uplink Heartbeat (Breathing Cycle)...")
        # We don't want to spam the channel with full embeds every 5 mins.
        # Maybe just edit a status message or send a small log?
        # For now, let's just log locally and maybe send a lightweight ping every hour?
        # Or checking for commands.
        
        # User requested "communicate with each other... and collaborate".
        # For now, the heartbeat is internal. 
        # But let's send a ping every 30 minutes (iteration 6).
        if self.uplink.current_loop > 0 and self.uplink.current_loop % 6 == 0:
             await self.announce_presence(f"❤️ System Healthy | Latency: {round(self.bot.latency * 1000)}ms")

    @uplink.before_loop
    async def before_uplink(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(UplinkCog(bot))
