"""
God mode commands.
"""

from discord.ext import commands
import src.internals as internals
import src.db.db as db

class God(commands.Cog):
    """
    God mode commands Cog.
    """
    def __init__(self, bot):
        self.bot = bot
    
    @commands.is_owner()
    @commands.command(name="halt-and-catch-fire", help="The bot explodes.")
    async def halt_and_catch_fire(self, ctx):
        await db.db_cleanup()
        god = (await internals.bot.application_info()).owner
        await internals.bot.close()
        print(f"Successfully caught fire via override from {god}.")