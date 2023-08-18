from enum import Enum


class CommandTypes(Enum):
    POPULATE = -1
    HELP = 0
    READ = 1
    ADD = 2
    EDIT = 3
    DELETE = 4
    MAP = 5
    STATS = 6

    # helper type
    ALL = 100

    # requiring admin role
    CLEAR = 100
    CHANGE_AUTHOR = 101

    CLEAR_COMMANDS = [
        "clean",
        "reset",
        "clear"
    ]
    POPULATE_COMMANDS = [
        "dummy",
        "populate",
        "test"
    ]
    CHANGE_AUTHOR_ALIASES = [
        "reassign",
        "author",
    ]

    @classmethod
    def lookup(cls, enum_str: str):
        return cls.__members__.get(enum_str.upper(), cls.check_aliases(enum_str.lower()))

    @classmethod
    def check_aliases(cls, alias: str):
        if alias in cls.CLEAR_COMMANDS.value:
            return cls.CLEAR

        if alias in cls.POPULATE_COMMANDS.value:
            return cls.POPULATE

        if alias in cls.CHANGE_AUTHOR_ALIASES.value:
            return cls.CHANGE_AUTHOR

        return None

    def is_modify_type(self):
        if self in [self.ADD, self.EDIT, self.DELETE]:
            return True
        return False


class HolocronCommand:

    def __init__(self, *user_inputs):
        self.command_type = None
        self.address = None
        self.error = None

        # contextual attributes
        self.help_section = None
        self.read_depth = 3
        self.new_tip_text = None
        self.new_author = None
        self.command_args = []

        # parsing
        self.parse_command(*user_inputs)
        self.parse_command_args()

    modify_commands = [
        'add',
        'edit',
        'delete',
    ]

    def parse_command(self, *user_inputs):
        if not user_inputs:
            return

        command_arg = user_inputs[0].lower()
        found_command = CommandTypes.lookup(command_arg)

        if found_command and self.command_type is CommandTypes.HELP:
            self.help_section = found_command
        elif found_command is CommandTypes.HELP and self.command_type:
            swap = self.command_type
            self.command_type = CommandTypes.HELP
            self.help_section = swap
        elif found_command:
            self.command_type = found_command
        elif not self.address:
            # assume the first non-command is an address
            self.address = command_arg
        else:
            # this is an argument to the command and address
            self.command_args.append(command_arg)

        self.parse_command(*user_inputs[1:])

    def parse_command_args(self):
        if not self.command_type:
            self.command_type = CommandTypes.READ

        if self.command_type is CommandTypes.HELP and not self.help_section and not self.command_args:
            self.help_section = CommandTypes.ALL

        if not self.command_args:
            return

        if self.command_type is CommandTypes.READ:
            self.read_depth = self.command_args[0]
            self._shift_args()

        if self.command_type is CommandTypes.ADD:
            if len(self.command_args) > 1:
                self.error = 'Surround the text with double quotes (`\"text\"`) to add the tip inline'
            else:
                self.new_tip_text = self.command_args[0]
                self._shift_args()

        if self.command_type is CommandTypes.CHANGE_AUTHOR:
            self.new_author = self.command_args[0]
            self._shift_args()

    def _shift_args(self):
        self.command_args = self.command_args[1:]
