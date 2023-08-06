import os

import discord
from discord.ext import commands
from util.settings.prefix_handler import bot_prefix
from util.settings.settings_initializer import check_default_settings

# build intents
bot_intents = discord.Intents.default()
bot_intents.members = True
bot_intents.message_content = True
bot_intents.reactions = True

# bot init
# noinspection PyTypeChecker
bot = commands.Bot(command_prefix=bot_prefix, intents=bot_intents)
bot.remove_command("help")

# add extensions
@bot.event
async def setup_hook():
    for dir_object in os.scandir("extensions"):
        if dir_object.is_file():
            await bot.load_extension(f"extensions.{dir_object.name[:-3]}")

    for dir_object in os.scandir("extensions/holocrons"):
        if dir_object.is_file():
            await bot.load_extension(f"extensions.holocrons.{dir_object.name[:-3]}")


# settings init
check_default_settings()

# run bot
bot_token = os.environ['BOT_TOKEN']
bot.run(bot_token)
