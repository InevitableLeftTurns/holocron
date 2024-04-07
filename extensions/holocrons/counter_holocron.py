from discord.ext import commands

from entities.counters import Squad, CounterTip
from entities.locations import CounterLocation
from entities.base_holocron import Holocron
from util.settings.tip_sorting_handler import sort_tips


class CounterHolocron(commands.Cog, Holocron):
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "counter")
        self.location_cls = CounterLocation
        self.labels = self.tip_storage

    def dummy_populate(self):
        jmk = Squad(lead_id="jmk", lead="Jedi Master Kenobi", squad="JMK/CAT/GK/Padme/Ahsoka", author="trich")
        see = Squad(lead_id="see", lead="Sith Eternal Emperor", squad="SEE/Bane", variants=["SEE/Wat", "SEE/Darth Malak"], author="trich")
        self.tip_storage["squads"][jmk.lead_id] = jmk
        self.tip_storage["squads"][see.lead_id] = see

        self.tip_storage["tips"][jmk.uid] = [
            CounterTip(jmk.uid, author="uaq", content="I'm running 2 leaders resolve and a green ZA; Han shoots Echo, Dash nuke; works down to 30% - probably more if I was a touch faster.", rating=0),
            CounterTip(jmk.uid, author="uaq", content="tip 2 for jmk", activity="GAC", rating=0),
            CounterTip(jmk.uid, author="uaq", content="tip 3 for jmk", rating=0),
            CounterTip(jmk.uid, author="trich", content="tip 4 for jmk for GAC 3v3", activity="GAC3", rating=0),
            CounterTip(jmk.uid, author="trich", content="tip 5 for jmk for TW", activity="TW", rating=0),
        ]

        self.tip_storage["tips"][see.uid] = [
            CounterTip(see.uid, author="uaq", content="tip 1 for see", rating=0),
            CounterTip(see.uid, author="uaq", content="tip 2 for see", rating=0),
            CounterTip(see.uid, author="uaq", content="tip 3 for see", rating=0),
        ]

        self.tip_storage["aliases"]["glk"] = jmk.uid

        self.save_storage()

    def format_tips(self, location: CounterLocation, read_filters=None):
        counter_tips = self.get_tips(location, read_filters=read_filters)
        total = len(counter_tips)
        sort_tips(counter_tips)
        top_n = counter_tips[:self._read_depth(read_filters)]
        detail = location.get_detail()

        if len(top_n) > 0:
            output = [f"__**Recent tip{'' if len(top_n) == 1 else 's'} "
                      f"for {location.get_location_name()}**__\n"]

            if detail:
                output.append(detail)

            counter = 0
            for index, tip in enumerate(top_n):
                counter = index + 1
                output.append(f"{counter} - " + tip.create_tip_message())

            return '\n'.join(output)
        else:
            output = ""
            if detail:
                output += f"{detail}\n"
            output += f"There are no tips for {location.get_location_name()}."
            return output

    def get_tips(self, location: CounterLocation, read_filters=None):
        squad = self.tip_storage["squads"][location.actual_squad_lead_id]
        tips = self.tip_storage["tips"][squad.uid]

        activity = location.check_activity(read_filters)
        if activity:
            tips = [tip for tip in tips if tip.activity == activity]
        return tips

    def get_all_tips(self):
        all_tips = []
        for squad_uid, tips in self.tip_storage["tips"].items():
            all_tips.extend(tips)
        return all_tips

    def generate_stats_report(self):
        total_squad_count = len(self.tip_storage["squads"])
        total_alias_count = len(self.tip_storage["aliases"])
        total_tip_count = 0
        for squad_uid, tips in self.tip_storage["tips"].items():
            total_tip_count += len(tips)
        return f"Counter Holocron Total Squads: {total_squad_count}\n" \
               f"Counter Holocron Total Tips: {total_tip_count}\n" \
               f"Counter Holocron Aliases: {total_alias_count}\n"

    def get_group_data(self, location: CounterLocation, feats=False):
        raise NotImplementedError

    def get_map_name(self, location: CounterLocation, *args):
        raise NotImplementedError

    def load_labels(self):
        pass

    def config_to_storage(self, config: dict):
        return config

    @commands.command(name="counter", aliases=["ctr"], extras={'is_holocron': True},
                      description="Access the Counter Holocron for reading and managing Territory War "
                                  "and Grand Arena Championship Counter Tips")
    async def counter_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(CounterHolocron(bot))
