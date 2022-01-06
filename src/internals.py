"""
Internal definitions and global vars.
"""
import os
import typing as tp

import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

import src.db.db as db

import src.cogs.servers_settings as servers_settings
import src.cogs.technical as technical
import src.cogs.voting as voting
import src.cogs.god as god

load_dotenv()  # export the vars from .env as environ vars
TOKEN = os.getenv("BOT_TOKEN")  # because, you know, it's supposed to be *secret*
IN_MEMORY_DB = os.getenv("IN_MEMORY_DB")  # whether we store the database in memory or in a file
DEFAULT_PREFIX = "!"

async def init_db():
    """
    Initialize database connection.
    Args: none
    Return value: None
    """
    await db.init(in_memory=bool(IN_MEMORY_DB))

asyncio.run(init_db())

async def get_prefix(bot: commands.bot, message: tp.Any) -> tp.Any:
    """
    Get the bot prefix.
    """
    prefixes = await servers_settings.ServersSettings().filter(server_id=message.guild.id).first().split(",")

    return commands.bot.when_mentioned_or(*prefixes)(bot, message)

bot_intents = discord.Intents.default()
bot_intents.members = True
bot_intents.reactions = True
bot = commands.Bot(command_prefix=get_prefix, intents=bot_intents)
del bot_intents
bot.add_cog(voting.Voting(bot))
bot.add_cog(technical.Technical(bot))
bot.add_cog(servers_settings.Settings(bot))
bot.add_cog(god.God(bot))