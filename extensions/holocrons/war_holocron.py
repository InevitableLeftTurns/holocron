from discord.ext import commands

from entities.locations import WarLocation
from util.base_holocron import Holocron


class WarHolocron(commands.Cog, Holocron):
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "war")
        self.location_cls = WarLocation

    def dummy_populate(self):
        pass

    def format_tips(self, location: WarLocation, depth=5):
        return super().format_tips(location, depth)

    def get_tips(self, location: WarLocation):
        # location is a leader name, so can be anything
        return self.tip_storage[location.address]

    def get_group_data(self, location: WarLocation, feats=False):
        raise NotImplementedError

    def get_map_name(self, location: WarLocation, *args):
        raise NotImplementedError

    @commands.command(name="war", aliases=["tw, gac, counter"], extras={'is_holocron': True},
                      description="Access the War Holocron for reading and managing Territory War "
                                  "and Grand Arena Championship Counter Tips")
    async def war_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(WarHolocron(bot))
