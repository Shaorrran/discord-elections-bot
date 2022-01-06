"""
A cogs for miscellaneous commands (namely, `ping`)
"""
from discord.ext import commands

import src.internals as internals


class Technical(commands.Cog):
    """
    Technical commands
    """

    def __init__(self, bot):
        """
        Initialize the cog.
        Args: bot object
        Return value: None
        """
        self.bot = bot

    @commands.command(name="ping", help="Get bot latency")
    async def ping(self, ctx):
        """
        Get bot latency
        Args: None except context
        Return value: None
        """
        await ctx.send(f"Latency: {round(internals.bot.latency * 1000)} ms")

    @ping.error
    async def ping_error(self, ctx, error):
        await ctx.reply(f"{error}")
