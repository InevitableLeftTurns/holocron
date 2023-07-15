import discord
from discord.ext import commands
from util.global_constants import bot_prefix


class BaseCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot loaded successfully. Logged in as '{self.bot.user}'")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception):
        if ctx.command is None:
            message_content = ctx.message.content
            space_index = message_content.find(" ")
            if space_index != -1:
                command_component = message_content[0:space_index]
            else:
                command_component = message_content
            await ctx.send(f"The command `{command_component}` does not exist. For a list of commands, use "
                           f"`{bot_prefix}help`.")
        else:
            await ctx.send(f"[TEMP] Error on command `{bot_prefix}{ctx.command.name}`: {exception}")

    @commands.command(name="help", description="Gives info on certain commands, or a list of commands")
    async def _help(self, ctx: commands.Context, *command_list):
        await ctx.send(f"[TEMP] Help is on the way: {', '.join(command_list)}")

async def setup(bot):
    await bot.add_cog(BaseCommands(bot))
