from datetime import datetime

from entities.command_parser import HolocronCommand
from entities.locations import HolocronLocation


class AwaitingReaction:
    def __init__(self, user_id, allowed_emoji, tips, command: HolocronCommand, location: HolocronLocation, page_num=1):
        self.user_id = user_id
        self.allowed_emoji = allowed_emoji
        self.tips = tips
        self.command = command
        self.location = location
        self.page_num = page_num
        self.creation_time = datetime.utcnow()

    def __repr__(self):
        return f"@{self.location}: {self.command.command_type.name}"
