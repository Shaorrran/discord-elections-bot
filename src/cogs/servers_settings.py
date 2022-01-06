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
        self.bot = bot

    @commands.command(
        name="set-reward-roles", help="Set the roles that will be given out as rewards to winners."
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def set_reward_roles(self, ctx, *, roles):
        """
        Set roles to be given as rewards for winning elections.
        Args: list of role mentions of type str
        """
        roles = roles.split()
        types = [await helpers.get_mention_type(i) for i in roles]
        if "user" in types or "channel" in types or "undef" in types:
            raise commands.errors.UserInputError(
                "Please check if you had mentioned a user/channel. Only roles are supported."
            )
        ids = [str(i) for i in await helpers.get_mention_ids(roles)]
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            await ServersSettings.create(server_id=ctx.guild.id, reward_roles=",".join(ids))
            await ctx.reply("Reward roles set.")
            return
        server.reward_roles = ",".join(ids)
        await server.save()
        await ctx.reply("Reward roles set.")

    @set_reward_roles.error
    async def set_reward_roles_error(self, ctx, error):
        """
        set-reward-roles error handling
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Please specify at least one role to set as a reward.")
            return
        else:
            await ctx.reply(error)
            return

    @commands.command(
        name="set-winners-count", help="Set the number of winner that are possible in an election."
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def set_winners_count(self, ctx, *, count):
        """
        Set the number of users that will be able to win the election.
        Args: count of type int
        """
        count = count.split()
        if len(count) > 1:
            raise commands.errors.UserInputError("Only one number required.")
        try:
            winners_pool = int(count[0])
        except ValueError:
            raise commands.errors.UserInputError("Please provide an integer number.") from None
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise commands.errors.CommandError("Set reward roles first.")
        server.winners_pool = winners_pool
        await server.save()
        await ctx.reply("Winners pool set.")

    @set_winners_count.error
    async def set_winners_count_error(self, ctx, error):
        """
        set-winners-count error handling
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Count required.")
            return
        else:
            await ctx.reply(error)
            return

    @commands.command(
        name="set-role-weights",
        help="Set the number of votes a member with a given role has available.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def set_role_weights(self, ctx, *, args):
        """
        Set the amount of votes a user with a given role has.
        The default amount would be 0, so take heed.
        """
        args = args.split()
        mentions = [e for i, e in enumerate(args) if i % 2 == 0]
        counts = [e for i, e in enumerate(args) if i % 2 != 0]
        try:
            counts = [int(i) for i in counts]
        except ValueError:
            raise commands.errors.UserInputError(
                "Please provide integer numbers for role weights."
            ) from None
        if "@everyone" in mentions:
            while "@everyone" in mentions:
                pos = mentions.index("@everyone")
                mentions[
                    pos
                ] = f"<@&{ctx.guild.id}>"  # @everyone is equal to mentioning by server id
        if "@here" in mentions:
            raise commands.errors.UserInputError(
                "Please avoid \
                using the \@here mention. \
                It does not make sense anyway, \
                because it targets individual users."
            )
        types = [await helpers.get_mention_type(i) for i in mentions]
        if "user" in types or "channel" in types or "undef" in types:
            raise commands.errors.UserInputError(
                "Please check if you had mentioned a user/channel. Only roles are supported."
            )
        ids = await helpers.get_mention_ids(mentions)
        role_weights = dict(zip(ids, counts))
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        server.role_weights = role_weights
        await server.save()
        await ctx.reply("Role weights updated!")

    @set_role_weights.error
    async def set_role_weights_error(self, ctx, error):
        """
        set-role-weights error handling
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                f"A list of mentions and numbers is required.\
                \nCommand syntax is: `@{internals.bot.user.name} \
                set-role-weights @mention weight @mention weight ...`"
            )
            return
        else:
            await ctx.reply(
                f"{error}\nCommand syntax is: `@{internals.bot.user.name} \
                set-role-weights @mention weight @mention weight ...`"
            )
            return

    @commands.command(
        name="view-server-settings", help="View the current settings for this server."
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def view_server_settings(self, ctx):
        """
        Reply with an embed storing server-wide settings.
        """
        server = await ServersSettings.filter(server_id=ctx.guild.id).first()
        if not server:
            raise commands.errors.CommandError("Server configuration is not set yet. Please run `set-reward-roles`.")
        embed = discord.Embed(
            title="Server settings",
            desc=f"Elections settings for {ctx.guild.name}",
            color=discord.Color.dark_blue(),
        )
        roles = [
            discord.utils.get(ctx.guild.roles, id=int(role_id)).name
            for role_id in server.reward_roles.split(",")
        ]
        reward_roles = ",".join(roles)
        embed.add_field(name="Reward roles", value=reward_roles)
        embed.add_field(name="Winners' pool", value=f"{server.winners_pool} winners possible")
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
            view-server-settings error handling
            """
            await ctx.reply(f"{error}")