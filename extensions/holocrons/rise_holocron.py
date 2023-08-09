from discord.ext import commands
from re import compile
from util.base_holocron import Holocron, InvalidLocationError


class RiseHolocron(commands.Cog, Holocron):
    @commands.command("error")
    async def _error(self, ctx):
        raise NotImplementedError
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "rise")
        self.location_regex = compile(r"([a-z]+)?([0-9]+)?([a-z]+)?([0-9]+)?")

    valid_sides = {
        "ds": "darkside",
        "mx": "mixed",
        "ls": "lightside",
        "lsb": "lightsidebonus"
    }
    valid_missions = {
        "cm": "cm",
        "f": "fleet",
        "sm": "sm"
    }

    def valid_location(self, location):
        location_fragments = self.location_regex.match(location).groups()

        try:
            side = self.valid_sides[location_fragments[0]]
        except (IndexError, KeyError):
            raise InvalidLocationError("Invalid or missing location. Queries to tips must start with `ds` for "
                                       "`darkside`, `mx` for `mixed`, `ls` for `lightside`, or `lsb` for `lightside "
                                       "bonus`.")

        try:
            planet_num = int(location_fragments[1])
            # noinspection PyStatementEffect
            self.tip_storage[side][planet_num]
        except (IndexError, ValueError, TypeError):
            raise InvalidLocationError("The character following your side must be a number identifying which planet to "
                                       "query.")
        except KeyError:
            raise InvalidLocationError("The number following your side must be between 1 and 6 (inclusive).")

        try:
            mission_type = self.valid_missions[location_fragments[2]]
        except (IndexError, KeyError, TypeError):
            raise InvalidLocationError("Characters following planet number must be `cm` for `combat missions`, `f` for "
                                       "`fleet battles`, or `sm` for `special missions`.")

        if mission_type == "cm":
            try:
                combat_num = int(location_fragments[3])
                # noinspection PyStatementEffect
                self.tip_storage[side][planet_num][mission_type][combat_num]
            except (IndexError, ValueError, TypeError):
                raise InvalidLocationError("Combat missions require numbers indicating which mission to query. Combat "
                                           "missions are numbered from left to right.")
            except KeyError:
                # noinspection PyUnboundLocalVariable
                raise InvalidLocationError(f"Combat mission {combat_num} does not exist. Combat mission number for this"
                                           f" planet must be between 1 and "
                                           f"{len(self.tip_storage[side][planet_num][mission_type].keys())} "
                                           f"(inclusive).")

        return True

    def get_tips(self, location):
        location_fragments = self.location_regex.match(location).groups()

        side = self.valid_sides[location_fragments[0]]
        planet = int(location_fragments[1])
        mission = self.valid_missions[location_fragments[2]]

        if mission == "cm":
            mission_num = int(location_fragments[3])
            return self.tip_storage[side][planet][mission][mission_num]
        return self.tip_storage[side][planet][mission]["tips"]

    def get_map_name(self, location, *args):
        try:
            track_loc = location[0:2]
            planet_loc = location[0:3]
        except IndexError:
            return "Invalid location given `location`. Must be a 3-character track+planet location. ex: `ds2`"

        track_data = self.labels.get(track_loc, {})
        planet_data = track_data.get(planet_loc, location)
        return planet_data['name']

    def get_label(self, location):
        track_loc = location[0:2]
        planet_loc = location[0:3]
        try:
            track = self.labels[track_loc]
            planet = track[planet_loc]
            labels = planet[location]

            planet_name = planet['name']
            reqs = labels['reqs']

            waves = labels['enemies']
            if isinstance(waves, list):
                waves = [f"Wave {idx+1}: {wave}" for idx, wave in enumerate(waves)]
                waves = '\n'.join(waves)

            return f"{planet_name}\nRequirements: {reqs}\n{waves}"
        except KeyError:
            return None

    @commands.command(name="rise", aliases=["r"], extras={'is_holocron': True},
                      description="Access the Rise Holocron for reading and managing Rise Tips")
    async def rise_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(RiseHolocron(bot))
