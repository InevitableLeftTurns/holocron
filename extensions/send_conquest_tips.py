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
            try:
                global_feat_num = int(tip_location[1])
                tip_list = self.tip_storage["globals"][global_feat_num]

            except IndexError:  # called if tip_location[1] dne
                await response_method.send("Character following `g` for global feat must be a number indicating which"
                                           " global feat to query.")
                return

            except ValueError:  # called if tip_location[1] not int
                await response_method.send("The character following `g` must be a number.")
                return

            except KeyError:  # called if feat_num not in [1,8]
                await response_method.send("The number following `g` must be between 1 and 8 (inclusive).")
                return

            tip_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
            top_three = tip_list[:3]

            if len(top_three) > 0:
                await response_method.send(f"__**Top {len(top_three)} tip{'s' if len(top_three) > 1 else ''} (of "
                                           f"{len(tip_list)}) for Global Feat {global_feat_num}**__\n"
                                           f"{top_three[0].create_tip_message()}")
                for tip in top_three[1:]:
                    await response_method.send(tip.create_tip_message())
                return

            await response_method.send(f"There are currently no tips for Global Feat {global_feat_num}. If you wish "
                                       f"to write one, [NYI]")

        elif tip_location[0] == 's':
            tip_location = tip_location[1:]  # remove s, as we no longer care
            try:
                sector_num = int(tip_location[0])  # in theory one of: [1, 2, 3, 4, 5]
                # noinspection PyStatementEffect
                self.tip_storage["sectors"][sector_num]  # checks if the key exists, above comment prevents editor noise

            except IndexError:  # called if no character in tip_location
                await response_method.send("Sector number expected. To query a sector, choose a sector number between 1"
                                           " and 5.")
                return

            except ValueError:  # called if non-number character in tip_location[0]
                await response_method.send("Requested sector must be a number 1 through 5 (inclusive).")
                return

            except KeyError:  # called if number not in [1,5]
                await response_method.send("The sector must be 1 through 5 (inclusive).")
                return

            type_functions = {
                "b": self.boss_tips,
                "m": self.mini_tips,
                "n": self.node_tips,
                "f": self.feat_tips
            }
            tip_location = tip_location[1:]  # remove number, as we no longer care
            try:
                tip_type = tip_location[0]  # in theory, one of [b, m, n, f]
                await type_functions[tip_type](response_method, sector_num, tip_location[1:])

            except IndexError:  # called if no character in tip_location[0]
                await response_method.send("Tip type expected. Use `b` for bosses, `m` for minibosses, `n` for generic "
                                           "nodes, and `f` for sector feats.")
                return

            except KeyError:  # called if tip_type is not [b,m,n,f]
                # noinspection PyUnboundLocalVariable
                await response_method.send(f"Tip type `{tip_type}` does not exist. Use `b` for bosses, `m` for "
                                           f"minibosses, `n` for generic nodes, and `f` for sector feats.")
                return

        else:
            await response_method.send("Queries to tips must start with an `s` to identify a sector or `g` to identify "
                                       "global feats")

    async def boss_tips(self, response_method, sector_num, extra_pos, boss_type="boss"):
        if extra_pos == "":
            feat_num = None

            tips_list = self.tip_storage["sectors"][sector_num][boss_type]["tips"]
            tips_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
            top_three = tips_list[:3]

        else:
            try:
                feat_num = int(extra_pos[0])
                tips_list = self.tip_storage["sectors"][sector_num][boss_type]["feats"][feat_num]

            except IndexError:  # should never be called because of prior if-statement, but placed just in case
                await response_method.send("Illegal state. Send for help.")
                return

            except ValueError:  # called if non-number character at feat_num pos
                await response_method.send(f"Characters following `boss` or `miniboss` must be either a number for "
                                           f"tips on feats, or blank for tips on clearing the stage.")
                return

            except KeyError:  # called if feat_num not [1,2]
                tip_request_base = f"s{sector_num}{boss_type[0]}"
                await response_method.send(f"The feat number you requested does not exist. Try `{tip_request_base}1` "
                                           f"or `{tip_request_base}2` for {boss_type} feat tips, or `g[number 1-8]` "
                                           f"for global feats")
                return

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
            return
        await response_method.send(f"There are currently no tips for Sector {sector_num} {boss_name}{feats_included}. "
                                   f"If you wish to write one, [NYI]")

    async def mini_tips(self, response_method, sector_num, extra_pos):
        await self.boss_tips(response_method, sector_num, extra_pos, "mini")

    async def node_tips(self, response_method, sector_num, node_num):
        if node_num == "":
            node_request_base = f"s{sector_num}n"
            await response_method.send(f"Node number expected. Try `{node_request_base}[number]`, where `[number]` is "
                                       f"the number of the node.")
            return

        no_tips_message = f"There are currently no tips for Sector {sector_num} Node {node_num}. If you wish to " \
                          f"write one, [NYI]"
        try:
            node_num = int(node_num)
            tips_list = self.tip_storage["sectors"][sector_num]["nodes"][node_num]

        except IndexError:  # should never be called because of prior if-statement, but placed just in case
            await response_method.send("Illegal state. Send for help.")
            return

        except ValueError:  # called if node_num is not a number
            await response_method.send("Character following `node` should be a number indicating which node to query.")
            return

        except KeyError:  # called if no tips for requested node
            await response_method.send(no_tips_message)
            return

        tips_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
        top_three = tips_list[:3]

        if len(top_three) > 0:
            # attaches first tip here to send fewer messages
            await response_method.send(f"__**Top {len(top_three)} tip{'s' if len(top_three) > 1 else ''} "
                                       f"(of {len(tips_list)}) for Sector {sector_num} Node {node_num}**__\n"
                                       f"{top_three[0].create_tip_message()}")
            for tip in top_three[1:]:
                await response_method.send(tip.create_tip_message())
            return

        # called only when all tips for a sector are removed
        await response_method.send(no_tips_message)

    async def feat_tips(self, response_method, sector_num, feat_num):
        if feat_num == "":
            feat_request_base = f"s{sector_num}f"
            await response_method.send(f"Feat number expected. Try `{feat_request_base}[number]`, where `[number]` is "
                                       f"the number of the feat.")
            return

        try:
            feat_num = int(feat_num[0])
            tips_list = self.tip_storage["sectors"][sector_num]["feats"][feat_num]

        except IndexError:  # should never be called because of prior if-statement, but placed just in case
            await response_method.send("Illegal state. Send for help.")
            return

        except ValueError:  # called if feat_num is not a number
            await response_method.send("Character following `feat` must be a number, indicating which feat to query.")
            return

        except KeyError:  # called if feat_num not [1,4]
            await response_method.send("Provided feat number too small or large. Try a number between 1 and 4 "
                                       "(inclusive)")
            return

        tips_list.sort(reverse=True, key=lambda each_tip: each_tip.rating)
        top_three = tips_list[:3]

        if len(top_three) > 0:
            await response_method.send(f"__**Top {len(top_three)} tip{'s' if len(top_three) > 1 else ''} (of "
                                       f"{len(tips_list)}) for Sector {sector_num} Feat {feat_num}**__\n"
                                       f"{top_three[0].create_tip_message()}")
            for tip in top_three[1:]:
                await response_method.send(tip.create_tip_message())
            return

        await response_method.send(f"There are currently no tips for Sector {sector_num} Feat {feat_num}. If you wish "
                                   f"to write one, [NYI]")

    async def add_tip(self):  # take same params as edit_tip
        pass  # part of one command

    async def edit_tip(self, response_method, location, author, guild, mod_type):
        if location[0] == "g":
            try:
                global_num = int(location[1])
                all_tips = self.tip_storage["globals"][global_num].copy()

            except IndexError:  # called if location[1] does not exist
                await response_method.send(f"To {mod_type} a Global Feat tip, you must specify which Global Feat to "
                                           f"{mod_type} a tip from.")
                return

            except ValueError:  # called if location[1] is not a number
                await response_method.send(f"To specify which Global Feat you wish to {mod_type} a tip from, use a "
                                           f"number corresponding to which feat you wish to {mod_type} from.")
                return

            except KeyError:  # called if global_num not in [1,8]
                # noinspection PyUnboundLocalVariable
                await response_method.send(f"The global feat number {global_num} does not exist. Please specify a "
                                           f"number between 1 and 8 (inclusive).")
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
                await response_method.send(f"There are no tips that you can {mod_type} in Global Feat {global_num}.")

        elif location[0] == "s":
            pass
        else:
            await response_method.send("Tips locations must start with an `s` to identify a sector, or `g` to identify "
                                       "global feats.")

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
        pass

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
                index = self.tip_storage["globals"][int(location[1])].index(tip)  # index of tip obj
                self.tip_storage["globals"][int(location[1])].pop(index)
                pass
            else:  # location[0] == "s"
                pass
            feedback = "Tip deleted."
        else:
            feedback = "Deletion canceled. Tip not deleted."

        await response_method.send(feedback)


async def setup(bot):
    await bot.add_cog(SendConquestTips(bot))
