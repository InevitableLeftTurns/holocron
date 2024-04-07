from discord.ext import commands

from entities.base_holocron import Holocron
from entities.locations import ConquestLocation
from entities.tip import Tip


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

    def get_tips(self, location: ConquestLocation, read_filters=None):
        tip_group = self.get_group_data(location)

        if location.is_group_location:
            return tip_group

        if location.sector_node_type_id == 'n' and location.feat_address not in tip_group:
            # nodes are not pre-assembled and may be missing
            tip_group[location.feat_address] = []
        return tip_group[location.feat_address]

    def get_all_tips(self):
        all_tips = []
        # globals
        for global_feat_tips in self.tip_storage['globals'].values():
            all_tips.extend(global_feat_tips)

        for sector_num, nodes in self.tip_storage['sectors'].items():
            for node_type, subtypes in nodes.items():
                if node_type in ['feats', 'nodes']:
                    for feat_id, tips in subtypes.items():
                        all_tips.extend(tips)
                if node_type in ['boss', 'mini']:
                    boss_feats = subtypes['feats']
                    for feat_id, tips in boss_feats.items():
                        all_tips.extend(tips)
                    boss_tips = subtypes['tips']
                    all_tips.extend(boss_tips)

        return all_tips

    def generate_stats_report(self):
        total_tips_count = 0
        global_tips_count = 0
        sector_tips = {sector_num: 0 for sector_num in self.tip_storage['sectors']}

        for global_feat_tips in self.tip_storage['globals'].values():
            tips_count = len(global_feat_tips)
            total_tips_count += tips_count
            global_tips_count += tips_count

        for sector_num, nodes in self.tip_storage['sectors'].items():
            sector_tip_count = 0
            for node_type, subtypes in nodes.items():
                if node_type in ['feats', 'nodes']:
                    for feat_id, tips in subtypes.items():
                        sector_tip_count += len(tips)
                if node_type in ['boss', 'mini']:
                    boss_feats = subtypes['feats']
                    for feat_id, tips in boss_feats.items():
                        sector_tip_count += len(tips)
                    boss_tips = subtypes['tips']
                    sector_tip_count += len(boss_tips)
            sector_tips[sector_num] = sector_tip_count
            total_tips_count += sector_tip_count

        msg = f"**Total Tips for Conquest**: {total_tips_count}\n"
        msg += f"Total Global Feat Tips: {global_tips_count}\n"
        for sector_num, sector_tip_count in sector_tips.items():
            msg += f"Total Tips in Sector {sector_num}: {sector_tip_count}\n"

        return msg

    def get_group_data(self, location: ConquestLocation, override_feats=False):
        group_data = self.tip_storage[location.feat_location_address]
        if not location.is_mid_level_location and location.is_sector_location:
            group_data = group_data[location.sector_address][location.sector_node_type_address]
            if not override_feats and location.is_boss_location and location.is_group_location:
                # boss tips
                group_data = group_data['tips']
            elif location.is_boss_location:
                # boss or sector feat tips
                group_data = group_data['feats']
        if location.is_mid_level_location and location.sector_address:
            group_data = group_data[location.sector_address]
        return group_data

    @commands.command(name="conquest", aliases=["c", "con", "conq"], extras={'is_holocron': True},
                      description="Access the Conquest Holocron for reading and managing Conquest Tips")
    async def conquest_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(ConquestHolocron(bot))
