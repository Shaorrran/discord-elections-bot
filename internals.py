"""
Internal definitions and global vars
"""
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # export the vars from .env as environ vars
TOKEN = os.getenv("BOT_TOKEN")  # because, you know, it's supposed to be *secret*
LOGFILE = os.getenv("LOGFILE")
ELECTIONS_DIR = os.getenv("ELECTIONS_DIR")
VOTERS_DIR = os.getenv("VOTERS_DIR")
# CONFIGS_DIR = os.getenv("CONFIGS_DIR")

bot_intents = discord.Intents.default()
bot_intents.members = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(">"), intents=bot_intents
)  # ugly, see TODO in main
