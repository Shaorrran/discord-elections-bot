"""
Cog defining commands for managing elections.
"""
import datetime
import operator

import discord
from discord.ext import commands

import src.helpers as helpers
import src.internals as internals
from src.db.db import Elections, ServersSettings


class Voting(commands.Cog):
    """
    Commands for managing elections.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="start-election", help="Start an election in current server.")
    @commands.has_guild_permissions(manage_guild=True)
    async def start_election(self, ctx, *, candidates):
        """
        Start an election in this server. \
        Requires a list of mentions (these users will be the candidates) \
        separated by a space.
        """
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise commands.errors.CommandError("Set reward roles first.")
        candidates = list(set(str(candidates).split()))
        types = [await helpers.get_mention_type(i) for i in candidates]
        if "channel" in types or "role" in types or "undef" in types:
            raise commands.errors.UserInputError(
                "Please check if you haven't selected \
                a role/channel as a candidate. Only users are supported."
            )
        ids = await helpers.get_mention_ids(candidates)
        is_bot = [internals.bot.get_user(int(i)).bot for i in ids]
        if True in is_bot:
            raise commands.errors.UserInputError(
                "Please check if you haven't selected \
                a bot as a candidate. Machines don't have voting rights... yet."
            )
        election_id = len(await Elections.all()) + 1
        emoji_ids = [i.id for i in ctx.guild.emojis]
        candidates_votes = dict(zip(ids, zip(emoji_ids, [0 for i in ids])))
        await Elections.create(
            server_id=ctx.guild.id,
            id=election_id,
            candidates_votes=candidates_votes,
            timestamp=datetime.datetime.now(),
        )
        election = await Elections.filter(id=election_id).first()
        embed = discord.Embed(
            title=f"Election #{election_id}",
            desc=f"Voting sheet for election #{election_id} in {ctx.guild.name}",
            color=discord.Color.blue(),
        )
        candidates = (await Elections.filter(id=election_id).first()).candidates_votes
        names = [
            internals.bot.get_user(int(i)).name for i in candidates.keys()
        ]  # int cast required for the method to work
        embed_data = dict(zip(ctx.guild.emojis, names))
        for i, name in enumerate(embed_data):
            embed.add_field(name=f"Candidate #{i+1}", value=f"{name}:{embed_data[name]}")
        await ctx.reply(f"Election #{election_id} started in {ctx.guild.name}")
        message = await ctx.reply(embed=embed)
        await message.pin(reason="Pinning an election voting board.")
        for emoji in embed_data:
            await message.add_reaction(emoji)
        election.progress_message = message.id
        await election.save()

    @start_election.error
    async def start_election_error(self, ctx, error):
        """
        start-election error handling
        """
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.reply("At least one candidate is required to start an election.")
            return
        else:
            await ctx.reply(error)
            return

    @commands.command(
        name="view-current-elections", help="View which elections are ongoing in this server."
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def view_current_elections(self, ctx):
        """
        View which elections are ongoing in this server as a Rich embed.
        """
        elections = list(await Elections.filter(server_id=ctx.guild.id).all())
        embed = discord.Embed(
            title="Ongoing elections",
            description=f"List of elections currently in progress in {ctx.guild.name}",
            color=discord.Color.blue(),
        )
        for i in elections:
            embed.add_field(name=f"Election #{i.id}", value=f"initiated at {i.timestamp}")
        if not elections:
            embed.add_field(
                name="Elections in progress:",
                value="None. You're way too authoritarian for those pesky things.",
            )
        await ctx.reply(embed=embed)

    @commands.command(name="view-election-poll", help="View the current polls for an election.")
    @commands.has_guild_permissions(manage_guild=True)
    async def view_election_poll(self, ctx, *, election_id):
        """
        View the current poll for an election. Requires the election's ID as a number.
        """
        try:
            election = await Elections.filter(id=election_id).first()
        except Exception:
            election = None
        if election is None:
            raise commands.errors.CommandError("No such election exists.")
        election_candidates = election.candidates_votes
        embed = discord.Embed(
            title=f"Election #{election_id}",
            desc=f"Polls for election #{election_id} at {datetime.datetime.now()}",
            color=discord.Color.blue(),
        )
        for i in election_candidates:
            name = (
                internals.bot.get_user(int(i)).name
                + "#"
                + internals.bot.get_user(int(i)).discriminator
            )  # int cast required for the methods to work
            embed.add_field(name=name, value=election_candidates[i][1])
        await ctx.reply(embed=embed)

    @view_election_poll.error
    async def view_election_poll_error(self, ctx, error):
        """
        view-election-poll error handling
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                "Please specify an election ID.\
                 Use `view-current-elections` to see which elections are in progress."
            )
            return
        else:
            await ctx.reply(error)
            return

    @commands.command(
        name="finish-election", help="Finish an election and give out the roles to the winners."
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def finish_election(self, ctx, *, election_id):
        """
        Finish an election and give out reward roles.
        Args: election ID as type int.
        """
        server = await ServersSettings.filter(
            server_id=ctx.guild.id
        ).first()  # assuming it exists, one can't start an election without that
        winners_cutoff = server.winners_pool
        try:
            election = await Elections.filter(id=election_id).first()
        except Exception:
            election = None
        if not election:
            raise commands.errors.CommandError("No such election exists.")
        candidates_votes = election.candidates_votes
        voting = sorted(
            dict(zip(candidates_votes.keys(), [i[1] for i in candidates_votes.values()])),
            key=operator.itemgetter(1),
            reverse=True,
        )[:winners_cutoff]
        reward_roles = [
            discord.utils.get(ctx.guild.roles, id=int(role_id))
            for role_id in server.reward_roles.split(",")
        ]
        for i in voting:
            winner = ctx.guild.get_member(int(i))
            await winner.add_roles(*reward_roles, reason=f"Won election #{election_id}")
        mentions = ", ".join([await helpers.get_user_mention_by_id(i) for i in voting])
        await election.delete()
        await ctx.reply(f"Election {election_id} finished. Winners: {mentions}")

    @finish_election.error
    async def finish_election_error(self, ctx, error):
        """
        finish-election error handling
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                "Please specify an election ID.\
                 Use `view-current-elections` to see which elections are in progress."
            )
            return
        else:
            await ctx.reply(error)
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Listener that captures reactions and counts them as votes.
        """
        user = internals.bot.get_user(int(payload.user_id))
        if user.bot:
            return  # machines can't vote
        progress_messages = [
            i.progress_message for i in (await Elections.filter(server_id=payload.guild_id))
        ]
        if not payload.message_id in progress_messages:
            return  # not an election message
        election = await Elections.filter(progress_message=payload.message_id).first()
        server = await ServersSettings.filter(server_id=payload.guild_id).first()
        candidates_votes = election.candidates_votes
        for i in candidates_votes:
            weights = [
                (i, server.role_weights[str(i)])
                for i in (
                    set([i.id for i in payload.member.roles])
                    & set([int(i) for i in server.role_weights.keys()])
                )
            ]
            weights = sorted(weights, key=operator.itemgetter(1), reverse=True)
            if candidates_votes[i][0] == payload.emoji.id and weights:
                candidates_votes[i][1] += weights[0][1]

        election.candidates_votes = candidates_votes
        await election.save()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        An inverse to on_raw_reaction_add that retractes votes if the reaction is removed.
        """
        user = internals.bot.get_user(int(payload.user_id))
        if user.bot:
            return  # machines can't vote
        progress_messages = [
            i.progress_message for i in (await Elections.filter(server_id=payload.guild_id))
        ]
        if not payload.message_id in progress_messages:
            return  # not an election message
        election = await Elections.filter(progress_message=payload.message_id).first()
        server = await ServersSettings.filter(server_id=payload.guild_id).first()
        candidates_votes = election.candidates_votes
        for i in candidates_votes:
            weights = [
                (i, server.role_weights[str(i)])
                for i in (
                    set([i.id for i in payload.member.roles])
                    & set([int(i) for i in server.role_weights.keys()])
                )
            ]
            weights = sorted(weights, key=operator.itemgetter(1), reverse=True)
            if candidates_votes[i][0] == payload.emoji.id and weights:
                candidates_votes[i][1] -= weights[0][1]
        election.candidates_votes = candidates_votes
        await election.save()
