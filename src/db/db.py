"""
Tortoise ORM models' definitions and db access internals.
"""
import os

from tortoise import Tortoise, fields, run_async
from tortoise.models import Model


class ServersSettings(Model):
    """
    Model for server-wide settings storage.
    """

    server_id = fields.IntField(pk=True, unique=True)
    reward_roles = fields.TextField(default="")  # ids separated by a comma
    role_weights = fields.JSONField(null=True) # dict: {role_id: integer_weight}
    winners_pool = fields.IntField(default=1)
    prefixes = fields.TextField(default="!")
    election_managers = fields.TextField(default="")

    def __str__(self):
        """
        Magic.
        """
        return str(self.server_id)

    class Meta:
        table = "servers_settings"
        table_description = "Stores election settings for servers"


class Elections(Model):
    """
    Model for storing individual elections.
    """

    id = fields.IntField(pk=True, unique=True)
    server_id = fields.IntField()
    timestamp = fields.DatetimeField()
    candidates_votes = fields.JSONField()  # dict: {"name": [emoji_id, number_of_votes]}
    progress_message = fields.IntField(default=-1)

    def __str__(self):
        """
        Magic.
        """
        return str(self.id)

    class Meta:
        table = "elections"
        table_description = "Stores individual election instances"


async def init(in_memory=False):
    """
    Start up the database connections.
    """
    if in_memory:
        database_path = "sqlite://:memory:"
    else:
        database_path = f"sqlite://{os.path.dirname(os.path.realpath(__file__))}/../../db.sqlite3"
    await Tortoise.init(
        db_url=database_path,
        modules={"models": [f"{__name__}"]},
    )
    await Tortoise.generate_schemas(safe=True)


async def db_cleanup():
    """
    Clean up db connections.
    """
    await Tortoise.close_connections()


if __name__ == "__main__":
    run_async(init())
