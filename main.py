"""
Main runner for Discord bot.
"""
import asyncio

import src.db.db as db
import src.events as events  # do not touch, removing this import disables the events defined in that file
import src.internals as internals

asyncio.run(internals.init_db())

internals.bot.run(internals.TOKEN)