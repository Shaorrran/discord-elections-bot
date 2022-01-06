"""
Cog defining commands for changing server-wide settings.
"""
import discord
from discord.ext import commands

import src.helpers as helpers
import src.internals as internals
from src.db.db import ServersSettings


class Settings(commands.Cog):
    """
    Commands for changing server-wide settings.
    """

    def __init__(self, bot):
        """
        Initialize the cog.
        Args: bot object
        Return value: None
        """
        self.bot = bot

    @commands.command(name="set-prefixes", help="Set bot prefixes for this server")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def set_prefixes(self, ctx, *, prefixes):
        """
        Set bot prefixes.
        Args: prefixes (strings separated by spaces)
        Return value: None
        """
        prefixes = prefixes.split()
        if "<" in prefixes:
            raise commands.errors.UserInputError("Please do not use \"<\" as a prefix. As discord stores some internal data in `<whatever>` format, this may cause a machine uprising.")
        if not prefixes:
            raise commands.errors.MissingRequiredArgument("At least one prefix required.")
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise ValueError("Server settings not found. This is most likely my own fault.")
        prefix_str = ",".join(prefixes)
        nickname = f"[{prefix_str}]{self.bot.user.name}"
        if len(nickname) > 32:
            raise commands.errors.UserInputError("Discord requires usernames to be 32 characters or less in length, and you supplied more, so the bot cannot rename itself.\nPlease select fewer and/or shorter prefixes.")
        server.prefixes = prefix_str
        await server.save()
        await ctx.guild.get_member(self.bot.user.id).edit(nick=nickname)
        await ctx.reply("New prefixes set!")

    @set_prefixes.error
    async def set_prefixes_error(self, ctx, error):
        """
        set-prefixes error handling.
        Args: context, error
        Return value: None
        """
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.reply("At least one prefix required.\nCommand syntax: `set-prefixes prefix prefix prefix ...`")
        else:
            await ctx.reply(f"{error}")

    @commands.command(name="set-election-managers", help="Select roles that have the ability to change election parameters and manage elections.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def set_election_managers(self, ctx, *, roles):
        """
        Set roles that can edit server election settings and manage elections.
        Args: list of role mentions of type str
        Return value: None
        """
        roles = roles.split()
        if not roles:
            raise commands.errors.MissingRequiredArgument("At least one role required.")
        types = [await helpers.get_mention_type(i) for i in roles]
        if "user" in types or "channel" in types or "undef" in types:
            raise commands.errors.UserInputError(
                "Please check if you had mentioned a user/channel. Only roles are supported."
            )
        ids = list(set([str(i) for i in await helpers.get_mention_ids(roles)]))
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise ValueError("Server settings not found. This is likely my own fault.")
        guild_managers = list(set([str(i.id) for i in ctx.guild.roles if i.permissions.manage_guild]))
        server.election_managers = ",".join(guild_managers) + "," + ",".join(ids)
        await server.save()
        await ctx.reply("Election manager roles set.")

    @set_election_managers.error
    async def set_election_managers_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.reply("At least one role required.")
        else:
            await ctx.reply(f"{error}")

    @commands.command(
        name="set-reward-roles", help="Set the roles that will be given out as rewards to winners."
    )
    @commands.guild_only()
    async def set_reward_roles(self, ctx, *, roles):
        """
        Set roles to be given as rewards for winning elections.
        Args: list of role mentions of type str
        Return value: None
        """
        has_permission = await helpers.is_election_manager(ctx)
        if not has_permission:
            raise commands.errors.CheckFailure(message="You are not an election manager.")
        roles = roles.split()
        if not roles:
            raise commands.errors.MissingRequiredArgument("At least one role required.")
        types = [await helpers.get_mention_type(i) for i in roles]
        if "user" in types or "channel" in types or "undef" in types:
            raise commands.errors.UserInputError(
                "Please check if you had mentioned a user/channel. Only roles are supported."
            )
        ids = [str(i) for i in await helpers.get_mention_ids(roles)]
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise ValueError("Server settings not found. This is likely my own fault.")
        server.reward_roles = ",".join(ids)
        await server.save()
        await ctx.reply("Reward roles set.")

    @set_reward_roles.error
    async def set_reward_roles_error(self, ctx, error):
        """
        set-reward-roles error handling.
        Args: context, error
        Return value: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Please specify at least one role to set as a reward.")
        else:
            await ctx.reply(error)

    @commands.command(
        name="set-winners-count", help="Set the number of winner that are possible in an election."
    )
    @commands.guild_only()
    async def set_winners_count(self, ctx, *, count):
        """
        Set the number of users that will be able to win the election.
        Args: count of type int
        Return value: None
        """
        has_permission = await helpers.is_election_manager(ctx)
        if not has_permission:
            raise commands.errors.CheckFailure(message="You are not an election manager.")
        count = count.split()
        if not count:
            raise commands.errors.MissingRequiredArgument("Please specify the winners count number.")
        if len(count) > 1:
            raise commands.errors.UserInputError("Only one number required.")
        try:
            winners_pool = int(count[0])
        except ValueError:
            raise commands.errors.UserInputError("Please provide an integer number.")
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise ValueError("Server settings not found. This is likely my own fault.")
            if winners_pool <= 0:
                raise commands.errors.UserInputError("Please provide a number that is more than zero.")
        server.winners_pool = winners_pool
        await server.save()
        await ctx.reply("Winners pool set.")

    @set_winners_count.error
    async def set_winners_count_error(self, ctx, error):
        """
        set-winners-count error handling.
        Args: context, error
        Return value: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Count required.")
        else:
            await ctx.reply(error)

    @commands.command(
        name="set-role-weights",
        help="Set the number of votes a member with a given role has available.",
    )
    @commands.guild_only()
    async def set_role_weights(self, ctx, *, args):
        """
        Set the amount of votes a user with a given role has.
        The default amount would be 0, so take heed.
        Args: list of mentions and integer weights
        (mentions on even indices, weights on odd indices)
        Return value: None
        """
        has_permission = await helpers.is_election_manager(ctx)
        if not has_permission:
            raise commands.errors.CheckFailure(message="You are not an election manager.")
        args = args.split()
        if not args:
            raise commands.errors.MissingRequiredArgument("At least one role-weight pair is required.")
        if len(args) % 2 != 0:
            raise commands.errors.MissingRequiredArgument(
                "Missing one or more weights."
            )
        mentions = [e for i, e in enumerate(args) if i % 2 == 0]
        counts = [e for i, e in enumerate(args) if i % 2 != 0]
        try:
            counts = [int(i) for i in counts]
        except ValueError:
            raise commands.errors.UserInputError(
                "Please provide integer numbers for role weights."
            )
        if "@everyone" in mentions:
            while "@everyone" in mentions:
                pos = mentions.index("@everyone")
                mentions[
                    pos
                ] = f"<@&{ctx.guild.id}>"  # @everyone is equal to mentioning by server id
        if "@here" in mentions:
            raise commands.errors.UserInputError(
                "Please avoid using the `@here` mention. It does not make sense anyway, because it targets individual users."
            )
        types = [await helpers.get_mention_type(i) for i in mentions]
        if "user" in types or "channel" in types or "undef" in types:
            raise commands.errors.UserInputError(
                "Please check if you had mentioned a user/channel. Only roles are supported."
            )
        ids = await helpers.get_mention_ids(mentions)
        role_weights = dict(zip(ids, counts))
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise ValueError("Server settings not found. This is likely my own fault.")
        server.role_weights = role_weights
        await server.save()
        await ctx.reply("Role weights updated!")

    @set_role_weights.error
    async def set_role_weights_error(self, ctx, error):
        """
        set-role-weights error handling.
        Args: context, error
        Return value: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                f"A list of mentions and numbers is required.\nCommand syntax is: `set-role-weights @mention weight @mention weight ...`"
            )
        else:
            await ctx.reply(
                f"{error}\nCommand syntax is: `set-role-weights @mention weight @mention weight ...`"
            )

    @commands.command(
        name="view-server-settings", help="View the current settings for this server."
    )
    @commands.guild_only()
    async def view_server_settings(self, ctx):
        """
        Reply with an embed storing server-wide settings.
        Args: none except context
        Return value: None
        """
        has_permission = await helpers.is_election_manager(ctx)
        if not has_permission:
            raise commands.errors.CheckFailure(message="You are not an election manager.")
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise ValueError("Server settings not found. This is likely my own fault.")
        embed = discord.Embed(
            title="Server settings",
            desc=f"Elections settings for {ctx.guild.name}",
            color=discord.Color.dark_blue(),
        )
        if not server.reward_roles:
            raise commands.errors.CheckFailure(message="Run `set-reward-roles` first.")
        roles = [
            discord.utils.get(ctx.guild.roles, id=int(role_id)).name
            for role_id in server.reward_roles.split(",")
        ]
        reward_roles = ",".join(roles)
        embed.add_field(name="Reward roles", value=reward_roles)
        selection_strategy_str = "Maximum votes" if server.winner_selection_strategy == "max_votes" else "Votes cutoff"
        embed.add_field(name="Winner selection strategy", value=selection_strategy_str)
        winner_pool_str = f"{server.winners_pool}" if server.winner_selection_strategy == "max_votes" else "N/A"
        embed.add_field(name="Winners pool", value=winner_pool_str)
        votes_cutoff_str = server.votes_cutoff if server.winner_selection_strategy == "cutoff" else "N/A"
        embed.add_field(name="Votes cutoff", value=votes_cutoff_str)
        if not server.role_weights:
            raise commands.errors.CheckFailure(message="Run `set-role-weights` first.")
        for i in server.role_weights:
            role = discord.utils.get(ctx.guild.roles, id=int(i))
            embed.add_field(
                name=f"Votes available for users with the role {role}",
                value=f"{server.role_weights[i]}",
            )
        await ctx.reply(embed=embed)

        @view_server_settings.error
        async def view_server_settings_error(self, ctx, error):
            """
            view-server-settings error handling.
            Args: context, error
            Return value: None
            """
            await ctx.reply(f"{error}")

    @commands.command(name="set-winner-selection-strategy", help="Set whether to choose winners by maximum votes count or simply by a cutoff number.")
    @commands.guild_only()
    async def set_winner_selection_strategy(self, ctx, strategy):
        """
        Set the election strategy to either select winners by sorting vote counts and selecting `winners_count` members as winners,
        or by setting all members with the amount of votes more or equal to `votes_cutoff` as winners.
        Args: mode of type str in ("max_votes", "cutoff")
        Return value: None
        """
        has_permission = await helpers.is_election_manager(ctx)
        if not has_permission:
            raise commands.errors.CheckFailure(message="You are not an election manager.")
        if strategy not in ("max_votes", "cutoff"):
            raise commands.errors.UserInputError("Incorrent election strategy, only `max_votes` or `cutoff` allowed.")
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise ValueError("Server settings not found. This is likely my own fault.")
        server.winner_selection_strategy = strategy
        await server.save()
        await ctx.reply("Winner selection strategy set.")

    @set_winner_selection_strategy.error
    async def set_winner_selection_strategy_error(self, ctx, error):
        """
        set-winner-selection-strategy error handling.
        Args: context, error
        Return value: None
        """
        await ctx.reply(f"{error}")

    @commands.command(name="set-votes-cutoff", help="Set the amount of votes that determine how much votes a member must amass to win an election if the `cutoff` strategy is used.")
    @commands.guild_only()
    async def set_votes_cutoff(self, ctx, *, cutoff):
        """
        Set the cutoff that determines the amount of votes a member must have to pass as a winner.
        Args: cutoff as type int
        Return value: None
        """
        has_permission = await helpers.is_election_manager(ctx)
        if not has_permission:
            raise commands.errors.CheckFailure(message="You are not an election manager.")
        cutoff = cutoff.split()
        if not cutoff:
            raise commands.errors.MissingRequiredArgument("Cutoff required.")
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if len(cutoff) > 1:
            raise commands.errors.UserInputError("Only one number required.")
        try:
            cutoff = int(cutoff[0])
        except ValueError:
            raise commands.errors.UserInputError("Please provide an integer number.")
        if cutoff <= 0:
            raise commands.errors.UserInputError("The cutoff must be more than zero.")
        server.votes_cutoff = cutoff
        await server.save()
        await ctx.reply("Votes cutoff set.")

    @set_votes_cutoff.error
    async def set_votes_cutoff_error(self, ctx, error):
        """
        set-votes-cutoff error handling.
        Args: context, error
        Return value: None
        """
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.reply("Cutoff required")
        else:
            await ctx.reply(f"{error}")