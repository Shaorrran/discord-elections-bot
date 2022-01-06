"""
Internal definitions and global vars.
"""
import os
import typing as tp

import discord
from discord.ext import commands
from dotenv import load_dotenv

import src.cogs.servers_settings as servers_settings
import src.cogs.technical as technical
import src.cogs.voting as voting
import src.cogs.god as god

load_dotenv()  # export the vars from .env as environ vars
TOKEN = os.getenv("BOT_TOKEN")  # because, you know, it's supposed to be *secret*
IN_MEMORY_DB = os.getenv("IN_MEMORY_DB")  # whether we store the database in memory or in a file

def get_prefix(bot: commands.bot, message: str) -> tp.Any:
    """
    Get the bot prefix. Mostly required to make the bot respond only to a mention.
    """
    return commands.when_mentioned(bot, message)

bot_intents = discord.Intents.default()
bot_intents.members = True
bot_intents.reactions = True
bot = commands.Bot(command_prefix=get_prefix, intents=bot_intents)
del bot_intents
bot.add_cog(voting.Voting(bot))
bot.add_cog(technical.Technical(bot))
bot.add_cog(servers_settings.Settings(bot))
bot.add_cog(god.God(bot))