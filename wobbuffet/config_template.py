"""Configuration values for Wobbuffet - Rename to config.py"""

# bot token from discord developers
bot_token = 'your_token_here'

# default bot settings
bot_prefix = '!'
bot_master = 12345678903216549878
bot_coowners = [132314336914833409, 263607303096369152]
preload_extensions = []

# minimum required permissions for bot user
bot_permissions = 268822608

# postgresql database credentials
db_details = {
    # 'username': 'wobbuffet',
    # 'database': 'wobbuffet',
    # 'hostname': 'localhost',
    'password': 'password'
}

# default language
lang_bot = 'en'

# team settings
team_list = ['mystic', 'valor', 'instinct']
team_colours = {
    "mystic": "0x3498db",
    "valor": "0xe74c3c",
    "instinct": "0xf1c40f"
}

team_emoji = {
    "mystic": "<:mystic:351758303912656896>",
    "valor": "<:valor:351758298975830016>",
    "instinct": "<:instinct:351758298627702786>",
    "unknown": "\u2754"
}

# help command categories
command_categories = {
    "Owner": {
        "index": "5",
        "description": "Owner-only commands for bot config or info."
    },
    "Server Config": {
        "index": "10",
        "description": "Server configuration commands."
    },
    "Bot Info": {
        "index": "15",
        "description": "Commands for finding out information on the bot."
    },
}
