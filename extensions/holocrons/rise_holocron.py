from discord.ext import commands

from entities.base_holocron import Holocron
from entities.locations import RiseLocation


class RiseHolocron(commands.Cog, Holocron):
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "rise")
        self.location_cls = RiseLocation
        # self.location_regex = compile(r"([a-z]+)?([0-9]+)?([a-z]+)?([0-9]+)?")

    def get_tips(self, location: RiseLocation, read_filters=None):
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

    def get_group_data(self, location: RiseLocation, override_feats=False):
        group_data = self.tip_storage[location.track_address]
        if not location.is_mid_level_location:
            # has to be on a planet
            # copied so the following mutations do not mutate tip_storage
            group_data = group_data[location.planet_address].copy()
            cm_data = group_data.pop('cm')

            new_group_data = {mission_type: data['tips'] for mission_type, data in group_data.items()}
            cm_data = {f"cm{idx}": tips for idx, tips in cm_data.items()}

            group_data = cm_data
            group_data.update(new_group_data)
        return group_data

    def cleanup_rise_data(self):
        response = []
        from collections import defaultdict
        top_level_tbr = []
        track_planet_tbr = {}
        planet_mission_tbr = defaultdict(dict)
        for track_name, track_data in self.tip_storage.items():
            address_lookup = {track_name: track_id for track_id, track_name in RiseLocation.tracks.items()}
            track_address = address_lookup[track_name]
            if track_address not in self.labels:
                top_level_tbr.append(track_name)
                continue

            planet_tbr = []
            for planet_id, planet_data in track_data.items():
                planet_label_address = track_address + str(planet_id)
                if planet_label_address not in self.labels[track_address]:
                    planet_tbr.append(planet_id)
                    track_planet_tbr[track_name] = planet_tbr
                    continue

                mission_tbr = []
                for mission_type, mission_data in planet_data.items():
                    mission_keys = []
                    if mission_type == 'cm':
                        mission_keys = [(planet_label_address + mission_type + str(mission_id), mission_id)
                                        for mission_id in mission_data.keys()]
                    if mission_type == 'sm':
                        mission_keys = [(planet_label_address + 'sm1', 'sm')]  # only one today

                    if mission_type == 'fleet':
                        mission_keys = [(planet_label_address + 'f', 'f')]

                    for mission_label_address, mission_id in mission_keys:
                        if mission_label_address not in self.labels[track_address][planet_label_address]:
                            mission_tbr.append((mission_type, mission_id))
                            planet_mission_tbr[track_name][planet_id] = mission_tbr

        for track_name, track_tbr in planet_mission_tbr.items():
            stored_track_data = self.tip_storage[track_name]
            for planet_key, mission_tbr in track_tbr.items():
                for mission_key, mission_id in mission_tbr:
                    stored_planet_data = stored_track_data[planet_key]
                    tbr_key = mission_key
                    if mission_key == 'cm':
                        stored_planet_data = stored_planet_data[mission_key]
                        tbr_key = mission_id
                    stored_planet_data.pop(tbr_key)
                    response.append(f'Removed {tbr_key} from {track_name}-{planet_key}')

        self.save_storage()

        return response or ["No further cleanup needed."]

    @commands.command(name="rise", aliases=["r"], extras={'is_holocron': True},
                      description="Access the Rise Holocron for reading and managing Rise Tips")
    async def rise_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(RiseHolocron(bot))
