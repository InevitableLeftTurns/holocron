import discord
from discord.ext import commands
from discord.utils import get

from entities.command_parser import HolocronCommand
from entities.locations import InvalidLocationError
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
        bot_perm_role = get(guild.roles, name="Holocron Admin")
        if bot_perm_role is None:
            bot_perm_role = await guild.create_role(name="Holocron Admin")
        bot = guild.get_member(self.bot.user.id)
        await bot.add_roles(bot_perm_role)

    @commands.Cog.listener()  # ignores response setting, always in-channel
    async def on_command_error(self, ctx: commands.Context, exception: commands.CommandInvokeError):
        if ctx.command is None:
            message_content = ctx.message.content
            space_index = message_content.find(" ")
            if space_index != -1:
                command_component = message_content[0:space_index]
            else:
                command_component = message_content
            await ctx.send(f"The command `{command_component}` does not exist. For a list of commands, use "
                           f"`{ctx.prefix}help`.")
            return

        python_exception = exception.original
        if isinstance(python_exception, InvalidLocationError):
            await ctx.send(python_exception.args[0])
            return
        else:
            await ctx.send(f"[TEMP] Error on command `{ctx.prefix}{ctx.command.name}`: {exception}")

    @commands.command(name="help", aliases=["h"], description="Provides help on Holocron and admin commands.")
    async def _help(self, ctx: commands.Context, *requested):
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)

        try:
            command = requested[0]
            command_args = requested[1:]
        except IndexError:
            command = ""
            command_args = tuple()

        bot_command = self.bot.get_command(command)
        holocron_command = HolocronCommand('help', *command_args)
        response = helpmgr.generate_bot_help(bot_command, ctx, holocron_command.help_section)

        if len(response) == 0:
            response = [f"**List of Holocrons and Commands**.\nFor detailed help, "
                        f"use `{ctx.prefix}help [holocron|command]`\n"]
            sorted_commands = sorted(self.bot.commands,
                                     key=lambda comm: comm.name if comm.extras.get('is_holocron', False) is True
                                     else 'zz' + comm.name)
            response.append('**Holocrons**')

            found_command = False
            for com in sorted_commands:
                if not found_command and not com.extras.get('is_holocron'):
                    found_command = True
                    response.append('**Commands**')

                aliases = "none" if len(com.aliases) == 0 else ", ".join(com.aliases)
                response.append(f"\t**{ctx.prefix}{com.name}** (aliases: {aliases})\n"
                                f"\t{com.description}\n")

            response.append("To submit feature requests, bug reports, or general comments:"
                            " [Holocron Tracker](https://github.com/InevitableLeftTurns/holocron_tracker/issues)")

        await response_method.send("\n".join(response), suppress_embeds=True)


async def setup(bot):
    await bot.add_cog(BaseCommands(bot))
