import discord
from discord.ext import commands
from util.global_constants import bot_token
from util.settings.prefix_handler import bot_prefix
from util.settings.settings_initializer import check_default_settings

# build intents
bot_intents = discord.Intents.default()
bot_intents.members = True
bot_intents.message_content = True
bot_intents.reactions = True

# bot init
bot = commands.Bot(command_prefix=bot_prefix, intents=bot_intents)
bot.remove_command("help")

# add extensions
extensions = ("extensions.base_commands", "extensions.send_conquest_tips", "extensions.settings_commands")


@bot.event
async def setup_hook():
    for extension in extensions:
        await bot.load_extension(extension)


# settings init
check_default_settings()

# run bot
bot.run(bot_token)
