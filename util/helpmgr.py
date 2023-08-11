class HelpContent:

    def __init__(self):
        self.content = None
        self.prefix = None

    def get_content(self, prefix, subcommand):
        if self.content is None or self.prefix != prefix:
            self.prefix = prefix
            self.content = self.generate_content()

        subcommand = subcommand or 'all'

        try:
            content = self.content[subcommand]
        except KeyError:
            return [f'{subcommand} has no specific help']

        response = self.get_header(subcommand)
        if not isinstance(content, list):
            # return is an array of items to be joined upstream
            response.append(content)
        else:
            for content_key in content:
                response.append(self.content[content_key])

        return response

    def get_header(self, subcommand):
        raise NotImplementedError

    def generate_content(self):
        raise NotImplementedError


class ConquestHelp(HelpContent):

    def __init__(self):
        super().__init__()
        self.modify_header = None

    def get_header(self, subcommand):
        if subcommand in ["add", "edit", "delete"]:
            return [self.content['modify_header']]
        return []

    def generate_content(self):
        return {

            "all": ["intro", "read", "list", "modify_header", "add", "edit", "delete", "clear"],

            "intro": f"Manages tips for the currently active conquest.\nStart with "
                     f"`{self.prefix}conquest`, then follow with options from below.\n",

            "read": f"*Accessing Tips*- Simply place a `location` following `{self.prefix}conquest`. "
                    f"ex: `{self.prefix}conquest s1f2`.\n"
                    f"\tFor `location` codes, use `{self.prefix}help conquest location`.\n"
                    f"\tTo read more than the most recent 3 tips, follow with a #.\n"
                    F"\t\tex: `{self.prefix}con s3m1 5` to show 5 tips for Sector 1 Miniboss Feat 1\n",

            "list": f"You can `list` all feats for a Sector, Boss, or Miniboss by using a shortened address.\n"
                    f"\tex: `{self.prefix}con s3b` or `{self.prefix}con s3f` or `{self.prefix}con g`\n",

            "modify_header": f"*Tip Modification*- For the below modifications, place the corresponding tag "
                             f"after your location.\nex: `{self.prefix}conquest <location> <command>`",

            "add": f"* `add` - Add a tips to the specified location. "
                   f"ex: `{self.prefix}conquest s1f2 add`.",

            'edit': f"* `edit` - Edit one of your tips. Bot admins can edit any tip. "
                    f"ex: `{self.prefix}conquest s1f2 edit`.",

            'delete': f"* `delete` - Delete one of your tips. Bot admins can delete any tip. "
                      f"ex: `{self.prefix}conquest s1f2 delete`.\n",

            'clear': f"*Clear All Tips*- `{self.prefix}conquest clear`. Permission role required. "
                     f"Intended for when conquests end.",

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


help_content = {
    'conquest': ConquestHelp(),
}


def generate_bot_help(command, ctx, subcommand=None, *command_args):
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
                response.extend(help_content[com_name].get_content(ctx.prefix, subcommand))
            except [IndexError, KeyError]:
                response.append(f"({command.name} has no help section. Referring to description.)\n"
                                f"{command.description}")

    return response
