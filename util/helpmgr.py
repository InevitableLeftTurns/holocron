from entities.command_parser import CommandTypes


class HelpContent:

    def __init__(self):
        self.content = None
        self.prefix = None
        self.modify_header = None

    def get_content(self, prefix, help_section: CommandTypes):
        if self.content is None or self.prefix != prefix:
            self.prefix = prefix
            self.content = self.generate_content()

        help_key = help_section.name.lower()
        try:
            content = self.content[help_key]
        except KeyError:
            return [f'{help_key} has no specific help']

        response = self.get_header(help_key)
        if not isinstance(content, list):
            # return is an array of items to be joined upstream
            response.append(content)
        else:
            for content_key in content:
                response.append(self.content[content_key])

        return response

    def get_header(self, help_section):
        if help_section in ["add", "edit", "delete"]:
            return [self.content['modify_header']]
        return []

    def generate_content(self):
        raise NotImplementedError


class ConquestHelp(HelpContent):

    def generate_content(self):
        return {

            "all": ["intro", "read", "list", "modify_header", "add", "edit", "delete", "clear"],

            "intro": f"Manages tips for the currently active conquest.\nStart with "
                     f"`{self.prefix}conquest`, then follow with options from below.\n",

            "read": f"*Accessing Tips*\n"
                    f"Simply place a `location` following `{self.prefix}conquest`. "
                    f"ex: `{self.prefix}conquest s1f2`.\n"
                    f"\tFor `location` codes, use `{self.prefix}help conquest location`.\n"
                    f"\tTo read more than the most recent 3 tips, follow with a #.\n"
                    F"\t\tex: `{self.prefix}con s3m1 5` to show 5 tips for Sector 1 Miniboss Feat 1\n",

            "list": f"You can `list` all feats for a Sector, Boss, or Miniboss by using a shortened address.\n"
                    f"\tex: `{self.prefix}con s3b` or `{self.prefix}con s3f` or `{self.prefix}con g`\n",

            "modify_header": f"*Tip Modification*\n"
                             f"To modify a tip, use the location and the modification type as below.\n "
                             f"ex: `{self.prefix}conquest <location> <command>` or "
                             f"`{self.prefix}conquest <command> <location>`",

            "add": f"* `add` - Add a tip to the specified location. "
                   f"ex: `{self.prefix}conquest s1f2 add` or `{self.prefix}conquest add s1f2`",

            'edit': f"* `edit` - Edit one of your tips. Only bot admins can edit any tip. "
                    f"ex: `{self.prefix}conquest s1f2 edit`or `{self.prefix}conquest edit s1f2`",

            'delete': f"* `delete` - Delete one of your tips. Only bot admins can delete any tip. "
                      f"ex: `{self.prefix}conquest s1f2 delete` or `{self.prefix}conquest delete s1f2`\n",

            'clear': f"*Clear All Tips*\n"
                     f"`{self.prefix}conquest clear`\n"
                     f"Permission role required. Intended for when conquests end.",

            'location': "Conquest location syntax will depend on what kind of location it is:\n"
                        "* Global Feats- global feats consist of `g` and a number representing which feat. "
                        "ex: `g3` for tips for Global Feat 3"
                        "* Sector Tips- Each kind of sector tip has a slightly different syntax, detailed "
                        "below, but all start with `s` and a number representing which sector. ex: `s2`.\n"
                        " * Boss- add `b` for tips on defeating the sector boss. ex: `s2b`\n"
                        " * Boss Feats- add `b` and the feat number to query boss feats. ex: `s2b3`\n"
                        " * Miniboss and Miniboss Feats- add `m`. Same syntax as boss. ex: `s4m` or `s4m2`\n"
                        " * Nodes- add `n` and a number representing which node. ex: `s3n16`\n"
                        " * Sector Feats- add `f` and a number representing which feat. ex: `s1f3`\n"
                        "* To `list` all feats for a Sector, Boss, or Miniboss use a shortened address.\n"
                        f"\tex: `{self.prefix}con s3b` or `{self.prefix}con s3f` or `{self.prefix}con g`\n",
        }


