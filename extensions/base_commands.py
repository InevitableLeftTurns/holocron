import discord
from discord.ext import commands
from discord.utils import get

from util import helpmgr
from util.settings.response_handler import get_response_type


class BaseCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot loaded successfully. Logged in as '{self.bot.user}'")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        bot_perm_role = get(guild.roles, name="Conquest Admin")
        if bot_perm_role is None:
            bot_perm_role = await guild.create_role(name="Conquest Admin")
        bot = guild.get_member(self.bot.user.id)
        await bot.add_roles(bot_perm_role)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception):  # ignores response setting, always in-channel
        if ctx.command is None:
            message_content = ctx.message.content
            space_index = message_content.find(" ")
            if space_index != -1:
                command_component = message_content[0:space_index]
            else:
                command_component = message_content
            await ctx.send(f"The command `{command_component}` does not exist. For a list of commands, use "
                           f"`{ctx.prefix}help`.")
        else:
            await ctx.send(f"[TEMP] Error on command `{ctx.prefix}{ctx.command.name}`: {exception}")

    @commands.command(name="help", aliases=["h"], description="Gives info on certain commands, or a list of commands")
    async def _help(self, ctx: commands.Context, *requested):
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)

        try:
            command = requested[0]
            commands_args = requested[1:]
        except IndexError:
            command = ""
            commands_args = tuple()

        bot_command = self.bot.get_command(command)
        response = helpmgr.generate_bot_help(bot_command, ctx, *commands_args)

        if len(response) == 0:
            response = [f"**List of Commands**. For detailed help, use `{ctx.prefix}help [command]`"]
            for com in self.bot.commands:
                aliases = "none" if len(com.aliases) == 0 else ", ".join(com.aliases)
                response.append(f"**{ctx.prefix}{com.name}** (aliases: {aliases})\n"
                                f"{com.description}\n")

        await response_method.send("\n".join(response))


async def setup(bot):
    await bot.add_cog(BaseCommands(bot))
