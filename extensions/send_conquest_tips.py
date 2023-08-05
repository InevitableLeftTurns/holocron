from data.Tip import Tip
from discord.ext import commands
from functools import partial
from util import helpmgr
from util.Holocron import Holocron
from util.settings.response_handler import get_response_type
from util.settings.tip_sorting_handler import sort_tips


class SendConquestTips(commands.Cog, Holocron):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, "conquest")

    tip_types = {
        "b": "boss",
        "m": "mini",
        "n": "nodes",
        "f": "feats"
    }

    # Super Implementations
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

    # Command Managing
    @commands.command(name="conquest", aliases=["c", "con", "conq"], extras={'is_holocron': True},
                      description="Access the Conquest Holocron for reading and managing Conquest Tips")
    async def conquest_manager(self, ctx: commands.Context, *args):
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)
        if len(args) == 0:
            await response_method.send(f"Conquest commands require extra information. For a list of commands and "
                                       f"options, use `{ctx.prefix}conquest help`.")
            return

        user_command = args[0]

        clear_names = [
            "clean",
            "reset",
            "clear"
        ]
        dummy_names = [
            "dummy",
            "populate",
            "test"
        ]
        if user_command in clear_names:
            await self.request_clean_storage(ctx.guild, ctx.channel, ctx.author, response_method)
            return

        elif user_command in dummy_names:
            await self.request_dummy_populate(ctx.guild, ctx.author, response_method)
            return

        elif user_command == 'help':
            commands_args = args[1:]
            response = helpmgr.generate_bot_help(self.bot.get_command('conquest'), ctx, *commands_args)
            await response_method.send('\n'.join(response))
            return

        else:
            if await self.valid_location(user_command, response_method):
                try:
                    to_edit = args[1]
                except IndexError:
                    to_edit = ""
                await self.conquest_tips(ctx.guild, ctx.channel, ctx.author, user_command, to_edit)
                return

    async def conquest_tips(self, guild, channel, author, tip_location: str, to_edit="no"):
        response_method = get_response_type(guild, author, channel)
        tip_location = tip_location.lower()

        if not await self.valid_location(tip_location, response_method):
            return

        modifying = {
            "add": partial(self.add_tip, channel),
            "edit": partial(self.edit_tip, to_edit, guild),
            "delete": partial(self.edit_tip, to_edit, guild)
        }
        try:
            await modifying[to_edit](author, tip_location, response_method)
            return
        except KeyError:
            pass

        if tip_location[0] == 'g':
            global_feat_num = int(tip_location[1])

            tip_list = self.tip_storage["globals"][global_feat_num]
            sort_tips(tip_list)
            top_three = tip_list[:3]
            total = len(tip_list)

        else:  # tip_location[0] == 's'
            sector_num = int(tip_location[1])  # in theory one of: [1, 2, 3, 4, 5]

            type_functions = {
                "b": self.boss_tips,
                "m": self.mini_tips,
                "n": self.node_tips,
                "f": self.feat_tips
            }

            tip_type = tip_location[2]  # one of [b, m, n, f]
            top_three, total = await type_functions[tip_type](sector_num, tip_location[3:])

        if len(top_three) > 0:
            response = [f"__**Recent {len(top_three)} tip{'' if len(top_three) == 1 else 's'} "
                        f"(of {total}) for {tip_location}**__"]
            for index, tip in enumerate(top_three):
                response.append(f"{index + 1} - " + tip.create_tip_message())
            await response_method.send('\n'.join(response))
        else:
            await response_method.send(f"There are no tips in {tip_location}.")

    async def boss_tips(self, sector_num, extra_pos, boss_type="boss"):
        if extra_pos == "":
            tips_list = self.tip_storage["sectors"][sector_num][boss_type]["tips"]
            sort_tips(tips_list)
            top_three = tips_list[:3]

        else:
            feat_num = int(extra_pos[0])

            tips_list = self.tip_storage["sectors"][sector_num][boss_type]["feats"][feat_num]
            sort_tips(tips_list)
            top_three = tips_list[:3]

        return top_three, len(tips_list)

    async def mini_tips(self, sector_num, extra_pos):
        return await self.boss_tips(sector_num, extra_pos, "mini")

    async def node_tips(self, sector_num, node_num):
        node_num = int(node_num)

        tips_list = self.tip_storage["sectors"][sector_num]["nodes"][node_num]
        sort_tips(tips_list)
        top_three = tips_list[:3]

        return top_three, len(tips_list)

    async def feat_tips(self, sector_num, feat_num):
        feat_num = int(feat_num[0])

        tips_list = self.tip_storage["sectors"][sector_num]["feats"][feat_num]
        sort_tips(tips_list)
        top_three = tips_list[:3]

        return top_three, len(tips_list)


async def setup(bot):
    await bot.add_cog(SendConquestTips(bot))
