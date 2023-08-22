from discord.ext import commands
from entities.base_holocron import Holocron
from entities.locations import RiseLocation


class RiseHolocron(commands.Cog, Holocron):
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "rise")
        self.location_cls = RiseLocation
        # self.location_regex = compile(r"([a-z]+)?([0-9]+)?([a-z]+)?([0-9]+)?")

    def get_tips(self, location: RiseLocation):
        track_data = self.tip_storage[location.track_address]
        planet_data = track_data[location.planet_address]
        mission_data = planet_data[location.mission_type_address]
        if location.mission_type_id == 'cm':
            # only cm's have #s for now. ignore sm #s
            if location.mission_address:
                mission_data = mission_data[location.mission_address]
            return mission_data
        return mission_data["tips"]

    def get_all_tips(self):
        all_tips = []
        for track_id, track_data in self.tip_storage.items():
            for planet_id, planet_data in track_data.items():
                for mission_type_id, mission_data in planet_data.items():
                    if mission_type_id == 'cm':
                        # only cm's have #s for now. ignore sm #s
                        for mission_id, mission_tips in mission_data.items():
                            all_tips.extend(mission_tips)
                    else:
                        all_tips.extend(mission_data["tips"])
        return all_tips

    def generate_stats_report(self):
        total_tips_count = 0
        msg = ""
        address_lookup = {track_name: track_id for track_id, track_name in RiseLocation.tracks.items()}

        for track_name, track_data in self.tip_storage.items():
            track_tip_count = 0
            track_msg = ""
            track_id = address_lookup[track_name]
            track_label = self.labels[track_id]['name']
            for planet_id, planet_data in track_data.items():
                if planet_id > 3 or (track_id == 'lsb' and planet_id > 1):
                    # temporary until further progress on Rise is made
                    continue
                planet_tip_count = 0
                for mission_type_id, mission_data in planet_data.items():
                    if mission_type_id == 'cm':
                        # only cm's have #s for now. ignore sm #s
                        for mission_id, mission_tips in mission_data.items():
                            planet_tip_count += len(mission_tips)
                    else:
                        planet_tip_count += len(mission_data["tips"])
                planet_address = str(track_id) + str(planet_id)
                track_msg += f"- Tips for {self.labels[track_id][planet_address]['name']}: {planet_tip_count}\n"
                track_tip_count += planet_tip_count
            msg += f"Tips for {track_label}: {track_tip_count}\n"
            msg += track_msg
            total_tips_count += track_tip_count

        msg = f"**Rise of the Empire Total Tips**: {total_tips_count}\n" + msg

        return msg

    @commands.command(name="rise", aliases=["r"], extras={'is_holocron': True},
                      description="Access the Rise Holocron for reading and managing Rise Tips")
    async def rise_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(RiseHolocron(bot))
