# Discord Electoral College bot
A bot that counts votes for moderators in Discord and updates roles as necessary. Refactored to use SQLite databases (with Tortoise ORM)

## Dependencies
See `requirements.txt`
    
## Config
The bot token is stored in the `.env` file as `BOT_TOKEN=token_here`
The `.env` file can also store a `IN_MEMORY_DB` boolean variable, which denotes database storage type: either the DB is entirely in-memory or stored in a file.

## Adding the bot to a server
[Go here](https://discord.com/api/oauth2/authorize?client_id=763917750233858068&permissions=335752240&scope=bot)