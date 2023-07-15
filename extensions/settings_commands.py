import discord
import json
from discord.ext import commands
from util.command_checks import check_higher_perms


class SettingsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = None
        self.load_settings()

    def load_settings(self):
        with open("util/settings.json") as settings_file:
            settings = json.load(settings_file)["guild_id"]
        self.settings = settings

    def update_settings(self):
        with open("util/settings.json", "w") as settings_file:
            json.dump({"guild_id": self.settings}, settings_file)

    def get_server_settings(self, guild: discord.Guild):
        try:
            return self.settings[str(guild.id)]
        except KeyError:
            default_settings = self.settings["0"]
            self.settings[str(guild.id)] = default_settings
            self.update_settings()
            return default_settings

    @commands.command(name="settings", description="A list of server settings which can be changed (requires admin)")
    async def settings(self, ctx: commands.Context, edit="no"):
        if not await check_higher_perms(ctx.author, ctx.guild):
            await ctx.send("You do not have access to this command.")
            return

        editing = True if edit == "edit" else False
        if editing:
            pass
        else:
            to_send = "**Current Settings**\n"
            current_settings = self.get_server_settings(ctx.guild)
            for setting, value in current_settings.items():
                to_send += f"{setting}: {value}\n"

            await ctx.send(to_send[0:-1])


async def setup(bot):
    await bot.add_cog(SettingsCommands(bot))
