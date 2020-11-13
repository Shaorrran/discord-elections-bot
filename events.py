"""
Bot event responses
"""
import datetime

import discord
from discord.ext import commands

import internals


@internals.bot.event
async def on_ready():  # gets called when the bot is finished connecting to guilds
    """
    Initialize presence and log server connections
    Args: None
    Return value: None
    """
    await internals.bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing, name="election fraud"
        )  # ha!
    )
    with open(internals.LOGFILE, "a", encoding="utf-8") as logfile:
        start_timestamp = datetime.datetime.now()
        logfile.write(f"Bot ready at: {start_timestamp}\n")
        print(f"Bot ready at: {start_timestamp}")
        for guild in internals.bot.guilds:
            guild_timestamp = datetime.datetime.now()
            logfile.write(
                f"{internals.bot.user} is connected to {guild.name} (id: {guild.id}) at {guild_timestamp}\n"
            )
            print(
                f"{internals.bot.user} is connected to {guild.name} (id: {guild.id}) at {guild_timestamp}"
            )


@internals.bot.event
async def on_command_error(ctx, error):
    """
    Commands' errors handling
    Args: error as type Exception
    Return value: None
    """
    if isinstance(error, commands.errors.MissingPermissions):
        await ctx.send(f"You lack the required permissions for this command.")
        # Never actually detected to be called since unprivileged users do not see the privileged commands
        # delete?
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f"Command not found!")
    else:
        await ctx.send(f"{error}")
