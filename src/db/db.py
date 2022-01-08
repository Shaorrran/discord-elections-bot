"""
Tortoise ORM models' definitions and db access internals.
"""
import os
import warnings

from dotenv import load_dotenv

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
    winner_selection_strategy = fields.TextField(default="max_votes")
    votes_cutoff = fields.IntField(default="0")

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


async def init():
    """
    Start up the database connections.
    """
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL") if os.getenv("DATABASE_URL") else None
    LOCAL_DB = bool(int(os.getenv("LOCAL_DB"))) if os.getenv("LOCAL_DB") else True
    POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME") if not LOCAL_DB else "postgres"
    POSTGRES_HOST = os.getenv("POSTGRES_HOST") if not LOCAL_DB else "localhost"
    POSTGRES_PORT = os.getenv("POSTGRES_PORT") if not LOCAL_DB else 5432
    POSTGRES_DBNAME = os.getenv("POSTGRES_DBNAME") if not LOCAL_DB else "postgres"
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") if not LOCAL_DB else ""
    if DATABASE_URL:
        database_path = DATABASE_URL
    else:
        database_path = f"postgres://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DBNAME}"
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