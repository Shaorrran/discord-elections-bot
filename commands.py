"""
Bot command coroutines
"""
import datetime
import os

import discord
from discord.ext import commands

import helpers
import internals


@internals.bot.command(name="init-election", help="Starts an election")
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
    await helpers.write_to_file(
        voters_base_name,
        f"# Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )
    await helpers.write_to_file(
        election_name,
        f"# Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )
    mentions = await helpers.get_mention_ids(args)
    for mention in mentions:
        s = str(mention) + " " + "0\n"
        await helpers.write_to_file(
            election_name, s
        )  # initialize candidate and set votes count to 0
    await ctx.send("Election initiated!")
    print(f"Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}")
    await helpers.write_to_file(
        internals.LOGFILE,
        f"Election initiated in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )


@internals.bot.command(name="add-candidates", help="Adds candidates to the current election")
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
    mentions = await helpers.get_mention_ids(args)
    for mention in mentions:
        if await helpers.is_string_in_file(
            election_name, str(mention)
        ):  # Don't allow a candidate to occupy two positions at once
            # BUG: if role has the same name as the user, the command will fail
            raise commands.errors.UserInputError(
                f"Candidate {await helpers.get_user_mention_by_id(int(mention))} is already registered!"
            )
        s = str(mention) + " " + "0\n"
        await helpers.write_to_file(
            election_name, s
        )  # initialize candidate and set votes count to 0

    await ctx.send("Added new candidates to current election!")
    print(f"Added candidates to election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}")
    await helpers.write_to_file(
        internals.LOGFILE,
        f"Added new candidates to election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )


@internals.bot.command(name="remove-candidates", help="Remove candidates from the election")
@commands.has_guild_permissions(manage_guild=True)
async def remove_candidates(ctx, *args):
    """
    Removes candidates from current election
    Args: user mentions, separated by a space
    Return value: None
    """
    election_name = "elections/election_" + str(ctx.guild.id)  # explicit cast required
    timestamp = datetime.datetime.now()
    if not os.path.isfile(election_name):
        raise commands.errors.UserInputError("No election is in progress in current server!")
    if len(args) == 0:
        raise commands.errors.UserInputError("No candidates supplied!")
    mentions = await helpers.get_mention_ids(args)
    for mention in mentions:
        if await helpers.is_string_in_file(election_name, str(mention)):
            await helpers.remove_line_from_file(election_name, str(mention))

    await ctx.send("Removed candidates from current election!")
    print(
        f"Removed candidates from election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}"
    )
    await helpers.write_to_file(
        internals.LOGFILE,
        f"Removed candidates from election in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp}\n",
    )


@internals.bot.command(
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
    election_info = await helpers.get_file_info(election_name)
    votes_sum = sum(election_info.values())
    reward_roles = await helpers.get_reward_roles(election_name)
    if len(reward_roles) != 0:
        output += "Reward roles: "
        for role_id in reward_roles:  # get reward roles' mentions
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            output += role.mention + " "
        output += "\n"
    if votes_sum == 0:  # we can't divide by zero, btw
        raise commands.errors.CommandError("No votes registered yet!")
    for user in election_info:
        output += f"{await helpers.get_user_mention_by_id(user)}: {election_info[user]} ({round((election_info[user] / votes_sum) * 100, 2)}%)\n"
        # we respect election secrecy and do not directly link voters to candidates
        # we just record the fact someone voted
        # (nevermind that we don't use encryption yet...)
    current_leader = max(election_info, key=lambda key: election_info[key])  # yay, lambdas
    if not len(election_info.values()) == len(set(election_info.values())):
        output += "No current leader detected!\n"
        await ctx.send(output)
        return
    output += f"Current leader: {await helpers.get_user_mention_by_id(current_leader)} at {election_info[current_leader]} votes ({round((election_info[current_leader ] / votes_sum) * 100, 2)}%)\n"
    voters_info = await helpers.get_file_info(voters_base_name)
    if len(voters_info) == 0:
        raise commands.errors.UserInputError("No votes registered yet!")
    turnout = round(
        (len(voters_info) / len([m for m in ctx.guild.members if not m.bot])) * 100, 2
    )  # machines don't vote. Yet.
    output += f"Voter turnout: {turnout}%"

    await ctx.send(output)


@internals.bot.command(name="vote", help="Cast your vote")
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
    if await helpers.is_string_in_file(
        voters_base_name,
        str(internals.bot.get_user(await helpers.get_id_by_mention(ctx.author.mention)).id),
    ):  # god fucking dammit that's a pile a shit
        raise commands.errors.UserInputError(
            "You have voted already, and you can't change your choice now!"
        )
    # maybe consider allowing changing votes
    for i in args:
        if await helpers.get_mention_type(i) != "user":
            raise commands.errors.UserInputError(
                "Please, check if you are mentioning a role/channel, only users are supported!"
            )
    candidates = await helpers.get_mention_ids(args)
    await helpers.write_to_file(
        voters_base_name,
        f"{str(internals.bot.get_user(await helpers.get_id_by_mention(ctx.author.mention)).id)} 1\n",  # 1 means voted
    )
    for candidate in candidates:
        await helpers.add_vote(election_name, candidate)

    await ctx.send(
        f"{await helpers.get_user_mention_by_id(str(internals.bot.get_user(await helpers.get_id_by_mention(ctx.author.mention)).id))} has voted!"
    )  # god fucking dammit that's a pile of shit


@internals.bot.command(name="finish-election", help="Finish the election and show the winner")
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
    election_info = await helpers.get_file_info(election_name)
    votes_sum = sum(election_info.values())
    reward_roles = await helpers.get_reward_roles(election_name)
    if len(reward_roles) != 0:
        output += "Reward roles: "
        for role_id in reward_roles:  # get reward roles' mentions
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            output += role.mention + ", "  # fix later
        output += "\n"
    if votes_sum == 0:  # we can't divide by zero, btw
        raise commands.errors.CommandError("No votes registered yet!")
    for user in election_info:
        output += f"{await helpers.get_user_mention_by_id(user)}: {election_info[user]} ({round((election_info[user] / votes_sum) * 100, 2)}%)\n"
        # we respect election secrecy and do not directly link voters to candidates
        # we just record the fact someone voted
        # (nevermind that we don't use encryption yet...)
    winner_id = max(election_info, key=lambda key: election_info[key])  # yay, lambdas
    if not len(election_info.values()) == len(set(election_info.values())):
        output += "No winner detected!\n"
        await ctx.send(output)
        return
    output += f"Winner is: {await helpers.get_user_mention_by_id(winner_id)} at {election_info[winner_id]} votes ({round((election_info[winner_id] / votes_sum) * 100, 2)}%)\n"
    voters_info = await helpers.get_file_info(voters_base_name)
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
    await helpers.write_to_file(
        internals.LOGFILE,
        f"Election finished in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp} UTC",
    )
    print(f"Election finished in {ctx.guild.name} (id: {ctx.guild.id}) at {timestamp} UTC")

    await ctx.send(output)


@internals.bot.command(
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
        role_id = await helpers.get_id_by_mention(role_mention)
        roles_str += str(role_id) + " "
    roles_str += "\n"
    await helpers.write_to_file(election_name, roles_str)

    await ctx.send(f"Set roles as rewards for current election winners!")


@internals.bot.command(name="ping", help="Get bot latency")  # just for reference
async def ping(ctx):
    """
    Get bot latency
    Args: None except context
    Return value: None
    """
    await ctx.send(f"Latency: {round(internals.bot.latency * 1000)} ms")
