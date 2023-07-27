from discord.ext import commands
from util.response_handler import get_response_type


class BaseCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot loaded successfully. Logged in as '{self.bot.user}'")

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
    async def _help(self, ctx: commands.Context, *command_list):
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)
        to_send = ""
        for command in command_list:
            bot_command = self.bot.get_command(command)

            if bot_command is not None:
                aliases = "none" if len(bot_command.aliases) == 0 else ", ".join(bot_command.aliases)
                to_send += f"**{ctx.prefix}{bot_command.name}** (aliases: {aliases})\n"
                if command == "help":
                    to_send += f"A command that gives you a list of commands, or help on specific ones.\n" \
                               f"To get a list of commands, use `{ctx.prefix}help`, or for help on a certain command," \
                               f" use `{ctx.prefix}help [command]`.\n\n"
                elif command == "tips":
                    to_send += f"A command to request tips for the currently active conquest.\n" \
                               f"To get tips on Global Feats, use `{ctx.prefix}tips g[number (1-8)]`. " \
                               f"(ex: `{ctx.prefix}tips g3`)\n" \
                               f"To get tips on Sectors, use `{ctx.prefix}tips s[number (1-5)][type (b,m,n,f)]" \
                               f"[number (optional)]`." \
                               f"\n(ex: `{ctx.prefix}tips s3b` for Sector 3 Boss tips. `{ctx.prefix}tips s1n13` for " \
                               f"Sector 1 Node 13 tips. `{ctx.prefix}tips s5f2` for Sector 5 Feat 2 tips.)\n\n"
                else:
                    to_send += f"[basic decripton]\n" \
                               f"{bot_command.description}\n\n"

            else:
                to_send += f"The command `{ctx.prefix}{command}` does not exist"

        if to_send == "":
            to_send = f"**List of Commands**. For detailed help, use `{ctx.prefix}help [command]`\n"
            for com in self.bot.commands:
                aliases = "none" if len(com.aliases) == 0 else ", ".join(com.aliases)
                to_send += f"**{ctx.prefix}{com.name}** (aliases: {aliases})\n" \
                           f"{com.description}\n\n"

        await response_method.send(to_send[0:-2])

async def setup(bot):
    await bot.add_cog(BaseCommands(bot))
