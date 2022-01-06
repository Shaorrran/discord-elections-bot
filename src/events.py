"""
Bot event responses.
"""
import datetime

import discord
from discord.ext import commands

import src.db.db as db
import src.internals as internals
from src.db.db import ServersSettings

@internals.bot.event
async def on_ready():
    """
    Initialize presence and log server connections.
    Args: None
    Return value: None
    """
    await internals.bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name="election fraud")  # ha!
    )
    start_timestamp = datetime.datetime.now()
    print(f"Bot ready at: {start_timestamp}")
    for guild in internals.bot.guilds:
        guild_timestamp = datetime.datetime.now()
        print(
            f"{internals.bot.user} is connected to {guild.name} \
            (id: {guild.id}) at {guild_timestamp}"
        )

@internals.bot.event
async def on_guild_join(guild):
    """
    Activated on server join. Creates server settings storage and sets the prefix to default.
    Args: server object
    Return value: None
    """
    server = await ServersSettings.create(server_id=guild.id)
    server.prefixes = internals.DEFAULT_PREFIX
    await server.save()
    await guild.me.edit(username=f"[{internals.DEFAULT_PREFIX}]{bot.user.name}")

@internals.bot.event
async def on_guild_remove(guild):
    """
    Activated on server leave. Cleans up server settings.
    Args: server object
    Return value: None
    """
    server = await ServersSettings.filter(server_id=guild.id).first()
    await server.delete()

@internals.bot.event
async def on_command_error(ctx, error):
    """
    Commands errors handling.
    Args: error as type Exception
    Return value: None
    """
    if isinstance(error, commands.errors.MissingPermissions):
        await ctx.reply(
            "You lack \
        the required permissions for this command."
        )
        return
    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.reply("Command not found.")
        return
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        # dealt with in per-command error handlers
        return
    elif isinstance((error, commands.errors.CommandError):
        # dealt with in per-command error handlers
        return
    else:
        await ctx.reply(f"{error}")
        return
