"""
Helper functions for Discord election bot
"""
import datetime
import os
import typing

from discord.ext import commands

import internals


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
        with open(internals.LOGFILE, "a", encoding="utf-8") as logfile:
            logfile.write(f"Created logfile and logs dir at {timestamp}\n")
            print(f"Created logfile and logs dir at {timestamp}")
    # create elections dir if none exists. See TODO #2
    if not os.path.isdir(internals.ELECTIONS_DIR):
        os.mkdir(internals.ELECTIONS_DIR)
        timestamp = datetime.datetime.now()
        with open(internals.LOGFILE, "a", encoding="utf-8") as logfile:
            logfile.write(f"Created elections dir at {timestamp}\n")
            print(f"Created elections dir at {timestamp}")
    # create voters dir if none exists. See TODO #2
    if not os.path.isdir(internals.VOTERS_DIR):
        os.mkdir(internals.VOTERS_DIR)
        timestamp = datetime.datetime.now()
        with open(internals.LOGFILE, "a", encoding="utf-8") as logfile:
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
    user = internals.bot.get_user(
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
    """
    Get roles that serve as reward for current election's winners
    Args: filename as type str
    Return value: List of role mentions
    """
    roles = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.startswith("Rewarded roles:"):  # add rewarded roles
                line_content = line.split()
                line_content = line_content[2:]  # delete "Rewarded roles"
                roles.append(line_content)

    roles = [int(j) for i in roles for j in i]  # flatten the list and cast to int

    return roles
