"""
A cogs for miscellaneous commands (namely, `ping`)
"""
from discord.ext import commands

import src.internals as internals


class Technical(commands.Cog):
    """
    Techical commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", help="Get bot latency")
    async def ping(self, ctx):
        """
        Get bot latency
        Args: None except context
        Return value: None
        """
        await ctx.send(f"Latency: {round(internals.bot.latency * 1000)} ms")
