from discord.ext import commands
from util.Holocron import Holocron


class RiseHolocron(commands.Cog, Holocron):
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "rise")

    valid_sides = {
        "d": "darkside",
        "l": "lightside",
        "m": "mixed",
        "b": "lightsidebonus"
    }
    valid_missions = {
        "c": "cm",
        "f": "fleet",
        "s": "sm"
    }

    async def valid_location(self, location, response_method):

        try:
            side = self.valid_sides[location[0]]
        except KeyError:
            await response_method.send("Tip Locations must start with `d` for `darkside`, `m` for `mixed`, `l` for "
                                       "`lightside`, or `b` for `lightside bonus`.")
            return False

        try:
            planet_num = int(location[1])
            # noinspection PyStatementEffect
            self.tip_storage[side][planet_num]
        except (IndexError, ValueError):
            await response_method.send("Tip locations following a side must be a number, representing which planet to "
                                       "query for tips.")
            return False
        except KeyError:
            await response_method.send("Planet number must be between 1 and 6 (inclusive).")
            return False

        try:
            mission_type = self.valid_missions[location[2]]
        except (IndexError, KeyError):
            await response_method.send("Tip locations following a planet number must be a mission type. Use `c` for "
                                       "`[TEMP]casual missions`, `f` for `fleet` or `s` for `[TEMP]special missions`.")
            return False

        if mission_type == "cm":
            try:
                cm_num = int(location[3])
                # noinspection PyStatementEffect
                self.tip_storage[side][planet_num][mission_type][cm_num]
            except (IndexError, ValueError):
                await response_method.send("Casual Missions must have a number representing which mission to select. "
                                           "Missions are ordered from left to right.")
                return False
            except KeyError:
                await response_method.send(f"Mission number must be between 1 and "
                                           f"{len(self.tip_storage[side][planet_num][mission_type].items())} "
                                           f"(inclusive).")
                return False

        return True

    def get_tips(self, location):
        side = self.valid_sides[location[0]]
        planet = int(location[1])
        mission = self.valid_missions[location[2]]

        if mission == "cm":
            mission_num = int(location[3])
            return self.tip_storage[side][planet][mission][mission_num]
        return self.tip_storage[side][planet][mission]["tips"]

    @commands.command(name="rise", aliases=["r"], extras={'is_holocron': True},
                      description="Access the Rise Holocron for reading and managing Rise Tips")
    async def rise_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(RiseHolocron(bot))
