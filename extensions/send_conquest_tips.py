import discord
from collections import namedtuple
from data.Tip import Tip
from discord.ext import commands
from util.response_handler import get_response_type
from util.command_checks import check_higher_perms


AwaitingReaction = namedtuple("AwaitingReaction", ["user_id", "allowed_emoji", "tips", "mod_type", "location"])


class SendConquestTips(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tip_storage = {
            # "sectors": {
            #     1: {
            #         "boss": {
            #             "feats": {
            #               1: [],
            #               2: []
            #             },
            #             "tips": []
            #         },
            #         "mini": {}, # same as boss
            #         "nodes": {},
            #         "feats": {
            #             1: ""  # through 4
            #         }
            #     },
            #     2: {},
            #     3: {},
            #     4: {},
            #     5: {}
            # }
            # "globals": {
            #     1: [],
            #     2: []  # through 8
            # }
        }
        self.create_tip_storage()
        self.dummy_populate()
        self.awaiting_reactions = {}

    def create_tip_storage(self):
        self.tip_storage["sectors"] = {}
        for i in range(5):
            self.tip_storage["sectors"][i+1] = {}
            self.tip_storage["sectors"][i+1]["boss"] = {"feats": {1: [], 2: []}, "tips": []}
            self.tip_storage["sectors"][i+1]["mini"] = {"feats": {1: [], 2: []}, "tips": []}
            self.tip_storage["sectors"][i+1]["nodes"] = {}
            self.tip_storage["sectors"][i+1]["feats"] = {}
            for j in range(4):
                self.tip_storage["sectors"][i+1]["feats"][j+1] = []

        self.tip_storage["globals"] = {}
        for i in range(8):
            self.tip_storage["globals"][i+1] = []

    def dummy_populate(self):
        self.tip_storage["globals"][1].append(Tip("trich", "this is a tip for g1"))
        self.tip_storage["globals"][1].append(Tip("trich", "this is another tip for g1"))

        self.tip_storage["sectors"][1]["feats"][1] = [
            Tip("uaq", "tip for s1f1", 0),
            Tip("uaq", "tip for s1f1", 7),
            Tip("uaq", "tip for s1f1", 2),
            Tip("uaq", "tip for s1f1", 4)
        ]

        self.tip_storage["sectors"][1]["nodes"][1] = [Tip("uaq", "tip for s1n1")]
        self.tip_storage["sectors"][1]["nodes"][12] = [
            Tip("uaq", "tip for s1n12", 0),
            Tip("uaq", "tip for s1n12", 7),
            Tip("uaq", "tip for s1n12", 2),
            Tip("uaq", "tip for s1n12", 4)
        ]

        self.tip_storage["sectors"][1]["boss"]["feats"][1] = [
            Tip("uaq", "tip for s1b1", 0),
            Tip("uaq", "tip for s1b1", 7),
            Tip("uaq", "tip for s1b1", 2),
            Tip("uaq", "tip for s1b1", 4),
        ]
        self.tip_storage["sectors"][1]["boss"]["tips"].append(Tip("uaq", "tip for s1b"))

        self.tip_storage["sectors"][1]["mini"]["feats"][1].append(Tip("uaq", "tip for s1m1"))
        self.tip_storage["sectors"][1]["mini"]["tips"].append(Tip("uaq", "tip for s1m"))

        self.tip_storage["globals"][1].append(Tip("uaq", "tip 1 to del in g1", user_id=490970360272125952))
        self.tip_storage["globals"][1].append(Tip("uaq", "tip 2 to del in g1", user_id=490970360272125952))
        self.tip_storage["globals"][1].append(Tip("uaq", "tip 3 to del in g1", user_id=490970360272125952))
        self.tip_storage["globals"][1].append(Tip("uaq", "tip 4 to del in g1", user_id=490970360272125952))
        self.tip_storage["globals"][1].append(Tip("uaq", "tip 5 to del in g1", user_id=490970360272125952))

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

            tip_types = [
                "b",
                "m",
                "n",
                "f"
            ]
            try:
                tip_type = location[2]
            except IndexError:
                await response_method.send(f"The character following `{sector_num}` must be `b` for boss tips, `m` for "
                                           "miniboss tips, `n` for node tips, or `f` for sector feats.")
                return False

            if tip_type not in tip_types:
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
            await response_method.send("Queries to tips must start with an `s` to identify a sector or `g` to identify "
                                       "global feats.")
            return False

        return True

    """
    tip_location- 
    syntax: sector,sector number,node/mini/boss/feat,number (op)
    examples: s1m, s3b, s3n13, s2f4
    -or-
    syntax: global,number
    examples: g1, g4, g8
    """
    @commands.command(name="conquest", aliases=["c", "con", "conq"],
                      description="Sends tips and tricks for the active conquest")
    async def conquest_tips(self, ctx: commands.Context, tip_location: str, to_edit="no"):
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)
        tip_location = tip_location.lower()

        if not await self.valid_location(tip_location, response_method):
            return

        modifying = {
            "add": self.add_tip,
            "edit": self.edit_tip,
            "delete": self.edit_tip
        }
        try:
            await modifying[to_edit](response_method, tip_location, ctx.author, ctx.guild, to_edit)
            return
        except KeyError:
            pass

        if tip_location[0] == 'g':
            global_feat_num = int(tip_location[1])

            tip_list = self.tip_storage["globals"][global_feat_num]
            tip_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
            top_three = tip_list[:3]

            if len(top_three) > 0:
                await response_method.send(f"__**Top {len(top_three)} tip{'s' if len(top_three) > 1 else ''} (of "
                                           f"{len(tip_list)}) for Global Feat {global_feat_num}**__\n"
                                           f"{top_three[0].create_tip_message()}")
                for tip in top_three[1:]:
                    await response_method.send(tip.create_tip_message())

            else:
                await response_method.send(f"There are currently no tips for Global Feat {global_feat_num}.")

        else:  # tip_location[0] == 's'
            sector_num = int(tip_location[1])  # in theory one of: [1, 2, 3, 4, 5]

            type_functions = {
                "b": self.boss_tips,
                "m": self.mini_tips,
                "n": self.node_tips,
                "f": self.feat_tips
            }

            tip_type = tip_location[2]  # one of [b, m, n, f]
            await type_functions[tip_type](response_method, sector_num, tip_location[3:])

    async def boss_tips(self, response_method, sector_num, extra_pos, boss_type="boss"):
        if extra_pos == "":
            feat_num = None

            tips_list = self.tip_storage["sectors"][sector_num][boss_type]["tips"]
            tips_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
            top_three = tips_list[:3]

        else:
            feat_num = int(extra_pos[0])

            tips_list = self.tip_storage["sectors"][sector_num][boss_type]["feats"][feat_num]
            tips_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
            top_three = tips_list[:3]

        boss_name = boss_type.capitalize()
        boss_name += "boss" if boss_name == "mini" else ""
        feats_included = f" Feat {feat_num}" if feat_num is not None else ""

        if len(top_three) > 0:
            # attaches first place here to send fewer messages
            await response_method.send(f"__**Top {len(top_three)} tip{'s' if len(top_three) > 1 else ''} (of "
                                       f"{len(tips_list)}) for Sector {sector_num} {boss_name}{feats_included}**__\n"
                                       f"{top_three[0].create_tip_message()}")
            for tip in top_three[1:]:
                await response_method.send(tip.create_tip_message())

        else:
            await response_method.send(f"There are currently no tips for Sector {sector_num} "
                                       f"{boss_name}{feats_included}.")

    async def mini_tips(self, response_method, sector_num, extra_pos):
        await self.boss_tips(response_method, sector_num, extra_pos, "mini")

    async def node_tips(self, response_method, sector_num, node_num):
        node_num = int(node_num)

        tips_list = self.tip_storage["sectors"][sector_num]["nodes"][node_num]
        tips_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
        top_three = tips_list[:3]

        if len(top_three) > 0:
            # attaches first tip here to send fewer messages
            await response_method.send(f"__**Top {len(top_three)} tip{'s' if len(top_three) > 1 else ''} "
                                       f"(of {len(tips_list)}) for Sector {sector_num} Node {node_num}**__\n"
                                       f"{top_three[0].create_tip_message()}")
            for tip in top_three[1:]:
                await response_method.send(tip.create_tip_message())

        else:
            await response_method.send(f"There are currently no tips for Sector {sector_num} Node {node_num}.")

    async def feat_tips(self, response_method, sector_num, feat_num):
        feat_num = int(feat_num[0])

        tips_list = self.tip_storage["sectors"][sector_num]["feats"][feat_num]
        tips_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
        top_three = tips_list[:3]

        if len(top_three) > 0:
            await response_method.send(f"__**Top {len(top_three)} tip{'s' if len(top_three) > 1 else ''} (of "
                                       f"{len(tips_list)}) for Sector {sector_num} Feat {feat_num}**__\n"
                                       f"{top_three[0].create_tip_message()}")
            for tip in top_three[1:]:
                await response_method.send(tip.create_tip_message())

        else:
            await response_method.send(f"There are currently no tips for Sector {sector_num} Feat {feat_num}.")

    async def add_tip(self, response_method, location, author, guild, mod_type):
        await response_method.send("NYI")

    async def edit_tip(self, response_method, location, author, guild, mod_type):
        if location[0] == "g":
            global_num = int(location[1])
            all_tips = self.tip_storage["globals"][global_num].copy()

            rep_string = f"Global Feat {global_num}"

        elif location[0] == "s":
            sector_num = int(location[1])
            tip_types = {
                "b": "boss",
                "m": "mini",
                "n": "nodes",
                "f": "feats"
            }
            tip_type = tip_types[location[2]]
            if tip_type == "boss" or tip_type == "mini":
                feat_num = location[3:]
                if feat_num == "":  # standard tips
                    all_tips = self.tip_storage["sectors"][sector_num][tip_type]["tips"]
                    rep_string = f"Sector {sector_num} {'Boss' if tip_type == 'boss' else 'Miniboss'}"
                else:  # feat tips
                    all_tips = self.tip_storage["sectors"][sector_num][tip_type]["feats"][int(feat_num)]
                    rep_string = f"Sector {sector_num} {'Boss' if tip_type == 'boss' else 'Miniboss'} Feat {feat_num}"
            elif tip_type == "nodes":
                all_tips = self.tip_storage["sectors"][sector_num]["nodes"][int(location[3:])]
                rep_string = f"Sector {sector_num} Node {location[3:]}"
            else:  # tip_type == "feats"
                all_tips = self.tip_storage["sectors"][sector_num]["feats"][int(location[3])]
                rep_string = f"Sector {sector_num} Feat {location[3]}"
        else:
            await response_method.send("Tips locations must start with an `s` to identify a sector, or `g` to identify "
                                       "global feats.")
            return

        if await check_higher_perms(author, guild):
            user_tips = all_tips
        else:
            user_tips = list(filter(lambda each_tip: each_tip.user_id == author.id, all_tips))

        if len(user_tips) > 0:
            user_tips.sort(reverse=True, key=lambda each_tip: each_tip.creation_time.time())
            user_tips = user_tips[:5]

            tip_messages = [f"Which tip would you like to {mod_type}?"]
            for index, tip in enumerate(user_tips):
                tip_messages.append(f"{index+1} - {tip.create_selection_message()}")

            sent_tip_message = await response_method.send("\n".join(tip_messages))
            emoji_list = []
            for index in range(len(user_tips)):
                emoji = str(index+1) + "\u20E3"

                await sent_tip_message.add_reaction(emoji)
                emoji_list.append(emoji)

            await sent_tip_message.add_reaction("\u27A1")  # right arrow
            emoji_list.append("\u27A1")

            self.awaiting_reactions[sent_tip_message.id] = AwaitingReaction(author.id, emoji_list,
                                                                            user_tips, mod_type, location)

        else:
            await response_method.send(f"There are no tips that you can {mod_type} in {rep_string}.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if user.id == self.bot.user.id:
            return
        try:
            awaiting_reaction = self.awaiting_reactions[reaction.message.id]
        except KeyError:
            return
        if awaiting_reaction.user_id == user.id and reaction.emoji in awaiting_reaction.allowed_emoji:
            await self.handle_reaction_add(reaction, user)

    async def handle_reaction_add(self, reaction, user):
        response_method = get_response_type(reaction.message.guild, user, reaction.message.channel)

        awaiting_reaction = self.awaiting_reactions[reaction.message.id]
        del self.awaiting_reactions[reaction.message.id]

        tips = awaiting_reaction.tips
        mod_type = awaiting_reaction.mod_type

        try:
            emoji_num = int(reaction.emoji[0])
        except ValueError:
            return  # page change, make a func or smth

        chosen_tip = tips[emoji_num - 1]
        if mod_type == "edit":
            await self.handle_tip_edit(response_method, chosen_tip)
        else:  # mod_type == delete:
            await self.handle_tip_delete(response_method, chosen_tip, reaction, user, awaiting_reaction.location)

    async def handle_tip_edit(self, response_method, tip):
        await response_method.send("NYI")

    async def handle_tip_delete(self, response_method, tip, reaction, user, location):
        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        user_id = user.id
        channel_id = reaction.message.channel.id
        await response_method.send(f"Are you sure you want to delete the tip:\n`{tip.create_delete_message()}`?\n\n"
                                   f"Please type `confirm` to confirm and permanently delete this tip, or `cancel` to "
                                   f"cancel.")
        confirm_message = await self.bot.wait_for("message", check=check_message)
        if confirm_message.content == "confirm":
            if location[0] == "g":
                self.tip_storage["globals"][int(location[1])].remove(tip)
            else:  # location[0] == "s"
                self.delete_sector_tip(location, tip)
            feedback = "Tip deleted."
        else:
            feedback = "Deletion canceled. Tip not deleted."

        await response_method.send(feedback)

    def delete_sector_tip(self, location, tip):
        tip_types = {
            "b": "boss",
            "m": "mini",
            "n": "nodes",
            "f": "feats"
        }
        sector_num = int(location[1])
        tip_type = tip_types[location[2]]
        if tip_type == "boss" or tip_type == "mini":
            try:
                boss_feat_num = int(location[3])
                self.tip_storage["sectors"][sector_num][tip_type]["feats"][boss_feat_num].remove(tip)
            except IndexError:  # called if no loc[3]; signifies boss tip
                self.tip_storage["sectors"][sector_num][tip_type]["tips"].remove(tip)

        elif tip_type == "nodes":
            node_num = int(location[3:])
            self.tip_storage["sectors"][sector_num][tip_type][node_num].remove(tip)

        else:  # tip_type == "feats
            feat_num = int(location[3])
            self.tip_storage["sectors"][sector_num][tip_type][feat_num].remove(tip)


async def setup(bot):
    await bot.add_cog(SendConquestTips(bot))