class RiseHelp(HelpContent):

    def generate_content(self):
        return {

            "all": ["intro", "read", "map", "modify_header", "add", "edit", "delete", "clear"],

            "intro": f"Manages tips for **Rise of the Empire** Territory Battle.\nStart with "
                     f"`{self.prefix}rise` or `{self.prefix}r`, then follow with options from below.\n",

            "read": f"*Accessing Tips*\n"
                    f"Simply place a `location` following `{self.prefix}rise`. "
                    f"ex: `{self.prefix}rise ds1cm2`.\n"
                    f"\tFor `location` codes, use `{self.prefix}help rise location` or use `map`.\n",

            "map": f"*Map*\n"
                   f"View location codes on a visual map, use `{self.prefix}rise map <location>`.\n"
                   f"Dark Side => ds, Mixed => mx, Light Side => ls and each tier is labeled 1 through 6.\n"
                   f"\tex: `{self.prefix}rise map ds3` for Dathomir or `{self.prefix}r map mx1` for Corellia\n",

            "modify_header": f"*Tip Modification*\n"
                             f"To modify a tip, use the location and the modification type as below.\n "
                             f"ex: `{self.prefix}rise <location> <command>` or "
                             f"`{self.prefix}rise <command> <location>`",

            "add": f"* `add` - Add a tip to the specified location. "
                   f"ex: `{self.prefix}rise ls2cm1 add` or `{self.prefix}rise add ls2cm1`",

            'edit': f"* `edit` - Edit one of your tips. Only bot admins can edit any tip. "
                    f"ex: `{self.prefix}rise mx3f edit` or `{self.prefix}rise mx3f edit`",

            'delete': f"* `delete` - Delete one of your tips. Only bot admins can delete any tip. "
                      f"ex: `{self.prefix}rise ds3sm1 delete` or `{self.prefix}rise ds3sm1 delete`\n",

            'clear': f"*Clear All Tips*\n"
                     f"`{self.prefix}rise clear`\n"
                     f"Permission role required. Intended for when conquests end.",

            'location': "Rise location syntax divides rise into 3 tracks, 6 destinations, and then battles:"
                        "locations are a combination of these addresses: `<track><destination><battle>`\n"
                        "* Tracks - Rise is split into 3 tracks, :\n"
                        "* Dark Side - ds"
                        "* Mixed - mx"
                        "* Light Side - ls"
                        "Destinations are addressed in order from 1 to 6.\n"
                        "* Dathomir on Dark Side is 3"
                        "* Corellia on Mixed is 1"
                        "* Bracca on Light Side is 2"
                        "Each combat or special mission is numbered left to right and is prefixed by its type. "
                        "Fleet is currently not numbered."
                        " * Combat Missions - cm"
                        " * Special Missions - sm"
                        " * Fleet - f"
                        "Examples:"
                        "* `ds2cm2` is the 2nd combat mission on Geonesis"
                        "* `mx3sm1` is Reva special mission on Tatooine"
                        "* `ls1f` is the fleet mission on Coruscant"
                        "\n"
                        "To view a visual map of each destination for battle addresses, you can use the `map` function"
                        f"* `{self.prefix}rise map ds2` will show the map for Geonesis"
                        f"* `{self.prefix}rise map mx1` will show the map for Corellia"
                        f"* `{self.prefix}rise map ls3` will show the map for Kashyyyk"
                        "Zeffo, the bonus planet on Light Side, is listed at `lsb`"
        }


