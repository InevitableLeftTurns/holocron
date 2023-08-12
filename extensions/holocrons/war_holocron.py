from util.base_holocron import Holocron
from discord.ext import commands


class WarHolocron(commands.Cog, Holocron):
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "war")

    def valid_location(self, location):
        if location:
            if location not in self.tip_storage:
                self.tip_storage[location] = []
            return True
        return False

    def dummy_populate(self):
        pass

    def format_tips(self, location, depth=5):
        return super().format_tips(location, depth)

    def is_group_location(self, location: str):
        return False

    def get_tips(self, location):
        # location is a leader name, so can be anything
        return self.tip_storage[location]

    def get_group_data(self, location, feats=False):
        raise NotImplementedError

    def get_map_name(self, location, *args):
        raise NotImplementedError

    @commands.command(name="war", aliases=["tw, gac, counter"], extras={'is_holocron': True},
                      description="Access the War Holocron for reading and managing Territory War "
                                  "and Grand Arena Championship Counter Tips")
    async def war_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(WarHolocron(bot))
