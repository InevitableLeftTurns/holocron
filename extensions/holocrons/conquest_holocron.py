from discord.ext import commands

from entities.locations import ConquestLocation
from entities.tip import Tip
from entities.base_holocron import Holocron


class ConquestHolocron(commands.Cog, Holocron):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, "conquest")
        self.location_cls = ConquestLocation

    def dummy_populate(self):
        self.tip_storage["globals"][1].append(Tip(author="trich", content="this is a tip for g1"))
        self.tip_storage["globals"][1].append(Tip(author="trich", content="this is another tip for g1"))

        self.tip_storage["sectors"][1]["feats"][1] = [
            Tip(author="uaq", content="tip for s1f1a", rating=0),
            Tip(author="uaq", content="tip for s1f1b", rating=7),
            Tip(author="uaq", content="tip for s1f1c", rating=2),
            Tip(author="uaq", content="tip for s1f1d", rating=4)
        ]

        self.tip_storage["sectors"][1]["nodes"][1] = [Tip(author="uaq", content="tip for s1n1")]
        self.tip_storage["sectors"][1]["nodes"][13] = [
            Tip(author="uaq", content="tip for s1n13a", rating=0),
            Tip(author="uaq", content="tip for s1n13b", rating=7),
            Tip(author="uaq", content="tip for s1n13c", rating=-3)
        ]

        self.tip_storage["sectors"][1]["boss"]["feats"][1] = [
            Tip(author="uaq", content="tip for s1b1a", rating=0),
            Tip(author="uaq", content="tip for s1b1b", rating=7),
            Tip(author="uaq", content="tip for s1b1c", rating=2),
            Tip(author="uaq", content="tip for s1b1d", rating=4),
        ]
        self.tip_storage["sectors"][1]["boss"]["tips"] = [Tip(author="uaq", content="tip for s1b")]

        self.tip_storage["sectors"][1]["mini"]["feats"][1] = [Tip(author="uaq", content="tip for s1m1")]
        self.tip_storage["sectors"][1]["mini"]["tips"] = [Tip(author="uaq", content="tip for s1m")]

        self.tip_storage["globals"][1] = [
            Tip(author="uaq", content="tip 1 to del in g1", user_id=490970360272125952),
            Tip(author="uaq", content="tip 2 to del in g1", user_id=490970360272125952),
            Tip(author="uaq", content="tip 3 to del in g1", user_id=490970360272125952),
            Tip(author="uaq", content="tip 4 to del in g1", user_id=490970360272125952),
            Tip(author="uaq", content="tip 5 to del in g1", user_id=490970360272125952)
        ]

        self.save_storage()

    def get_tips(self, location: ConquestLocation):
        tip_group = self.get_group_data(location)

        if location.is_group_location:
            return tip_group

        if location.sector_node_type_id == 'n' and location.feat_address not in tip_group:
            # nodes are not pre-assembled and may be missing
            tip_group[location.feat_address] = []
        return tip_group[location.feat_address]

    def get_group_data(self, location: ConquestLocation, override_feats=False):
        group_data = self.tip_storage[location.feat_location_address]
        if location.is_sector_location:
            group_data = group_data[location.sector_address][location.sector_node_type_address]
            if not override_feats and location.is_boss_location and location.is_group_location:
                # boss tips
                group_data = group_data['tips']
            elif location.is_boss_location:
                # boss or sector feat tips
                group_data = group_data['feats']
        return group_data

    @commands.command(name="conquest", aliases=["c", "con", "conq"], extras={'is_holocron': True},
                      description="Access the Conquest Holocron for reading and managing Conquest Tips")
    async def conquest_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(ConquestHolocron(bot))
