from discord.ext import commands

from entities.base_holocron import Holocron
from entities.command_parser import HolocronCommand, CommandTypes
from entities.counters import Squad, CounterTip, Alias
from entities.locations import CounterLocation, InvalidLocationError
from util.parsers import counter_parser
from util.settings.tip_sorting_handler import sort_tips


class CounterHolocron(commands.Cog, Holocron):
    def __init__(self, bot=commands.Bot):
        super().__init__(bot, "counter")
        self.location_cls = CounterLocation

    def dummy_populate(self):
        jmk = Squad(lead_id="jmk", lead="Jedi Master Kenobi", author="trich")
        see = Squad(lead_id="see", lead="Sith Eternal Emperor", author="trich")
        self.tip_storage["squads"][jmk.lead_id] = jmk
        self.tip_storage["squads"][see.lead_id] = see

        jmk.tips = [
            CounterTip(squad="JMK/CAT/GK/Padme/Ahsoka Mirror",
                       content="I'm running 2 leaders resolve and a green ZA; Han shoots Echo, Dash nuke; works down to 30% - probably more if I was a touch faster.",
                       author="uaq", edited=True,
                       rating=0),
            CounterTip(squad="vs JMK/CAT/GK/Padme/Ahsoka",
                       content="Jabba/Boussh/Krrs/Boba/Lando standard counter\n"
                               "Leia/Drogan/R2/Ben/Crex standard counter", activity="GAC",
                       author="uaq", rating=0),
            CounterTip(squad="vs standard JMK squad", content="tip 4 for jmk for GAC 3v3",
                       activity="GAC3", author="trich", rating=0),
            CounterTip(squad="Yet another Counter", content="tip 5 for jmk for TW", activity="TW",
                       author="trich", rating=0),
        ]

        see.tips = [
            CounterTip(squad="SEE/Bane Mirror", content="tip 1 for countering see", author="uaq", rating=0),
            CounterTip(squad="JMK/CAT/any vs SEE/any", content="tip 2 for countering see", author="uaq", rating=0),
            CounterTip(squad="Jabba++ vs SEE/any", content="tip 3 for countering see", author="trich", rating=0),
        ]

        self.tip_storage["aliases"]["glk"] = Alias("glk", jmk.lead_id, author="uaq")

        self.save_storage()

    def _find_activity(self, location: CounterLocation, tip_message: str) -> (str, str | None):
        index = tip_message.find("tag=")
        if index != -1:
            end_index = tip_message.find(" ", index + 4)
            if end_index > index:
                activity = tip_message[index + 4:end_index]
            else:
                activity = tip_message[index + 4:]

            if activity.upper() in location.valid_activities:
                # remove from message (using original value), bump value, and return both
                tip_message = tip_message.replace(f"tag={activity}", "").strip()
                activity = activity.upper()
                return tip_message, activity
        return tip_message, None

    async def add_tip(self, command: HolocronCommand, channel, author, location: CounterLocation, response_method):

        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        if not command.new_tip_text:
            await response_method.send(
                f"Enter the title of this counter for {location.get_location_name()}.\n"
                f"Example: `Jabba/Boussh/Krrs/Lando/Embo vs JMK/CAT/GK/Ahsoka/Padme` or `Leia/Drogan/Any vs any JMK`\n"
                f"If you wish to cancel, respond with `cancel`.")
            channel_id = channel.id
            user_id = author.id
            tip_response = await self.bot.wait_for("message", check=check_message)
            squad = tip_response.content
        else:
            squad = command.new_tip_text

        if squad.lower() == "cancel":
            await response_method.send("Tip addition has been cancelled.")
            return

        await response_method.send(f"Title added. Now enter any helpful context to the counter.\n"
                                   f"Examples: `standard counter` or `requires Bane Datacron`\n"
                                   f"If you wish to cancel, respond with `cancel`.")
        channel_id = channel.id
        user_id = author.id
        tip_response = await self.bot.wait_for("message", check=check_message)
        tip_message = tip_response.content

        existing_squad = self.tip_storage["squads"][location.actual_squad_lead_id]
        tip_message, activity = self._find_activity(location, tip_message)

        existing_squad.tips.append(CounterTip(squad=squad, content=tip_message, activity=activity,
                                              author=author.display_name, user_id=author.id))
        self.save_storage()
        sent_message = await response_method.send(f"Your tip has been added.\n{self.format_tips(location)}")
        await self.send_modifier_choices(author, sent_message, location)
        return

    async def add_squad(self, command: HolocronCommand, channel, author, location: CounterLocation, response_method):
        def check_message(message):
            return message.channel.id == channel_id and message.author.id == user_id

        if command.command_type is CommandTypes.ADD_SQUAD and self.squad_exists(location):
            raise InvalidLocationError(f"Squad already exists: `{location}`")

        if not command.new_tip_text:
            await response_method.send(f"Please enter the Squad Name for {location}. (e.g. `Jedi Master Kenobi)`\n"
                                       f"If you wish to cancel, respond with `cancel`.")
            channel_id = channel.id
            user_id = author.id
            response = await self.bot.wait_for("message", check=check_message)
            leader = response.content
        else:
            leader = command.new_tip_text

        if leader.lower() == "cancel":
            await response_method.send("Squad addition has been cancelled.")
            return

        self.add_squad_to_storage(command, location, leader, author)

        sent_message = await response_method.send(f"Your squad has been added.\n{self.format_tips(location)}")
        await self.send_modifier_choices(author, sent_message, location)

    def add_squad_to_storage(self, command: HolocronCommand, location: CounterLocation, lead, author):
        new_squad = Squad(lead_id=location.actual_squad_lead_id, lead=lead,
                          author=author.display_name, user_id=author.id)

        existing = self.tip_storage["squads"].get(location.actual_squad_lead_id)
        if command.command_type is CommandTypes.EDIT_SQUAD and existing:
            new_squad.tips = existing.tips
        elif existing:
            raise InvalidLocationError(f"Squad already exists: `{location.actual_squad_lead_id}`")

        self.tip_storage['squads'][new_squad.lead_id] = new_squad
        self.save_storage()

    def squad_exists(self, location: CounterLocation):
        return self.get_squad(location) is not None

    async def handle_import(self, command: HolocronCommand, location: CounterLocation, author, response_method):
        if len(command.command_args) != 2:
            raise InvalidLocationError("Import command must have a squad id, import address, and season #.\n"
                                       f"You provided {command.address} {' '.join(command.command_args)}.\n")

        # if location not in self.tip_storage["squads"]:
        #     raise InvalidLocationError("Invalid Squad id. Import must import into an existing squad.\n"
        #                                f"You provided {command.address}.\n")

        leader_id = command.address
        import_lead, season_id = command.command_args
        counters, characters_map = counter_parser.run_parser(leader_id, import_lead, season_id)

        activity = "GG"
        if int(season_id) % 2 != 0:
            activity = "GG3"

        tips_added = 0
        for grouped_counters in counters.values():
            idx = 0
            output = ""
            defense = ""
            for actual_counter in grouped_counters:
                if actual_counter.wins_float() < 50.0:
                    continue
                idx += 1
                if idx == 1:
                    defense = f"{', '.join([characters_map[defender]['name'] for defender in actual_counter.defenders])}"

                attackers = f"{', '.join([characters_map[ac]['name'] for ac in actual_counter.attackers])}"
                output += f"Attackers: {attackers}\n"
                output += f"\tWin %: {actual_counter.wins_float()}"
                output += f"\tAvg Points: {actual_counter.points}\n"

            if idx > 0:
                existing_squad = self.tip_storage["squads"][leader_id]
                existing_squad.tips.append(CounterTip(squad=f"vs {defense}", content=output, activity=activity,
                                                      author=author.display_name, user_id=author.id))
                tips_added += 1

        self.save_storage()
        sent_message = await response_method.send(f"{tips_added} tips imported.\n"
                                                  f"{self.format_tips(location, read_filters=['5'])}")
        await self.send_modifier_choices(author, sent_message, location)
        return

    def add_alias_to_storage(self, location: CounterLocation, author):
        pass

    def format_tips(self, location: CounterLocation, read_filters=None):
        squad = self.get_squad(location)
        counter_tips = self.get_tips(location)

        activity = location.check_activity(read_filters)
        if activity:
            counter_tips = [tip for tip in counter_tips if tip.activity == activity]

        total = len(counter_tips)
        sort_tips(counter_tips)
        top_n = counter_tips[:self._read_depth(read_filters)]

        if len(top_n) > 0:
            output = [f"__**Recent tip{'' if len(top_n) == 1 else 's'} for {location.get_location_name()}**__\n"]

            # output.append(squad.create_squad_detail_message())

            for index, tip in enumerate(top_n):
                counter = index + 1
                output.append(f"{counter} - " + tip.create_tip_message())

            return '\n'.join(output)
        else:
            return f"There are no tips for **{location.get_location_name()}**.\n"

    def get_squad(self, location: CounterLocation):
        return self.tip_storage["squads"].get(location.actual_squad_lead_id)

    def get_tips(self, location: CounterLocation):
        squad = self.tip_storage["squads"].get(location.actual_squad_lead_id)
        if not squad:
            raise InvalidLocationError(f"Squad Leader not found: '{location.actual_squad_lead_id}'.")

        return squad.tips

    def get_list(self):
        # this is really get squads
        output = "**Listing all squads for counters**\n"
        for squad in sorted(self.tip_storage["squads"].values(), key=lambda squad: squad.lead):
            output += f"`{squad.lead_id}`\t{squad.lead}"  # \t \t[{squad.squad}]"
            output += f"\t*tips: {len(squad.tips)}*\n"
        return output

    def get_all_tips(self):
        all_tips = []
        for squad_id, squad in self.tip_storage["squads"].items():
            all_tips.extend(squad.tips)
        return all_tips

    def generate_stats_report(self):
        total_squad_count = len(self.tip_storage["squads"])
        total_alias_count = len(self.tip_storage["aliases"])
        total_tip_count = len(self.get_all_tips())
        return f"Counter Holocron Total Squads: {total_squad_count}\n" \
               f"Counter Holocron Total Tips: {total_tip_count}\n" \
               f"Counter Holocron Aliases: {total_alias_count}\n"

    def get_group_data(self, location: CounterLocation, feats=False):
        raise NotImplementedError

    def get_map_name(self, location: CounterLocation, *args):
        raise NotImplementedError

    def load_labels(self):
        return self.tip_storage

    def config_to_storage(self, config: dict):
        return config

    @commands.command(name="counter", aliases=["ctr"], extras={'is_holocron': True},
                      description="Access the Counter Holocron for reading and managing Territory War "
                                  "and Grand Arena Championship Counter Tips")
    async def counter_manager(self, ctx: commands.Context, *args):
        await self.holocron_command_manager(ctx, *args)


async def setup(bot):
    await bot.add_cog(CounterHolocron(bot))
