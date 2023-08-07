from data.Tip import Tip
from discord.ext import commands
from util.Holocron import Holocron


class ConquestHolocron(commands.Cog, Holocron):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, "conquest")

    tip_types = {
        "b": "boss",
        "m": "mini",
        "n": "nodes",
        "f": "feats"
    }

    def dummy_populate(self):
        self.tip_storage["globals"][1].append(Tip("trich", "this is a tip for g1"))
        self.tip_storage["globals"][1].append(Tip("trich", "this is another tip for g1"))

        self.tip_storage["sectors"][1]["feats"][1] = [
            Tip("uaq", "tip for s1f1a", 0),
            Tip("uaq", "tip for s1f1b", 7),
            Tip("uaq", "tip for s1f1c", 2),
            Tip("uaq", "tip for s1f1d", 4)
        ]

        self.tip_storage["sectors"][1]["nodes"][1] = [Tip("uaq", "tip for s1n1")]
        self.tip_storage["sectors"][1]["nodes"][13] = [
            Tip("uaq", "tip for s1n13a", 0),
            Tip("uaq", "tip for s1n13b", 7),
            Tip("uaq", "tip for s1n13c", -3)
        ]

        self.tip_storage["sectors"][1]["boss"]["feats"][1] = [
            Tip("uaq", "tip for s1b1a", 0),
            Tip("uaq", "tip for s1b1b", 7),
            Tip("uaq", "tip for s1b1c", 2),
            Tip("uaq", "tip for s1b1d", 4),
        ]
        self.tip_storage["sectors"][1]["boss"]["tips"] = [Tip("uaq", "tip for s1b")]

        self.tip_storage["sectors"][1]["mini"]["feats"][1] = [Tip("uaq", "tip for s1m1")]
        self.tip_storage["sectors"][1]["mini"]["tips"] = [Tip("uaq", "tip for s1m")]

        self.tip_storage["globals"][1] = [
            Tip("uaq", "tip 1 to del in g1", user_id=490970360272125952),
            Tip("uaq", "tip 2 to del in g1", user_id=490970360272125952),
            Tip("uaq", "tip 3 to del in g1", user_id=490970360272125952),
            Tip("uaq", "tip 4 to del in g1", user_id=490970360272125952),
            Tip("uaq", "tip 5 to del in g1", user_id=490970360272125952)
        ]

        self.save_storage()

    async def valid_location(self, location, response_method):
        if location[0] == "g":
            try:
                feat_num = int(location[1])
                # noinspection PyStatementEffect
                self.tip_storage["globals"][feat_num]
            except IndexError:  # called if location[1] dne
                await response_method.send("Character following `g` for global feat must be a number indicating which"
                                           " global feat to query.")
                return False
            except ValueError:  # called if location[1] not an int
                await response_method.send("The character following `g` must be a number.")
                return False
            except KeyError:  # called if feat_num not in [1,8]
                await response_method.send("The number following `g` must be between 1 and 8 (inclusive).")
                return False

        elif location[0] == "s":
            try:
                sector_num = int(location[1])
                # noinspection PyStatementEffect
                self.tip_storage["sectors"][sector_num]
            except IndexError:  # called if location[1] dne
                await response_method.send("The character following `s` for sectors must be a number indicating which "
                                           "sector to query.")
                return False
            except ValueError:  # called if location[1] not an int
                await response_method.send("The character following `s` must be a number.")
                return False
            except KeyError:  # called if sector_num not in [1,5]
                await response_method.send("The number following `s` must be between 1 and 5 (inclusive).")
                return False

            try:
                tip_type = location[2]
            except IndexError:
                await response_method.send(f"The character following `{sector_num}` must be `b` for boss tips, `m` for "
                                           "miniboss tips, `n` for node tips, or `f` for sector feats.")
                return False

            if tip_type not in self.tip_types.keys():
                await response_method.send(f"The character following `{sector_num}` must be `b` for boss tips, `m` for "
                                           "miniboss tips, `n` for node tips, or `f` for sector feats.")
                return False

            if tip_type == "b" or tip_type == "m":
                tip_type = "boss" if tip_type == "b" else "mini"
                try:
                    feat_num = int(location[3])
                    # noinspection PyStatementEffect
                    self.tip_storage["sectors"][sector_num][tip_type]["feats"][feat_num]
                except IndexError:  # location[3] dne, do standard tips
                    return True
                except ValueError:  # called if location[3] not an int
                    await response_method.send(f"The character following `{tip_type[0]}` must be a number indicating "
                                               f"which feat to query.")
                    return False
                except KeyError:  # called if feat_num not 1 or 2
                    await response_method.send(f"The number following `{tip_type[0]}` must be either a 1 or 2, "
                                               f"indicating the first or second feat")
                    return False

            elif tip_type == "n":
                try:
                    node_num = int(location[3:])
                    # noinspection PyStatementEffect
                    self.tip_storage["sectors"][sector_num]["nodes"][node_num]
                except IndexError:  # called if location[3:] dne
                    await response_method.send("The character following `n` for nodes must be a number indicating which"
                                               " node to query.")
                    return False
                except ValueError:  # called if location[3:] not a number
                    await response_method.send("The characters following `n` must ba a number.")
                    return False
                except KeyError:  # called if the key does not yet exist, make it an empty list
                    # noinspection PyUnboundLocalVariable
                    self.tip_storage["sectors"][sector_num]["nodes"][node_num] = []

            else:  # tip_type == "f"
                try:
                    feat_num = int(location[3])
                    # noinspection PyStatementEffect
                    self.tip_storage["sectors"][sector_num]["feats"][feat_num]
                except IndexError:  # called if location[3] dne
                    await response_method.send("The character following `f` for sector feats must be a number "
                                               "indicating which feat to query.")
                    return False
                except ValueError:  # called if location[3] not a number
                    await response_method.send("The character following `f` must be a number.")
                    return False
                except KeyError:  # called if feat_num not in [1,4]
                    await response_method.send("The number following `f` must be between 1 and 4 (inclusive).")
                    return False
        else:
            await response_method.send("Invalid or missing location. Queries to tips must start with an `s` to "
                                       "identify a sector or `g` to identify global feats.")
            return False

        return True

    def get_tips(self, location):
        if location[0] == "g":
            tip_list = self.tip_storage["globals"][int(location[1])]

        else:  # location[0] == "s"
            tip_type = self.tip_types[location[2]]
            sector = self.tip_storage["sectors"][int(location[1])][tip_type]
            if tip_type == "boss" or tip_type == "mini":
                feat_num = location[3:]
                if feat_num == "":  # standard tips
                    tip_list = sector["tips"]
                else:  # feat tips
                    tip_list = sector["feats"][int(feat_num)]

            else:  # tip_type == "feats" or "nodes"
                tip_list = sector[int(location[3:])]

        return tip_list

    @commands.command(name="conquest", aliases=["c", "con", "conq"], extras={'is_holocron': True},
                      description="Access the Conquest Holocron for reading and managing Conquest Tips")
    async def conquest_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)

    # ALTERNATIVE TO ABOVE
    # holocron_command_manager = (
    #     commands.command(name="conquest", aliases=["c", "con", "conq"],
    #                      extras={'is_holocron': True},
    #                      description="Access the Conquest Holocron for reading and managing "
    #                                  "Conquest Tips")
    #     (Holocron.holocron_command_manager))


async def setup(bot):
    await bot.add_cog(ConquestHolocron(bot))
