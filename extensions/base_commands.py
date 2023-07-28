import discord
from discord.ext import commands
from discord.utils import get
from util.response_handler import get_response_type


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
        except IndexError:
            command = ""

        response = []
        bot_command = self.bot.get_command(command)
        if bot_command is not None:
            aliases = "none" if len(bot_command.aliases) == 0 else ", ".join(bot_command.aliases)
            com_name = bot_command.name
            response.append(f"**{ctx.prefix}{com_name}** (aliases: {aliases})")
            if com_name == "help":
                response.append(f"A command that gives you a list of commands, or help on specific ones.\n"
                                f"To get a list of commands, use `{ctx.prefix}help`, or for help on a certain "
                                f"command, use `{ctx.prefix}help [command]`.")

            elif com_name == "conquest":
                try:
                    loc_help = requested[1] == "location"
                except IndexError:
                    loc_help = False

                if loc_help:
                    response.append("Conquest location syntax will depend on what kind of location it is:\n"
                                    "* Global Feats- global feats consist of `g` and a number representing which feat. "
                                    "ex: `g3`\n"
                                    "* Sector Tips- Each kind of sector tip has a slightly different syntax, detailed "
                                    "below, but all start with `s` and a number representing which sector. ex: `s2`.\n"
                                    " * Boss- add `b`. Adding a number will query boss feats, while leaving out a "
                                    "number will query the boss itself. ex: `s2b3` or `s2b`\n"
                                    " * Miniboss- add `m`. Same syntax as boss. ex: `s4m2` or `s4m`\n"
                                    " * Nodes- add `n` and a number representing which node. ex: `s3n16`\n"
                                    " * Feats- add `f` and a number representing which feat. ex: `s1f3`")
                else:
                    response.append(f"A command to manage tips for the currently active conquest. Start with "
                                    f"`{ctx.prefix}conquest`, then follow with options from below.\n"
                                    f"*Accessing Tips*- Simply place a `location` following `{ctx.prefix}conquest`. "
                                    f"ex: `{ctx.prefix}conquest s1f2`. For help with locations, use "
                                    f"`{ctx.prefix}help conquest location`.\n"
                                    f"*Tip Modification*- For the below modifications, place the corresponding tag "
                                    f"after your location. ex: `{ctx.prefix}conquest s1f2 add`\n"
                                    f"* Adding Tips- `add`.\n"
                                    f"* Editing Tips- `edit`. You can only edit your own tips unless you have the "
                                    f"permission role.\n"
                                    f"* Deleting Tips- `delete`. You can only delete your own tips unless you have the "
                                    f"permission role.\n"
                                    f"* Clearing Tips- `clear`. Permission role required. Clears all tips in "
                                    f"all locations. Intended for when conquests end.")

            elif com_name == "settings":
                response.append(f"A list of settings applied to the server and their current values. To edit server "
                                f"settings, you must have the permission role, then use `{ctx.prefix}settings edit`.")
            else:
                response.append(f"({bot_command.name} has no help section. Refering to description.)\n"
                                f"{bot_command.description}")

        elif command != "":
            response.append(f"The command `{ctx.prefix}{command}` does not exist")

        if len(response) == 0:
            response = [f"**List of Commands**. For detailed help, use `{ctx.prefix}help [command]`"]
            for com in self.bot.commands:
                aliases = "none" if len(com.aliases) == 0 else ", ".join(com.aliases)
                response.append(f"**{ctx.prefix}{com.name}** (aliases: {aliases})\n"
                                f"{com.description}\n")

        await response_method.send("\n".join(response))


async def setup(bot):
    await bot.add_cog(BaseCommands(bot))
