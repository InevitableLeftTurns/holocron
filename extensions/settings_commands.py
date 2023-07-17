import unicodedata
import discord
import json
from discord.ext import commands
from util.command_checks import check_higher_perms
from collections import namedtuple
from util.prefix_handler import bot_prefixes


AwaitingReaction = namedtuple("AwaitingReaction", ["user_id", "allowed_emoji"])

def check_prefix(message: discord.Message):
    content = message.content
    return True if len(content) <= 3 and content.find(" ") == -1 else False


class SettingsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = None
        self.load_settings()
        self.waiting_for_reactions = {}

    def load_settings(self):
        with open("util/settings.json") as settings_file:
            settings = json.load(settings_file)["guild_id"]
        self.settings = settings
        for guild_id, settings in settings.items():
            bot_prefixes[guild_id] = settings["Bot Prefix"]

    def update_settings(self):
        with open("util/settings.json", "w") as settings_file:
            json.dump({"guild_id": self.settings}, settings_file)

    def get_server_settings(self, guild: discord.Guild):
        try:
            settings = self.settings[str(guild.id)]
        except KeyError:
            default_settings = self.settings["0"]
            self.settings[str(guild.id)] = default_settings
            self.update_settings()
            return default_settings

        default_settings = self.settings["0"]
        if len(settings.keys()) != len(default_settings.keys()):
            for key, value in default_settings.items():
                try:
                    settings[key]
                except KeyError:
                    self.settings[str(guild.id)][key] = default_settings[key]

            self.update_settings()
        return self.settings[str(guild.id)]

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if user.id == self.bot.user.id:
            return
        try:
            message_user_id = self.waiting_for_reactions[reaction.message.id].user_id
        except KeyError:
            return
        if message_user_id == user.id:
            await self.handle_setting_change(reaction, user)

    async def handle_setting_change(self, reaction: discord.Reaction, user: discord.Member):
        def check_message(message: discord.Message):
            return message.channel.id == channel.id and message.author.id == user.id

        channel = reaction.message.channel

        allowed_emojis = self.waiting_for_reactions[reaction.message.id].allowed_emoji
        if reaction.emoji not in allowed_emojis:
            return

        del self.waiting_for_reactions[reaction.message.id]

        setting_index = int(reaction.emoji[0])-1
        current_settings = self.get_server_settings(reaction.message.guild)
        await channel.send(f"What should the new value of `{[key for key in current_settings.keys()][setting_index]}` "
                           f"be?")

        setting_accepted = False
        new_setting = None
        setting_checks = [
            check_prefix
        ]
        error_messages = [
            "That prefix has been rejected. Try a shorter prefix, or one without a space."
        ]
        success_functions = [
            self.set_prefix
        ]
        while not setting_accepted:
            new_setting = await self.bot.wait_for("message", check=check_message)
            setting_accepted = setting_checks[setting_index](new_setting)
            if not setting_accepted:
                await channel.send(error_messages[setting_index])
        await success_functions[setting_index](new_setting)

    async def set_prefix(self, message: discord.Message):
        id_key = str(message.guild.id)
        self.settings[id_key]["Bot Prefix"] = message.content
        bot_prefixes[id_key] = message.content
        self.update_settings()
        await message.channel.send(f"Set Prefix to {message.content}")

    @commands.command(name="settings", description="A list of server settings which can be changed (requires admin)")
    async def settings(self, ctx: commands.Context, edit="no"):
        if not await check_higher_perms(ctx.author, ctx.guild):
            await ctx.send("You do not have access to this command.")
            return

        editing = True if edit == "edit" else False
        if editing:
            to_send = "Which setting do you want to change?\n"

            current_settings = self.get_server_settings(ctx.guild)
            emoji_list = []
            for index, key in enumerate(current_settings.keys()):
                to_send += f"{index+1}: **{key}** (current value: {current_settings[key]})\n"
                emoji_list.append(unicodedata.lookup(unicodedata.name(chr(ord(str(index+1))))) + "\u20E3")

            settings_message = await ctx.send(to_send[0:-1])

            for emoji in emoji_list:
                await settings_message.add_reaction(emoji)

            self.waiting_for_reactions[settings_message.id] = AwaitingReaction(ctx.message.author.id, emoji_list)

        else:
            to_send = "**Current Settings**\n"
            current_settings = self.get_server_settings(ctx.guild)
            for setting, value in current_settings.items():
                to_send += f"{setting}: {value}\n"

            await ctx.send(to_send[0:-1])


async def setup(bot):
    await bot.add_cog(SettingsCommands(bot))
