import datetime
import json
import os.path
import pickle
import sys
from copy import deepcopy
from functools import partial

import discord
from discord.ext import commands, tasks

from entities import tip as tip_module
from entities.command_parser import HolocronCommand, CommandTypes
from entities.interactions import AwaitingReaction
from entities.locations import HolocronLocation, LocationDisabledError
from entities.tip import Tip
from util import helpmgr
from util.command_checks import check_higher_perms
from util.datautils import clamp
from util.settings.response_handler import get_response_type
from util.settings.tip_sorting_handler import sort_tips

sys.modules['data.Tip'] = tip_module


class Holocron:
    """
    Class for all Holocrons to inherit from. Contains most base functionality required for Holocrons to work.
    Methods needing implementation at top, commands not included.
    """

    def __init__(self, bot: commands.Bot, name):
        self.bot = bot
        self.name = name
        self.storage_filepath = f"data/{self.name}/{self.name}_storage.pckl"

        self.awaiting_reactions = {}
        self.clean_awaiting_reactions.start()
        self.modifier_emoji_list = ["➕", "✍", "➖"]
        self.modifier_command_types = [CommandTypes.ADD, CommandTypes.EDIT, CommandTypes.DELETE]

        self.tip_storage = None
        self.load_storage()

        self.labels = self.load_labels()
        self.location_cls = None

    # Requires Implementation
    def dummy_populate(self):
        raise NotImplementedError

    def get_tips(self, location: HolocronLocation):
        raise NotImplementedError

    def get_all_tips(self):
        raise NotImplementedError

    def generate_stats_report(self):
        raise NotImplementedError

    def get_group_data(self, location, override_feats=False):
        raise NotImplementedError

    # Base Functionality
    def get_location(self, location_string, location_string_suffix=None, **kwargs) -> HolocronLocation:
        location_obj = self.location_cls(location_string, location_string_suffix, self.labels)
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
            await response_method.send("Dummy population not yet implemented.")
            return

        await response_method.send("Data added.")

    async def holocron_command_manager(self, ctx: commands.Context, *command_args):
        response_method = get_response_type(ctx.guild, ctx.author, ctx.channel)
        if len(command_args) == 0:
            await response_method.send(f"Holocron commands require extra information. For a list of commands and "
                                       f"options, use `{ctx.prefix}{self.name} help`.")
            return

        command_obj = HolocronCommand(*command_args)
        command_type = command_obj.command_type

        # await response_method.send(f"C: {command_obj.command_type} | A: {command_obj.address} | "
        #                            f"H: {command_obj.help_section} | ARGS: {command_obj.command_args} | "
        #                            f"RD: {command_obj.read_depth} | NA: {command_obj.new_author} | "
        #                            f"NTT: {command_obj.new_tip_text}")

        if command_obj.error:
            await response_method.send(f"Error when processing command. {command_obj.error}")
            return

        if command_type is CommandTypes.USER_MIGRATION:
            self.migrate_users(ctx.channel)
            await response_method.send('User names migrated to Global Names')
            return

        if command_type is CommandTypes.CLEAR:
            await self.request_clean_storage(ctx.guild, ctx.channel, ctx.author, response_method)
            return

        if command_type is CommandTypes.POPULATE:
            await self.request_dummy_populate(ctx.guild, ctx.author, response_method)
            return

        if command_type is CommandTypes.MAP:
            try:
                location = self.get_location(command_obj.address, is_map=True)
                map_name = location.get_map_name()
                await response_method.send(map_name,
                                           file=discord.File(f'data/{self.name}/images/{map_name.lower()}.png'))
            except NotImplementedError:
                await response_method.send(f"Map command not supported for {self.name}")
            return

        if command_type is CommandTypes.STATS:
            await response_method.send(self.generate_stats_report())
            return

        if command_type is CommandTypes.HELP:
            response = helpmgr.generate_bot_help(self.bot.get_command(self.name), ctx, command_obj.help_section)
            await response_method.send('\n'.join(response))
            return

        location = self.get_location(command_obj.address.lower())

        # detect and handle short addresses
        if location.is_group_location:
            if command_type is not CommandTypes.READ:
                await response_method.send('Error when processing command.\n'
                                           'Modification commends - add/edit/delete - must specify a full tip address. '
                                           f'e.g. {ctx.prefix}{self.name} {list(self.labels.keys())[-1]}')
                return
            await self.holocron_group_list(command_obj, location, response_method, ctx.author)
        else:
            await self.holocron_tips(command_obj, location, response_method, ctx.author, ctx.channel, ctx.guild)

    def migrate_users(self, channel):
        all_tips = self.get_all_tips()
        member_map = {}
        for member in channel.members:
            member_map[member.display_name] = member
            member_map[member.global_name] = member
            member_map[member.name] = member

        for tip in all_tips:
            author_obj = member_map.get(tip.author)
            if author_obj:
                tip.author = author_obj.display_name
                tip.user_id = author_obj.id

        self.save_storage()

    async def send_modifier_choices(self, user, sent_message, location):
        self.awaiting_reactions[sent_message.id] = AwaitingReaction(user.id, self.modifier_emoji_list,
                                                                    None, HolocronCommand(), location)

        for emoji in self.modifier_emoji_list:
            await sent_message.add_reaction(emoji)

    def format_tips(self, location: HolocronLocation, depth=3) -> str:
        location_tips = self.get_tips(location)
        total = len(location_tips)
        sort_tips(location_tips)
        top_n = location_tips[:depth]
        detail = location.get_detail()

        if len(top_n) > 0:
            output = [f"__**Recent tip{'' if len(top_n) == 1 else 's'} {len(top_n)}** "
                      f"(of {total}) for **{location.get_location_name()}**__"]

            if detail:
                output.append(detail)

            counter = 0
            for index, tip in enumerate(top_n):
                counter = index + 1
                output.append(f"{counter} - " + tip.create_tip_message())

            return '\n'.join(output)
        else:
            output = ""
            if detail:
                output += f"{detail}\n"
            output += f"There are no tips for {location.get_location_name()}."
            return output

    async def holocron_tips(self, command: HolocronCommand, tip_location: HolocronLocation,
                            response_method, author, channel, guild):
        command_type = command.command_type
        if command_type.is_modify_type():
            modifying = {
                CommandTypes.ADD: partial(self.add_tip, command, channel),
                CommandTypes.EDIT: partial(self.edit_tip, command, guild),
                CommandTypes.DELETE: partial(self.edit_tip, command, guild),
                CommandTypes.CHANGE_AUTHOR: partial(self.edit_tip, command, guild),
            }
            await modifying[command_type](author, tip_location, response_method)
            return

        try:
            num_tips = clamp(int(command.read_depth), 3, 10)
        except ValueError:
            await response_method.send(
                f"If you include a value after the address for reading or listing Tips, that value "
                f"defines how many tips to show. It must be a number between 3 and 10.\n"
                f"You entered: `{command.read_depth}`")
            return

        response = self.format_tips(tip_location, num_tips)
        sent_message = await response_method.send(response)
        await self.send_modifier_choices(author, sent_message, tip_location)

    async def holocron_group_list(self, command: HolocronCommand, location: HolocronLocation, response_method, author):
        # tip_location is a short address, missing a final id
        # looking to display a list of tip locations. however, it is possible the group itself
        # has tips e.g. bosses and mini-bosses in Conquest
        response = []
        if location.has_group_tips():
            response = [self.format_tips(location), ""]

        response.append(f"View Tips for which {location.get_address_type_name()}?")
        try:
            map_name = location.get_map_name()
            await response_method.send(file=discord.File(f'data/{self.name}/images/{map_name.lower()}_mini.png'))
        except (NotImplementedError, KeyError):
            pass

        group_data = self.get_group_data(location, override_feats=True)
        selection_idx = 1
        for section_id, tips in group_data.items():
            try:
                # added to support WIPs when some locations are disabled and it's not really an error yet
                temp_location = self.get_location(location.address, location_string_suffix=str(section_id),
                                                  is_group=True)
            except LocationDisabledError:
                continue

            tip_title = temp_location.get_tip_title()
            msg = f"{selection_idx} - {tip_title}"

            if not location.is_mid_level_location:
                count_tips = len(tips)
                msg += f" (#tips: {count_tips})"

            response.append(msg)
            selection_idx += 1

        emoji_list = []
        for index in range(selection_idx - 1):
            emoji = str(index + 1) + "\u20E3"
            emoji_list.append(emoji)

        emoji_list.append("🚫")
        sent_message = await response_method.send('\n'.join(response))

        self.awaiting_reactions[sent_message.id] = AwaitingReaction(author.id, emoji_list,
                                                                    list(group_data.keys()), command, location)

        for emoji in emoji_list:
            await sent_message.add_reaction(emoji)

    async def add_tip(self, command: HolocronCommand, channel, author, location: HolocronLocation, response_method):
        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        if not command.new_tip_text:
            await response_method.send(f"Your next message in this channel will be added as a tip "
                                       f"for {location.get_location_name()}.\n"
                                       f"If you wish to cancel, respond with `cancel`.")
            channel_id = channel.id
            user_id = author.id
            tip_response = await self.bot.wait_for("message", check=check_message)
            tip_message = tip_response.content
        else:
            tip_message = command.new_tip_text

        if tip_message.lower() == "cancel":
            await response_method.send("Tip addition has been cancelled.")
            return

        self.get_tips(location).append(Tip(content=tip_message, author=author.display_name, user_id=author.id))
        self.save_storage()

        sent_message = await response_method.send(f"Your tip has been added.\n{self.format_tips(location)}")
        await self.send_modifier_choices(author, sent_message, location)

    async def edit_tip(self, command: HolocronCommand, guild, author, location: HolocronLocation, response_method):
        tips_list = self.get_tips(location)

        if await check_higher_perms(author, guild):
            user_tips = tips_list
        else:
            user_tips = list(filter(lambda each_tip: each_tip.user_id == author.id, tips_list))

        if len(user_tips) > 0:
            sort_tips(user_tips)
            page_count = ((len(user_tips) - 1) // 5) + 1
            user_tips = user_tips[:5]

            tip_messages = [f"Which tip would you like to {command.command_type.description()}?"]
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

            self.awaiting_reactions[sent_tip_message.id] = \
                AwaitingReaction(author.id, emoji_list, user_tips, command, location)

            for emoji in emoji_list:
                await sent_tip_message.add_reaction(emoji)

        else:
            await response_method.send(f"There are no tips that you can {command.command_type.description()} "
                                       f"for {location.get_location_name()}.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if user.id == self.bot.user.id:
            return
        try:
            awaiting_reaction = self.awaiting_reactions[reaction.message.id]
            if awaiting_reaction.user_id == user.id and reaction.emoji in awaiting_reaction.allowed_emoji:
                await self.handle_reaction(reaction, user)
            return
        except KeyError:
            pass

    async def handle_reaction(self, reaction, user):
        response_method = get_response_type(reaction.message.guild, user, reaction.message.channel)

        awaiting_reaction = self.awaiting_reactions[reaction.message.id]

        tips = awaiting_reaction.tips
        command = awaiting_reaction.command
        location = awaiting_reaction.location

        try:
            emoji_num = int(reaction.emoji[0])
        except ValueError:  # if emoji is one of the arrow emojis
            if reaction.emoji == "🚫":
                del self.awaiting_reactions[reaction.message.id]
                await response_method.send("Selection Cancelled.")
                return
            elif reaction.emoji in self.modifier_emoji_list:
                idx = self.modifier_emoji_list.index(reaction.emoji)
                command.command_type = self.modifier_command_types[idx]
                command.address = location.address
                await self.holocron_tips(command, location, response_method, user,
                                         reaction.message.channel, reaction.message.guild)
                return
            else:
                await self.change_edit_page(reaction, awaiting_reaction, user)
                return

        del self.awaiting_reactions[reaction.message.id]

        chosen_tip = tips[emoji_num - 1]
        channel = reaction.message.channel
        if command.command_type is CommandTypes.READ:
            await self.handle_view_group(chosen_tip, location, response_method, user)
        elif command.command_type is CommandTypes.EDIT:
            await self.handle_tip_edit(chosen_tip, location, response_method, user, channel)
        elif command.command_type is CommandTypes.CHANGE_AUTHOR:
            await self.handle_change_author(chosen_tip, command.new_author, location, response_method,
                                            user, reaction.message.guild, channel)
        elif command.command_type is CommandTypes.DELETE:
            await self.handle_tip_delete(chosen_tip, location, response_method, user, channel)
        else:
            await response_method.send(f"Unexpected error when modifying a tip: {command.command_type}")

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

    async def handle_view_group(self, chosen, location: HolocronLocation, response_method, user):
        # location has a group address
        selected_location = self.get_location(location.address, location_string_suffix=str(chosen))
        command_obj = HolocronCommand(selected_location.address)
        if selected_location.is_group_location:
            await self.holocron_group_list(command_obj, selected_location, response_method, user)
        else:
            await self.holocron_tips(command_obj, selected_location, response_method, user, None, None)
        return

    async def handle_tip_edit(self, tip, location, response_method, user, channel):
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
            await response_method.send(feedback)
        else:
            tip.content = tip_message.content
            tip.edited = True
            self.save_storage()

            feedback = "Edit success.\n"
            feedback += f"{self.format_tips(location)}"
            sent_message = await response_method.send(feedback)
            await self.send_modifier_choices(user, sent_message, location)

    async def handle_tip_delete(self, tip, location, response_method, user, channel):
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
            self.save_storage()

            sent_message = await response_method.send(feedback)
            await self.send_modifier_choices(user, sent_message, location)
        else:
            await response_method.send("Deletion canceled. Tip not deleted.")

    async def handle_change_author(self, chosen_tip, new_author, location, response_method, user, guild, channel):
        if not check_higher_perms(user, guild):
            await response_method.send("Only Holocron Admins and Server admins can change author.")
            return

        chosen_tip.author = new_author

        member_id = {member_obj.display_name: member_obj.id for member_obj in channel.members}.get(new_author)
        if not member_id:
            member_id = {member_obj.global_name: member_obj.id for member_obj in channel.members}.get(new_author)
        chosen_tip.user_id = member_id
        self.save_storage()

        feedback = "Author change successful.\n"
        feedback += f"{self.format_tips(location)}"
        sent_message = await response_method.send(feedback)
        await self.send_modifier_choices(user, sent_message, location)

    @tasks.loop(time=datetime.time(hour=12))
    async def clean_awaiting_reactions(self):
        to_del = []
        for message_id, awaiting in self.awaiting_reactions.items():
            if (datetime.datetime.utcnow() - awaiting.creation_time).days >= 1:
                to_del.append(message_id)
        for message_id in to_del:
            del self.awaiting_reactions[message_id]
