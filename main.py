import datetime
import os
import string
import typing

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # export the vars from .env as environ vars
TOKEN = os.getenv("BOT_TOKEN")  # because, you know, it's supposed to be *secret*

LOGFILE = "logs/bot.log"  # ugly, see TODO

bot_intents = discord.Intents.default()
bot_intents.members = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(">"), intents=bot_intents
)  # ugly, see TODO


# TODO:
#   0. Make a class with the bot instance inside and toss it around
#   1. Group helper functions and commands together into separate files
#   2. Make a global config file(for storing directory structure)?
#   3. Make guild-specific configs for storing moderator roles/command prefixes?/election channels
#   4. Implement moderator role storage/retrieval for guilds and use those roles for mod commands
#   5. Implement multiple elections in same guild
#   6. Check for bots voting/being candidates (no one wants a machine as President, right?)
#   7. Create a separate init block for creating dirs/reading configs/readying bot?
#   8. (See 0) Access the files more efficiently without opening/closing them all the time?
#   9. (See 0) Group globals into the class (because leaving a TOKEN var in globals is not nice, y'know)
#   10. Maybe make the bot accept only mentions as command prefixes, if that's possible?
#   11. Make add_candidates mention all existing candidates on "candidate already registered" error?
#   12. Update get_mention_by_id to make it return correct user/role/channel mentions
#   13. Implement elections that require roles (Electoral College, lol)


def set_dir_structure():
    """
    Create the necessary directories for the bot to function
    Args: none
    Return value: None
    """
    # create logs dir if none exists. See TODO #2
    if not os.path.isdir("./logs"):
        os.mkdir("./logs")
        timestamp = datetime.datetime.now()
        with open(LOGFILE, "a", encoding="utf-8") as logfile:
            logfile.write(f"Created logfile and logs dir at {timestamp}\n")
            print(f"Created logfile and logs dir at {timestamp}")
    # create elections dir if none exists. See TODO #2
    if not os.path.isdir("elections"):
        os.mkdir("./elections")
        timestamp = datetime.datetime.now()
        with open(LOGFILE, "a", encoding="utf-8") as logfile:
            logfile.write(f"Created elections dir at {timestamp}\n")
            print(f"Created elections dir at {timestamp}")
    # create voters dir if none exists. See TODO #2
    if not os.path.isdir("voters"):
        os.mkdir("./voters")
        timestamp = datetime.datetime.now()
        with open(LOGFILE, "a", encoding="utf-8") as logfile:
            logfile.write(f"Created voters dir at {timestamp}\n")
            print(f"Created voters dir at {timestamp}")


async def get_mention_type(mention: str) -> str:
    """
    Get mention type by mention
    Mentions in Discord have a <@user_id> format or <@!user_id> if the user has a guild-specific nickname,
    or <@&role_id> for role mentions, or <@#channel_id> for channel mentions
    Args: mention of type str
    Return value: one of the strings "user", "channel", "role", "undef"
    """
    # Mentions in Discord have a <@user_id> format or <@!user_id> if the user has a guild-specific nickname,
    # or <@&role_id> for role mentions, or <@#channel_id> for channel mentions
    mention = str(mention)
    if mention.startswith("<@") and mention.endswith(">"):  # user mention
        return "user"
    if mention.startswith("<@!") and mention.endswith(">"):  # user mention by guild-specific name
        return "user"
    if mention.startswith("<#") and mention.endswith(">"):  # channel mention
        return "channel"
    if mention.startswith("<@&") and mention.endswith(">"):  # role mention
        return "role"

    return "undef"


async def get_id_by_mention(mention: str) -> int:
    """
    Get id from mention
    Args: mention of type str
    Return value: id of type int
    """
    if mention.startswith("<@") and mention.endswith(">"):
        mention = mention[2:-1]  # delete these chars
    if mention.startswith("!"):
        mention = mention[1:]  # delete the char
    if mention.startswith("&"):
        mention = mention[1:]
    if mention.startswith("<#") and mention.endswith(">"):
        mention = mention[1:-1]

    # Note: maybe use regex?
    return int(mention)  # otherwise the methods fail


