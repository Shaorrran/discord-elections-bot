"""
Helper functions.
"""
import typing

from discord.ext import commands

import src.internals as internals


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


async def get_mention_ids(mentions: typing.List[str]) -> typing.List[int]:
    """
    Get a list of ids from a list of mentions
    Args: mentions of type List[str]
    Return value: ids of type List[str]
    """
    result = []
    for mention in mentions:
        result.append(await get_id_by_mention(mention))

    return result


async def get_user_mention_by_id(identifier: str) -> str:
    """
    Wrapper for user.mention checking for mention type
    Args: id of type str
    Return value: mention of type str
    """
    # user mentions only for now
    user = internals.bot.get_user(
        int(identifier)
    )  # explicit cast required to avoid illegal argument exceptions
    if not await get_mention_type(user.mention) == "user":
        raise commands.errors.BadArgument(
            "Please check if you are mentioning a role/channel, only users are supported."
        )
    return user.mention  # automatically constructs a mention


async def get_mention_type(mention: str) -> str:
    """
    Get mention type by mention
    Mentions in Discord have a <@user_id> format
    or <@!user_id> if the user has a guild-specific nickname,
    or <@&role_id> for role mentions,
    or <@#channel_id> for channel mentions
    Args: mention of type str
    Return value: one of the strings
    "user", "channel", "role", "undef"
    """
    # Mentions in Discord have a <@user_id> format or <@!user_id> if the user has a guild-specific nickname,
    # or <@&role_id> for role mentions, or <@#channel_id> for channel mentions
    mention = str(mention)
    if mention.startswith("<@&") and mention.endswith(">"):  # role mention
        return "role"
    if mention.startswith("<@") and mention.endswith(">"):  # user mention
        return "user"
    if mention.startswith("<@!") and mention.endswith(">"):  # user mention by guild-specific name
        return "user"
    if mention.startswith("<#") and mention.endswith(">"):  # channel mention
        return "channel"

    return "undef"


async def get_emoji_id_from_embed_field(field: str) -> int:
    """
    Get emoji id from an embed field
    The embed fields look like <:emoji_name:emoji_id>:candidate_name
    Args: embed field value of type str
    Return value: emoji id of type int
    """
    emoji_data = field[: field.find(">")][2:]
    emoji_id = int(emoji_data[emoji_data.find(":") + 1 :])
    return emoji_id
