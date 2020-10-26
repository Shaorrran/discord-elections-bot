"""
Main runner for Discord bot
"""
import helpers
import internals

# TODO:
#   0. Make a class with the bot instance inside and toss it around
#   1. Make a global config file(for storing directory structure)?
#   2. Make guild-specific configs for storing moderator roles/command prefixes?/election channels
#   3. Implement moderator role storage/retrieval for guilds and use those roles for mod commands
#   4. Implement multiple elections in same guild
#   5. Check for bots voting/being candidates (no one wants a machine as President, right?)
#   6. Create a separate init block for creating dirs/reading configs/readying bot?
#   7. (See 0) Access the files more efficiently without opening/closing them all the time?
#   8. (See 0) Group globals into the class (because leaving a TOKEN var in globals is not nice)
#   9. Maybe make the bot accept only mentions as command prefixes, if that's possible?
#   10. Make add_candidates mention all existing candidates on "candidate already registered" error?
#   11. Update get_mention_by_id to make it return correct user/role/channel mentions
#   12. Implement elections that require roles (Electoral College, lol)

helpers.set_dir_structure()  # creates necessary directories
# This doesn't look good

internals.bot.run(internals.TOKEN)
