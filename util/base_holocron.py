import datetime

import discord
import json
import os.path
import pickle
from copy import deepcopy
from data.AwaitingReaction import AwaitingReaction
from data.Tip import Tip
from discord.ext import commands, tasks
from functools import partial

from entities.locations import HolocronLocation
from util import helpmgr
from util.command_checks import check_higher_perms
from util.datautils import clamp
from util.settings.response_handler import get_response_type
from util.settings.tip_sorting_handler import sort_tips


class Holocron:
    """
    Class for all Holocrons to inherit from. Contains most base functionality required for Holocrons to work.
    Methods needing implementation at top, commands not inlcuded.
    """

    def __init__(self, bot: commands.Bot, name):
        self.bot = bot
        self.name = name
        self.storage_filepath = f"data/{self.name}/{self.name}_storage.pckl"

        self.awaiting_reactions = {}
        self.clean_awaiting_reactions.start()

        self.tip_storage = None
        self.load_storage()

        self.labels = self.load_labels()
        self.location_cls = None

    # Requires Implementation

    def dummy_populate(self):
        raise NotImplementedError

    def get_tips(self, location: HolocronLocation):
        raise NotImplementedError

    def get_group_data(self, location, feats=False):
        raise NotImplementedError

    # Base Functionality
    def get_location(self, location_string, **kwargs) -> HolocronLocation:
        location_obj = self.location_cls(location_string, self.labels)
        location_obj.parse_location(**kwargs)
        return location_obj

    def load_storage(self):
        if os.path.exists(self.storage_filepath):
            with open(self.storage_filepath, "rb") as storage_file:
                self.tip_storage = pickle.load(storage_file)
        else:
            self.clean_storage()
            self.save_storage()

    def load_labels(self):
        with open(f'data/{self.name}/labels.json') as labels_file:
            return json.load(labels_file)

    def clean_storage(self):
        self.tip_storage = {}
        with open(f"data/{self.name}/base.json") as config_file:
            config = json.load(config_file)

        self.tip_storage = self.config_to_storage(config)
        self.save_storage()

    def config_to_storage(self, config: dict):
        storage = {}
        for section, section_config in config.items():
            sub_sections = section_config.get('subs', {})
            sub_section_storage = self.config_to_storage(sub_sections)

            section_storage = {}
            section_count = section_config.get('count', 0)
            if section_count:
                # duplicate subsection in a dict of index -> subsection data for count times
                for idx in range(0, section_count):
                    section_storage[idx + 1] = deepcopy(sub_section_storage or [])
            else:
                if section_config.get('tips'):
                    section_storage['tips'] = []
                section_storage.update(sub_section_storage)

            storage[section] = section_storage
        return storage

    def save_storage(self):
        with open(self.storage_filepath, "wb") as storage_file:
            pickle.dump(self.tip_storage, storage_file)

    async def request_clean_storage(self, guild, channel, author, response_method):
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
            self.clean_storage()
            feedback = "Tip storage has been cleared."

        await response_method.send(feedback)

    async def request_dummy_populate(self, guild, author, response_method):
        if not await check_higher_perms(author, guild):
            await response_method.send("You do not have access to this command.")
            return

        try:
            self.dummy_populate()
        except NotImplementedError:
            await response_method.send("Dummy popuation not yet implemented.")
            return

        await response_method.send("Data added.")

    async def holocron_command_manager(self, ctx: commands.Context, *args):
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

        elif user_command == 'map':
            location = self.get_location(args[1:], is_map=True)
            map_name = location.get_map_name()
            await response_method.send(map_name,
                                       file=discord.File(f'data/{self.name}/images/{map_name}.png'))

        elif user_command == 'help':
            commands_args = args[1:]
            response = helpmgr.generate_bot_help(self.bot.get_command(self.name), ctx, *commands_args)
            await response_method.send('\n'.join(response))
            return

        else:
            location = self.get_location(user_command.lower())

            # detect and handle short addresses
            if location.is_group_location():
                # what about boss tips?
                await self.holocron_handle_group(ctx.author, response_method, location)
            else:
                try:
                    to_edit = args[1]
                except IndexError:
                    to_edit = ""
                await self.holocron_tips(ctx.guild, ctx.channel, ctx.author, response_method, location, to_edit)
                return

    def format_tips(self, location: HolocronLocation, depth=3):
        location_tips = self.get_tips(location)
        total = len(location_tips)
        sort_tips(location_tips)
        top_n = location_tips[:depth]
        detail = location.get_detail()

        if len(top_n) > 0:
            response = [f"__**Recent {len(top_n)} tip{'' if len(top_n) == 1 else 's'} "
                        f"(of {total}) for {location.get_location_name()}**__"]

            if detail:
                response.append(detail)

            for index, tip in enumerate(top_n):
                response.append(f"{index + 1} - " + tip.create_tip_message())

            return '\n'.join(response)
        else:
            response = ""
            if detail:
                response += f"{detail}\n"
            response += f"There are no tips for {location.get_location_name()}."
            return response

    async def holocron_tips(self, guild, channel, author, response_method, tip_location: HolocronLocation, subcommand):
        if subcommand in ["add", "edit", "delete"]:
            modifying = {
                "add": partial(self.add_tip, channel),
                "edit": partial(self.edit_tip, subcommand, guild),
                "delete": partial(self.edit_tip, subcommand, guild)
            }
            await modifying[subcommand](author, tip_location, response_method)
            return

        elif subcommand and subcommand.isdigit():
            num_tips = clamp(int(subcommand), 3, 10)

        else:
            num_tips = 3

        response = self.format_tips(tip_location, num_tips)
        await response_method.send(response)

    async def holocron_handle_group(self, author, response_method, group_location: HolocronLocation):
        # tip_location is a short address, missing a trailing numeral and therefore
        # looking to display a list of tip locations. however, it is possible the group itself
        # has tips e.g. bosses and mini-bosses in Conquest
        response = []
        try:
            response = [self.format_tips(group_location), ""]
        except LookupError:
            pass
        except ValueError:
            pass

        response.append(f"View Tips for which feat?")  # group_location.get_leaf_name()

        group_data = self.get_group_data(group_location, True)
        for idx, tips in group_data.items():
            tip_title = group_location.get_tip_title() + f"{str(idx)}"
            count_tips = len(tips)

            response.append(f"{idx} - {tip_title} (#tips: {count_tips})")

        emoji_list = []
        for index in range(len(group_data)):
            emoji = str(index + 1) + "\u20E3"
            emoji_list.append(emoji)

        emoji_list.append("🚫")
        sent_message = await response_method.send('\n'.join(response))

        self.awaiting_reactions[sent_message.id] = AwaitingReaction(author.id, emoji_list,
                                                                    list(group_data.keys()), 'view', group_location)

        for emoji in emoji_list:
            await sent_message.add_reaction(emoji)

    async def add_tip(self, channel, author, location: HolocronLocation, response_method):
        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        await response_method.send(f"Your next message in this channel will be added as a tip "
                                   f"for {location.get_location_name()}.\n"
                                   f"If you wish to cancel, respond with `cancel`.")
        channel_id = channel.id
        user_id = author.id
        tip_message = await self.bot.wait_for("message", check=check_message)

        if tip_message.content.lower() == "cancel":
            await response_method.send("Tip addition has been cancelled.")
            return

        self.get_tips(location).append(Tip(tip_message))
        self.save_storage()

        await response_method.send(f"Your tip has been added.\n{self.format_tips(location)}")

    async def edit_tip(self, mod_type, guild, author, location: HolocronLocation, response_method):
        tips_list = self.get_tips(location)

        if await check_higher_perms(author, guild):
            user_tips = tips_list
        else:
            user_tips = list(filter(lambda each_tip: each_tip.user_id == author.id, tips_list))

        if len(user_tips) > 0:
            sort_tips(user_tips)
            page_count = ((len(user_tips) - 1) // 5) + 1
            user_tips = user_tips[:5]

            tip_messages = [f"Which tip would you like to {mod_type}?"]
            for index, tip in enumerate(user_tips):
                tip_messages.append(f"{index + 1} - {tip.create_selection_message()}")

            emoji_list = []
            for index in range(len(user_tips)):
                emoji = str(index + 1) + "\u20E3"
                emoji_list.append(emoji)

            if page_count > 1:
                tip_messages.append(f"Page 1/{page_count}")
                emoji_list.append("➡️")
            emoji_list.append("🚫")

            sent_tip_message = await response_method.send("\n".join(tip_messages))

            self.awaiting_reactions[sent_tip_message.id] = AwaitingReaction(author.id, emoji_list, user_tips,
                                                                            mod_type, location)

            for emoji in emoji_list:
                await sent_tip_message.add_reaction(emoji)

        else:
            await response_method.send(f"There are no tips that you can {mod_type} for {location.get_location_name()}.")

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
        location = awaiting_reaction.location

        try:
            emoji_num = int(reaction.emoji[0])
        except ValueError:  # if emoji is one of the arrow emojis
            if reaction.emoji == "🚫":
                del self.awaiting_reactions[reaction.message.id]
                await response_method.send("Selection Cancelled.")
                return
            await self.change_edit_page(reaction, awaiting_reaction, user)
            return

        del self.awaiting_reactions[reaction.message.id]

        chosen_tip = tips[emoji_num - 1]
        channel = reaction.message.channel
        if mod_type == "view":
            await self.handle_view_group(response_method, chosen_tip, location)
        elif mod_type == "edit":
            await self.handle_tip_edit(response_method, chosen_tip, location, channel, user)
        else:  # mod_type == delete:
            await self.handle_tip_delete(response_method, chosen_tip, channel, user, location)

    async def change_edit_page(self, reaction, awaiting_reaction, user):
        page_num = awaiting_reaction.page_num

        if reaction.emoji == "➡️":
            page_num += 1
        else:  # reaction.emoji == "⬅️"
            page_num -= 1

        awaiting_reaction.page_num = page_num
        message = reaction.message
        await message.clear_reactions()

        all_tips = self.get_tips(awaiting_reaction.location)
        index_low = (page_num - 1) * 5
        index_high = page_num * 5

        if await check_higher_perms(user, reaction.message.guild):
            user_tips = all_tips
        else:
            user_tips = list(filter(lambda each_tip: each_tip.user_id == reaction.message.author.id, all_tips))
        sort_tips(user_tips)

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

    async def handle_view_group(self, response_method, chosen, location):
        selected_location = self.get_location(location + str(chosen))
        await self.holocron_tips(None, None, None, response_method, selected_location, '')
        return

    async def handle_tip_edit(self, response_method, tip, location, channel, user):
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

            feedback = "Edit success.\n"
            feedback += f"{self.format_tips(location)}"

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
            self.get_tips(location).remove(tip)
            feedback = "Tip deleted.\n"
            feedback += f"{self.format_tips(location)}"
        else:
            feedback = "Deletion canceled. Tip not deleted."

        await response_method.send(feedback)

        self.save_storage()

    @tasks.loop(time=datetime.time(hour=12))
    async def clean_awaiting_reactions(self):
        to_del = []
        for message_id, awaiting in self.awaiting_reactions.items():
            if (datetime.datetime.utcnow() - awaiting.creation_time).days >= 1:
                to_del.append(message_id)
        for message_id in to_del:
            del self.awaiting_reactions[message_id]
