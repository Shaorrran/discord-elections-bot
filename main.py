"""
Main runner for Discord bot.
"""

import src.db.db as db
import src.events as events  # do not touch, removing this import disables the events defined in that file
import src.internals as internals

internals.bot.run(internals.TOKEN)
