# Discord Electoral College bot
A bot that counts votes for moderators in Discord and updates roles as necessary

## Dependencies
    discord >= 1.5.0
    python-dotenv >= 0.14.0
    
## Config
The variables `ELECTIONS_DIR`, `VOTERS_DIR`, `LOGFILE` and the bot token are put in the .env file and contain either absolute or relative paths to the corresponding dirs (LOGFILE is the log file name, it's always in the ./logs dir for now)

## Adding the bot to a server
[Go here](https://discord.com/api/oauth2/authorize?client_id=763917750233858068&permissions=335752240&scope=bot)

## Concerns
The bot is not hosted anywhere yet, if you want to use it, deploy it as your own, the above link is for testing purposes only.
