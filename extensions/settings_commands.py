import discord
import json
from discord.ext import commands
from util.command_checks import check_higher_perms
from collections import namedtuple
from util.prefix_handler import bot_prefixes, check_prefix_valid, set_prefix
from util.response_handler import response_settings, check_set_response, set_response_method, get_response_type

AwaitingReaction = namedtuple("AwaitingReaction", ["user_id", "allowed_emoji"])


class SettingsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = None
        self.load_settings()
        self.waiting_for_reactions = {}

    def load_settings(self):
        with open("data/settings.json") as settings_file:
            settings = json.load(settings_file)["guild_id"]
        self.settings = settings

        defaults = settings["0"]
        for guild_id, settings in settings.items():
            bot_prefixes[guild_id] = settings.get("Bot Prefix", defaults["Bot Prefix"])
            response_settings[guild_id] = settings.get("Response Method", defaults["Response Method"])

    def update_settings(self):
        with open("data/settings.json", "w") as settings_file:
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

        setting_index = int(reaction.emoji[0]) - 1
        current_settings = self.get_server_settings(reaction.message.guild)
        key_list = [key for key in current_settings.keys()]
        setting_accepted = False
        new_setting = None
        setting_hints = [
            None,
            "channel, dm"
        ]
        hints = "" if setting_hints[setting_index] is None else f"({setting_hints[setting_index]})"
        setting_checks = [
            check_prefix_valid,
            check_set_response
        ]
        error_messages = [
            "That prefix has been rejected. Try a shorter prefix, or one without a space.",
            "To change response method, choose `channel` to change response method to the messaged channel, "
            "or `dm` to change response method to DM's"
        ]
        setting_specific_functions = [
            set_prefix,
            set_response_method
        ]

        await channel.send(f"What should `{key_list[setting_index]}` be changed to? {hints}")

        while not setting_accepted:
            new_setting = await self.bot.wait_for("message", check=check_message)
            setting_accepted = setting_checks[setting_index](new_setting)
            if not setting_accepted:
                await channel.send(error_messages[setting_index])

        guild_id_key = str(new_setting.guild.id)
        content = new_setting.content

        setting_specific_functions[setting_index](guild_id_key, content)

        response_method = get_response_type(new_setting.guild, new_setting.author, channel)
        await self.set_new_setting(guild_id_key, key_list[setting_index], content, response_method)

    async def set_new_setting(self, id_key, setting_key, new_value, response_method):
        self.settings[id_key][setting_key] = new_value
        self.update_settings()
        await response_method.send(f"Set `{setting_key}` to `{new_value}`")

    @commands.command(name="settings", description="A list of server settings which can be changed (requires admin)")
    async def settings(self, ctx: commands.Context, edit="no"):
        current_settings = self.get_server_settings(ctx.guild)
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)
        if not await check_higher_perms(ctx.author, ctx.guild):
            await response_method.send("You do not have access to this command.")
            return

        editing = True if edit == "edit" else False
        if editing:
            response = ["Which setting do you want to change?"]

            emoji_list = []
            for index, key in enumerate(current_settings.keys()):
                response.append(f"{index + 1}: {key} (current value: `{current_settings[key]}`)")
                emoji_list.append(str(index + 1) + "\u20E3")

            # ignores response setting, always in-channel (due to how settings are stored/changed. might be 'fixable')
            settings_message = await ctx.send("\n".join(response))

            self.waiting_for_reactions[settings_message.id] = AwaitingReaction(ctx.message.author.id, emoji_list)

            for emoji in emoji_list:
                await settings_message.add_reaction(emoji)

        else:
            response = ["**Current Settings**"]
            for setting, value in current_settings.items():
                response.append(f"{setting}: `{value}`")

            await response_method.send("\n".join(response))


async def setup(bot):
    await bot.add_cog(SettingsCommands(bot))