async def get_user_mention_by_id(identifier: str) -> str:
    """
    Wrapper for user.mention checking for mention type
    Args: id of type str
    Return value: mention of type str
    """
    # user mentions only for now
    user = bot.get_user(
        int(identifier)
    )  # explicit cast required to avoid illegal argument exceptions
    if not await get_mention_type(user.mention) == "user":
        raise commands.errors.BadArgument(
            "Please check if you are mentioning a role/channel, only users are supported! in get user mention by id"
        )
    return user.mention  # automatically constructs a mention


async def write_to_file(filename: str, content: str):
    """
    Writes a string to file
    Args: filename as type str, content as type str
    Return value: None
    """
    with open(f"{filename}", "a", encoding="utf-8") as f:
        f.write(content)


async def remove_line_from_file(filename: str, content: str):
    """
    Removes a line from file
    Args: filename as type str, content as type str
    Return value: None
    """
    with open(f"{filename}", "r+", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if content in line:
                lines.remove(line)
        f.seek(0)
        f.truncate()
        # we just deleted everything from the file
        for line in lines:
            await write_to_file(filename, line + "\n")


async def get_mention_ids(mentions: typing.List[str]) -> typing.List[str]:
    """
    Get a list of ids from a list of mentions
    Args: mentions of type List[str]
    Return value: ids of type List[str]
    """
    # user mentions only for now
    result = []
    for mention in mentions:
        if await get_mention_type(mention) != "user":
            raise commands.errors.UserInputError(
                "Please, check if you are mentioning a role/channel, only users are supported!"
            )
        result.append(await get_id_by_mention(mention))

    return result


async def is_string_in_file(filename: str, s: str) -> bool:
    """
    Check if a current string is present in a file
    Args: filename as type str, s as type str
    Return value: True if a string exists, False otherwise
    """
    with open(f"{filename}", "r", encoding="utf-8") as f:
        if s in f.read():
            return True

    return False


async def get_file_info(filename: str) -> typing.Dict[int, int]:
    """
    Gets user id's and respective values from a file(ignores empty lines and comments)
    Args: filename as type str
    Return value: file_info as type Dict[int, int]
    """
    file_info = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.startswith("#"):  # discard comments and trailing newline
                continue
            if line.startswith("Rewarded roles:"):  # discard rewarded roles
                continue
            if line.startswith("\n"):
                continue
            user, value = line.split()  # default split uses whitespace as separator, which suits us
            file_info[int(user)] = int(value)  # explicit casts to int

    return file_info


async def add_vote(filename: str, candidate: str):
    """
    Adds a vote to an file, i. e increments the corresponding candidates' vote value
    Args: filename as type str, candidate as type str
    Return value: None
    """
    file_info = await get_file_info(filename)
    if candidate in file_info:
        candidate = str(candidate)
        with open(filename, "r+", encoding="utf-8") as f:
            lines = f.readlines()
            new_lines = []
            for line in lines:
                if line.startswith("#"):  # discard comments and trailing newline
                    new_lines.append(line)
                    continue
                if line.startswith("Rewarded roles:"):  # ignore reward roles
                    new_lines.append(line)
                    continue
                if line.startswith("\n"):  # discard trailing newlines
                    continue
                user, value = line.split()
                if candidate == user:
                    line = user + " " + str(int(value) + 1)  # very bad, but should work
                new_lines.append(line)
            del lines
            f.seek(0)
            f.truncate()
            # we just deleted everything from the file
            for line in new_lines:
                await write_to_file(filename, line + "\n")
    else:
        raise commands.errors.UserInputError("No such candidate!")


async def get_reward_roles(filename: str) -> typing.List[int]:
    roles = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.startswith("Rewarded roles:"):  # add rewarded roles
                line_content = line.split()
                line_content = line_content[2:]  # delete "Rewarded roles"
                roles.append(line_content)

    roles = [int(j) for i in roles for j in i]  # flatten the list and cast to int

    return roles


@bot.command(name="init-election", help="Starts an election")
@commands.has_guild_permissions(manage_guild=True)
async def init_election(ctx, *args):
    """
    Initiates an election in a given server (from context). Requires "Manage Server" permissions
    Args: User mentions, separated by a space
    Return value: None
    """
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    voters_base_name = "voters/voters_" + str(ctx.guild.id)  # explicit cast required
    timestamp = datetime.datetime.now()
    if os.path.isfile(election_name) or os.path.isfile(voters_base_name):
        raise commands.errors.UserInputError("An election is already in progress on this server!")
    if len(args) == 0:
        raise commands.errors.UserInputError("At least one candidate required!")
    # Checking for existing candidates is not required as the file is guaranteed to be empty
    await write_to_file(
        voters_base_name,
        f"# Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )
    await write_to_file(
        election_name,
        f"# Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )
    mentions = await get_mention_ids(args)
    for mention in mentions:
        s = str(mention) + " " + "0\n"
        await write_to_file(election_name, s)  # initialize candidate and set votes count to 0
    await ctx.send("Election initiated!")
    print(f"Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}")
    await write_to_file(
        LOGFILE,
        f"Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )


@bot.command(name="add-candidates", help="Adds candidates to the current election")
@commands.has_guild_permissions(manage_guild=True)
async def add_candidates(ctx, *args):
    """
    Adds candidates to a current election. Requires "Manage Server" permissions
    Args: User mentions, separated by a space
    Return value: None
    """
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    timestamp = datetime.datetime.now()
    if not os.path.isfile(election_name):
        raise commands.errors.UserInputError("No election is in progress in current server!")
    if len(args) == 0:
        raise commands.errors.UserInputError("No candidates supplied!")
    mentions = await get_mention_ids(args)
    for mention in mentions:
        if await is_string_in_file(
            election_name, str(mention)
        ):  # Don't allow a candidate to occupy two positions at once
            # BUG: if role has the same name as the user, the command will fail
            raise commands.errors.UserInputError(
                f"Candidate {await get_user_mention_by_id(int(mention))} is already registered!"
            )
        s = str(mention) + " " + "0\n"
        await write_to_file(election_name, s)  # initialize candidate and set votes count to 0

    await ctx.send("Added new candidates to current election!")
    print(f"Added candidates to election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}")
    await write_to_file(
        LOGFILE,
        f"Added new candidates to election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )


@bot.command(name="remove-candidates", help="Remove candidates from the election")
@commands.has_guild_permissions(manage_guild=True)
async def remove_candidates(ctx, *args):
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    timestamp = datetime.datetime.now()
    if not os.path.isfile(election_name):
        raise commands.errors.UserInputError("No election is in progress in current server!")
    if len(args) == 0:
        raise commands.errors.UserInputError("No candidates supplied!")
    mentions = await get_mention_ids(args)
    for mention in mentions:
        if await is_string_in_file(election_name, str(mention)):
            await remove_line_from_file(election_name, str(mention))

    await ctx.send("Removed candidates from current election!")
    print(
        f"Removed candidates from election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}"
    )
    await write_to_file(
        LOGFILE,
        f"Removed candidates from election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )


@bot.command(
    name="show-election-progress", help="Show a table of candidates and their current polls"
)
@commands.has_guild_permissions(manage_guild=True)
async def show_election_progress(ctx):
    """
    Shows the current vote tally and candidate polls. Requires "Manage Server" permissions
    Args: None except context
    Return value: None
    """
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    voters_base_name = "voters/voters_" + str(ctx.guild.id)  # explicit cast required
    if not os.path.isfile(election_name):
        raise commands.errors.UserInputError("No election is in progress in current server!")
    timestamp = datetime.datetime.now()
    time_s = (
        str(timestamp.year)
        + "-"
        + str(timestamp.month)
        + "-"
        + str(timestamp.day)
        + " "
        + str(timestamp.hour)
        + ":"
        + str(timestamp.minute)
        + ":"
        + str(timestamp.second)
    )
    # there should be a more elegant method for that
    output = f"Election status in {ctx.guild.name} at {time_s} UTC:\n"
    election_info = await get_file_info(election_name)
    votes_sum = sum(election_info.values())
    reward_roles = await get_reward_roles(election_name)
    if len(reward_roles) != 0:
        output += "Reward roles: "
        for role_id in reward_roles:  # get reward roles' mentions
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            output += role.mention + ", "
        output += "\n"
    if votes_sum == 0:  # we can't divide by zero, btw
        raise commands.errors.CommandError("No votes registered yet!")
    for user in election_info:
        output += f"{await get_user_mention_by_id(user)}: {election_info[user]} ({round((election_info[user] / votes_sum) * 100, 2)}%)\n"
        # we respect election secrecy and do not directly link voters to candidates
        # we just record the fact someone voted
        # (nevermind that we don't use encryption yet...)
    current_leader = max(election_info, key=lambda key: election_info[key])  # yay, lambdas
    if not len(election_info.values()) == len(set(election_info.values())):
        output += "No current leader detected!\n"
        await ctx.send(output)
        return
    output += f"Current leader: {await get_user_mention_by_id(current_leader)} at {election_info[current_leader]} votes ({round((election_info[current_leader ] / votes_sum) * 100, 2)}%)\n"
    voters_info = await get_file_info(voters_base_name)
    if len(voters_info) == 0:
        raise commands.errors.UserInputError("No votes registered yet!")
    turnout = round(
        (len(voters_info) / len([m for m in ctx.guild.members if not m.bot])) * 100, 2
    )  # machines don't vote. Yet.
    output += f"Voter turnout: {turnout}%"

    await ctx.send(output)


@bot.command(name="vote", help="Cast your vote")
async def vote(ctx, *args):
    """
    Cast a vote for candidates
    Args: User mentions, separated by a space
    Return value: None
    """
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    voters_base_name = "voters/voters_" + str(ctx.guild.id)  # explicit cast required
    if not os.path.isfile(voters_base_name) or not os.path.isfile(election_name):
        raise commands.errors.UserInputError("No election is in progress in current server!")
    if len(args) == 0:
        raise commands.errors.UserInputError("Please select a candidate to vote for first!")
    if await is_string_in_file(
        voters_base_name, str(bot.get_user(await get_id_by_mention(ctx.author.mention)).id)
    ):  # god fucking dammit that's a pile a shit
        raise commands.errors.UserInputError(
            "You have voted already, and you can't change your choice now!"
        )
    # maybe consider allowing changing votes
    for i in args:
        if await get_mention_type(i) != "user":
            raise commands.errors.UserInputError(
                "Please, check if you are mentioning a role/channel, only users are supported!"
            )
    candidates = await get_mention_ids(args)
    await write_to_file(
        voters_base_name,
        f"{str(bot.get_user(await get_id_by_mention(ctx.author.mention)).id)} 1\n",  # 1 means voted
    )
    for candidate in candidates:
        await add_vote(election_name, candidate)

    await ctx.send(
        f"{await get_user_mention_by_id(str(bot.get_user(await get_id_by_mention(ctx.author.mention)).id))} has voted!"
    )  # god fucking dammit that's a pile of shit


@bot.command(name="finish-election", help="Finish the election and show the winner")
@commands.has_guild_permissions(manage_guild=True)
async def finish_election(ctx):
    """
    Finishes an election, announcing the current winner. Requires "Manage Server" permissions
    Args: None except context
    Return value: None
    """
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    voters_base_name = "voters/voters_" + str(ctx.guild.id)  # explicit cast required
    if not os.path.isfile(election_name):
        raise commands.errors.UserInputError("No election is in progress in current server!")
    timestamp = datetime.datetime.now()
    time_s = (
        str(timestamp.year)
        + "-"
        + str(timestamp.month)
        + "-"
        + str(timestamp.day)
        + " "
        + str(timestamp.hour)
        + ":"
        + str(timestamp.minute)
        + ":"
        + str(timestamp.second)
    )
    # there should be a more elegant method for that
    output = f"Election finished in {ctx.guild.name} at {time_s} UTC!\n"
    election_info = await get_file_info(election_name)
    votes_sum = sum(election_info.values())
    reward_roles = await get_reward_roles(election_name)
    if len(reward_roles) != 0:
        output += "Reward roles: "
        for role_id in reward_roles:  # get reward roles' mentions
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            output += role.mention + ", "  # fix later
        output += "\n"
    if votes_sum == 0:  # we can't divide by zero, btw
        raise commands.errors.CommandError("No votes registered yet!")
    for user in election_info:
        output += f"{await get_user_mention_by_id(user)}: {election_info[user]} ({round((election_info[user] / votes_sum) * 100, 2)}%)\n"
        # we respect election secrecy and do not directly link voters to candidates
        # we just record the fact someone voted
        # (nevermind that we don't use encryption yet...)
    winner_id = max(election_info, key=lambda key: election_info[key])  # yay, lambdas
    if not len(election_info.values()) == len(set(election_info.values())):
        output += "No winner detected!\n"
        await ctx.send(output)
        return
    output += f"Winner is: {await get_user_mention_by_id(winner_id)} at {election_info[winner_id]} votes ({round((election_info[winner_id] / votes_sum) * 100, 2)}%)\n"
    voters_info = await get_file_info(voters_base_name)
    print(f"voters_info: {voters_info}")
    if len(voters_info) == 0:
        raise commands.errors.UserInputError("No votes registered yet!")
    turnout = round(
        (len(voters_info) / len([m for m in ctx.guild.members if not m.bot])) * 100, 2
    )  # machines don't vote. Yet.
    output += f"Voter turnout: {turnout}%"
    winner = ctx.guild.get_member(winner_id)
    print(f"winner is {winner}")
    print(f"reward roles: {reward_roles}")
    for role_id in reward_roles:  # add reward roles
        print(f"in for at {role}")
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        await winner.add_roles(role, reason="Won the election")
        print("added role")
    os.remove(election_name)
    os.remove(voters_base_name)
    await write_to_file(
        LOGFILE, f"Election finished in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp} UTC"
    )
    print(f"Election finished in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp} UTC")

    await ctx.send(output)


@bot.command(
    name="set-election-reward-roles", help="Set roles that the winner will be rewarded with"
)
@commands.has_guild_permissions(manage_guild=True)
async def set_election_reward_roles(ctx, *args):
    """
    Adds roles that will serve as rewards for the election winner
    Args: Role mentions, separated by a space
    Return value: None
    """
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    if not os.path.isfile(election_name):
        raise commands.errors.UserInputError("No election is in progress in current server!")
    if len(args) == 0:
        raise commands.errors.UserInputError("At least one role required as reward!")
    roles_str = "Rewarded roles: "
    for role_mention in args:
        role_id = await get_id_by_mention(role_mention)
        roles_str += str(role_id) + " "
    roles_str += "\n"
    await write_to_file(election_name, roles_str)

    await ctx.send(f"Set roles as rewards for current election winners!")


@bot.command(name="ping", help="Get bot latency")  # just for reference
async def ping(ctx):
    """
    Get bot latency
    Args: None except context
    Return value: None
    """
    await ctx.send(f"Latency: {round(bot.latency * 1000)} ms")


@bot.event
async def on_ready():  # gets called when the bot is finished connecting to guilds
    """
    Initialize presence and log server connections
    Args: None
    Return value: None
    """
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name="election fraud")  # ha!
    )
    with open(LOGFILE, "a", encoding="utf-8") as logfile:
        start_timestamp = datetime.datetime.now()
        logfile.write(f"Bot ready at: {start_timestamp}\n")
        print(f"Bot ready at: {start_timestamp}")
        for guild in bot.guilds:
            guild_timestamp = datetime.datetime.now()
            logfile.write(
                f"{bot.user} is connected to {guild.name} (id: {guild.id}) at {guild_timestamp}\n"
            )
            print(f"{bot.user} is connected to {guild.name} (id: {guild.id}) at {guild_timestamp}")


@bot.event
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


set_dir_structure()  # creates necessary directories
# This doesn't look good

bot.run(TOKEN)
