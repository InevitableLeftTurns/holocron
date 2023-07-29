import discord

from data.AwaitingReaction import AwaitingReaction
from data.Tip import Tip
from discord.ext import commands
from functools import partial
from util.command_checks import check_higher_perms
from util.settings.response_handler import get_response_type
from util.tip_storage_manager import load_tip_storage


class SendConquestTips(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tip_storage = load_tip_storage()
        self.awaiting_reactions = {}

    tip_types = {
        "b": "boss",
        "m": "mini",
        "n": "nodes",
        "f": "feats"
    }

    def save_storage(self):
        from util.tip_storage_manager import save_storage_to_file
        save_storage_to_file(self.tip_storage)

    @commands.command(name="conquest", aliases=["c", "con", "conq"], description="Command for managing and branching to"
                                                                                 " all conquest commands")
    async def conquest_manager(self, ctx: commands.Context, *args):
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)
        if len(args) == 0:
            await response_method.send(f"This command requires extra information to have functionality. For a list of "
                                       f"options, use `{ctx.prefix}help conquest`.")
            return

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
        if args[0] in clear_names:
            await self.clean_storage(ctx.guild, ctx.channel, ctx.author, response_method)
            return

        elif args[0] in dummy_names:
            await self.dummy_populate(ctx.guild, ctx.author, response_method)
            return

        else:
            if await self.valid_location(args[0], response_method):
                try:
                    to_edit = args[1]
                except IndexError:
                    to_edit = ""
                await self.conquest_tips(ctx.guild, ctx.channel, ctx.author, args[0], to_edit)
                return

    async def clean_storage(self, guild, channel, author, response_method):
        def check_message(message):
            return message.channel.id == channel.id and message.author.id == author.id

        if not await check_higher_perms(author, guild):
            await response_method.send("You do not have access to this command.")
            return

        await response_method.send("Are you sure you want to clear all tips from storage? Type `confirm` to confirm, or"
                                   "`cancel` to cancel.")
        confirm_message = await self.bot.wait_for("message", check=check_message)
        if confirm_message.content != "confirm":
            feedback = "Storage clearing canceled. All tips will remain."
        else:
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

            self.save_storage()
            feedback = "Tip storage has been cleared."

        self.save_storage()
        await response_method.send(feedback)

    async def dummy_populate(self, guild, author, response_method):
        if not await check_higher_perms(author, guild):
            await response_method.send("You do not have permission to use this command")
            return

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
            Tip("uaq", "tip for s1n12", 0),
            Tip("uaq", "tip for s1n12", 7),
            Tip("uaq", "tip for s1n12", -3)
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

        self.save_storage()
        await response_method.send("Data added.")

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
            await response_method.send("Queries to tips must start with an `s` to identify a sector or `g` to identify "
                                       "global feats.")
            return False

        return True

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
            tip_list.sort(reverse=True, key=lambda each_tip: each_tip.creation_time)
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
            tips_list.sort(reverse=True, key=lambda each_tip: each_tip.creation_time)
            top_three = tips_list[:3]

        else:
            feat_num = int(extra_pos[0])

            tips_list = self.tip_storage["sectors"][sector_num][boss_type]["feats"][feat_num]
            tips_list.sort(reverse=True, key=lambda each_tip: each_tip.creation_time)
            top_three = tips_list[:3]

        return top_three, len(tips_list)

    async def mini_tips(self, sector_num, extra_pos):
        return await self.boss_tips(sector_num, extra_pos, "mini")

    async def node_tips(self, sector_num, node_num):
        node_num = int(node_num)

        tips_list = self.tip_storage["sectors"][sector_num]["nodes"][node_num]
        tips_list.sort(reverse=True, key=lambda each_tip: each_tip.creation_time)
        top_three = tips_list[:3]

        return top_three, len(tips_list)

    async def feat_tips(self, sector_num, feat_num):
        feat_num = int(feat_num[0])

        tips_list = self.tip_storage["sectors"][sector_num]["feats"][feat_num]
        tips_list.sort(reverse=True, key=lambda each_tip: each_tip.creation_time)
        top_three = tips_list[:3]

        return top_three, len(tips_list)

    async def add_tip(self, channel, author, location, response_method):
        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        await response_method.send(f"Your next message in this channel will be added as a tip in {location}. If you "
                                   f"wish to cancel, respond with `cancel`.")
        channel_id = channel.id
        user_id = author.id
        tip_message = await self.bot.wait_for("message", check=check_message)

        if tip_message.content.lower() == "cancel":
            await response_method.send("Tip addition has been cancelled.")
            return

        self.write_tip(location, tip_message)

        await response_method.send(f"Your tip has been added to {location}")

    def write_tip(self, location, tip_message: discord.Message):
        if location[0] == "g":
            global_num = int(location[1])
            self.tip_storage["globals"][global_num].append(Tip(tip_message))

        else:  # location[0] == "s"
            sector = self.tip_storage["sectors"][int(location[1])][self.tip_types[location[2]]]
            if location[2] == "b" or location[2] == "m":
                if location[3:] == "":  # no number, normal tip
                    sector["tips"].append(Tip(tip_message))
                else:  # number, feat tip
                    sector["feats"][int(location[3])].append(Tip(tip_message))
            elif location[2] == "n":
                sector[int(location[3:])].append(Tip(tip_message))
            else:  # location[2] == "f"
                sector[int(location[3])].append(Tip(tip_message))

        self.save_storage()

    async def edit_tip(self, mod_type, guild, author, location, response_method):
        tips_list = self.get_tips(location)

        if await check_higher_perms(author, guild):
            user_tips = tips_list
        else:
            user_tips = list(filter(lambda each_tip: each_tip.user_id == author.id, tips_list))

        if len(user_tips) > 0:
            user_tips.sort(reverse=True, key=lambda each_tip: each_tip.creation_time.time())
            page_count = ((len(user_tips) - 1) // 5) + 1
            user_tips = user_tips[:5]

            tip_messages = [f"Which tip would you like to {mod_type}?"]
            for index, tip in enumerate(user_tips):
                tip_messages.append(f"{index+1} - {tip.create_selection_message()}")

            emoji_list = []
            for index in range(len(user_tips)):
                emoji = str(index+1) + "\u20E3"
                emoji_list.append(emoji)

            if page_count > 1:
                tip_messages.append(f"Page 1/{page_count}")
                emoji_list.append("➡️")

            sent_tip_message = await response_method.send("\n".join(tip_messages))

            self.awaiting_reactions[sent_tip_message.id] = AwaitingReaction(author.id, emoji_list,
                                                                            user_tips, mod_type, location)

            for emoji in emoji_list:
                await sent_tip_message.add_reaction(emoji)

        else:
            await response_method.send(f"There are no tips that you can {mod_type} in {location}.")

    def get_tips(self, location):
        if location[0] == "g":
            tip_list = self.tip_storage["globals"][int(location[1])].copy()

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

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if user.id == self.bot.user.id:
            return
        try:
            awaiting_reaction = self.awaiting_reactions[reaction.message.id]
            if awaiting_reaction.user_id == user.id and reaction.emoji in awaiting_reaction.allowed_emoji:
                await self.handle_reaction_add(reaction, user)
            return
        except KeyError:
            pass

    async def handle_reaction_add(self, reaction, user):
        response_method = get_response_type(reaction.message.guild, user, reaction.message.channel)

        awaiting_reaction = self.awaiting_reactions[reaction.message.id]

        tips = awaiting_reaction.tips
        mod_type = awaiting_reaction.mod_type

        try:
            emoji_num = int(reaction.emoji[0])
        except ValueError:
            await self.edit_page_change(reaction, awaiting_reaction)
            return

        del self.awaiting_reactions[reaction.message.id]

        chosen_tip = tips[emoji_num - 1]
        channel = reaction.message.channel
        if mod_type == "edit":
            await self.handle_tip_edit(response_method, chosen_tip, channel, user)
        else:  # mod_type == delete:
            await self.handle_tip_delete(response_method, chosen_tip, channel, user, awaiting_reaction.location)

    async def edit_page_change(self, reaction, awaiting_reaction):
        page_num = awaiting_reaction.page_num

        if reaction.emoji == "➡️":
            page_num += 1
        else:  # reaction.emoji == "⬅️"
            page_num -= 1

        awaiting_reaction.page_num = page_num
        message = reaction.message
        await message.clear_reactions()

        all_tips = self.get_tips(awaiting_reaction.location)
        index_low = (page_num-1) * 5
        index_high = page_num * 5

        if await check_higher_perms(reaction.message.author, reaction.message.guild):
            user_tips = all_tips
        else:
            user_tips = list(filter(lambda each_tip: each_tip.user_id == reaction.message.author.id, all_tips))
        user_tips.sort(reverse=True, key=lambda each_tip: each_tip.creation_time.time())

        page_count = ((len(user_tips) - 1) // 5) + 1
        tip_list = all_tips[index_low:index_high]
        tip_messages = [f"Which tip would you like to {awaiting_reaction.mod_type}?"]
        for index, tip in enumerate(tip_list):
            tip_messages.append(f"{index + 1}: {tip.create_selection_message()}")

        emoji_list = []
        for index in range(len(tip_list)):
            emoji = str(index + 1) + "\u20E3"
            emoji_list.append(emoji)

        if page_count > page_num:
            emoji_list.append("➡️")
        if page_num > 1:
            emoji_list.insert(0, "⬅️")
        tip_messages.append(f"Page {page_num}/{page_count}")
        awaiting_reaction.allowed_emoji = emoji_list
        awaiting_reaction.tips = tip_list

        await reaction.message.edit(content="\n".join(tip_messages))
        for emoji in emoji_list:
            await reaction.message.add_reaction(emoji)

    async def handle_tip_edit(self, response_method, tip, channel, user):
        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        channel_id = channel.id
        user_id = user.id
        await user.send(tip.create_tip_message())
        await response_method.send("A message containing the tip has been sent to you. The content of that tip will "
                                   "update to the content of your next message in this channel. If you wish to cancel "
                                   "the edit, type `cancel`.")
        tip_message = await self.bot.wait_for("message", check=check_message)

        if tip_message.content == "cancel":
            feedback = "Edit cancelled. Tip will remain as it was."
        else:
            tip.content = tip_message.content
            tip.edited = True

            feedback = "Edit success. The tip will now display your last message as its content."

        await response_method.send(feedback)

        self.save_storage()

    async def handle_tip_delete(self, response_method, tip, channel, user, location):
        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        channel_id = channel.id
        user_id = user.id
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

        self.save_storage()

    def delete_sector_tip(self, location, tip):
        sector_num = int(location[1])
        tip_type = self.tip_types[location[2]]
        numbered_sector = self.tip_storage["sectors"][sector_num][tip_type]
        if tip_type == "boss" or tip_type == "mini":
            try:
                boss_feat_num = int(location[3])
                numbered_sector["feats"][boss_feat_num].remove(tip)
            except IndexError:  # called if no loc[3]; signifies boss tip
                numbered_sector["tips"].remove(tip)

        else:  # tip_type == "feats" or "nodes"
            numbered_sector[int(location[3:])].remove(tip)


async def setup(bot):
    await bot.add_cog(SendConquestTips(bot))