class CounterHelp(HelpContent):

    def generate_content(self):
        return {

            "all": ["intro", "list", "read", "squad_header", "add_squad", "edit_squad", "modify_header", "add", "edit",
                    "delete", "clear"],

            "intro": f"Manages tips for counters in **Territory War** or **Grand Arena Championships**.\nStart with "
                     f"`{self.prefix}counter` or `{self.prefix}ctr`, "
                     f"then follow with the options below.\n",

            "list": f"**Listing Counters**\n"
                    f"Use the command `list` to show all squads with counter tips. This will list all squads including "
                    f"the `squad leader id` (e.g. `jmk` for Jedi Master Kenobi counters), the squad name, and the "
                    f"number of tips.\n",

            "read": f"**Accessing Counter Tips**\n"
                    f"Simply place a `<squad leader id>` following `{self.prefix}ctr`.\n"
                    f"ex: `{self.prefix}ctr jmk` or `{self.prefix}ctr see`.\n"
                    f"*aliases can also be used such as glrey for rey*\n"
                    f"  \n"
                    f"To filter to only TW or GAC counters follow the leader id with `TW`, `GAC`, or `GAC3`\n"
                    f"ex: `{self.prefix}ctr jmk gac` for 5v5 GAC specific counters.\n",

            "squad_header": f"**Adding and Editing Squads**\n"
                            f"To add or edit a squad use `add-squad` or `edit-squad` with the leader id.",

            "add_squad": f"`add-squad` - Add a squad to the list of squad counters. You will be prompted for a Squad "
                         f"Name and a Squad for counter tips such as `Commander Luke Skywalker` and "
                         f"`CLS/Han/Chewie/Chewpio/C3PO`\n"
                         f"ex: `{self.prefix}counter add-squad CLS` or `{self.prefix}ctr add-squad Reva`\n",

            'edit_squad': f"`edit-squad` - Edit one of the squads in the counter list. You will be prompted to set a "
                          f"new name and Squad such as `Maul` and `Maul/BAM/Armorer/Bo/Ordo`\n"
                          f"ex: `{self.prefix}counter edit-squad maul`\n",

            "modify_header": f"**Tip Modification**\n"
                             f"Use the corresponding command with the squad leader or select the icon after displaying "
                             f"tips.\n"
                             f"ex: `{self.prefix}ctr <leader> <command>`",

            "add": f"`add` - Add a counter tip to the specified squad. You will be prompted to add a counter squad "
                   f"and a description of how the counter works.\n"
                   f"ex: `{self.prefix}counter add cls` will add a counter against CLS squads.\n",

            'edit': f"`edit` - Edit one of your counter tips. You will be asked to edit both squad and counter "
                    f"description."
                    f"ex: `{self.prefix}counter edit maul` will update a counter against Maul squads.\n",

            'delete': f"`delete` - Delete one of your counter tips. \n"
                      f"ex: `{self.prefix}ctr 50rt delete`.\n",

            'clear': f"**Clear All Tips**\n"
                     f"`{self.prefix}counter clear`\n"
                     f"Permission role required.\n",

            'alias': "not yet supported. will allow multiple aliases for the same squad.\n"
        }


help_content = {
    'conquest': ConquestHelp(),
    'rise': RiseHelp(),
    'counter': CounterHelp(),
}


def generate_bot_help(command, ctx, help_section):
    response = []
    if command:
        aliases = "none" if len(command.aliases) == 0 else ", ".join(command.aliases)
        com_name = command.name
        response.append(f"**{ctx.prefix}{com_name}** (aliases: {aliases})")
        if com_name == "help":
            response.append(f"Provides a list of commands or help on specific ones.\n"
                            f"To get a list of commands, use `{ctx.prefix}help`, or for help on a certain "
                            f"command, use `{ctx.prefix}help [command]` or `{ctx.prefix}help [command] [subcommand]`.\n"
                            f"Help can also be displayed using `{ctx.prefix}[command] help [subcommand].`\n"
                            f"examples: `!help conquest` | `!help conquest add` | `!conquest help`"
                            f" | `!conquest help edit`")

        elif com_name == "settings":
            response.append(f"A list of settings applied to the server and their current values. To edit server "
                            f"settings, you must have the permission role, then use `{ctx.prefix}settings edit`.")
        else:
            try:
                response.extend(help_content[com_name].get_content(ctx.prefix, help_section))
            except [IndexError, KeyError]:
                response.append(f"({command.name} has no help section. Referring to description.)\n"
                                f"{command.description}")

    return response
