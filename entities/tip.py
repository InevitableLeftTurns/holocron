from datetime import datetime

import discord


class Tip:
    def __init__(self, content="", author="n/a", rating=0, user_id=0):
        self.content = content
        self.author = author
        self.rating = rating
        self.user_id = user_id
        self.creation_time = datetime.utcnow()
        self.edited = False

    def create_tip_message(self, rating=False):
        # *(+/-rating)* **Tip from author** *(edited)*:\ncontent
        edited = "" if not self.edited else " *(edited)*"
        rating = "" if not rating else " *({0:+})*".format(self.rating)
        return f"**Tip from {self.author}**{rating}:\n\t{self.content}{edited}"

    def create_selection_message(self):
        # **author**: first_50_char (time_ago)
        return f"**{self.author}**: {self.content[:50]} ({self.get_elapsed_time()})"

    def create_delete_message(self):
        # author: first_50_char
        return f"{self.author}: {self.content[:50]}"

    def get_elapsed_time(self):
        def plural(number):
            return '' if number == 1 else 's'

        present = datetime.utcnow()
        elapsed_timedelta = present - self.creation_time

        if elapsed_timedelta.days >= 365:
            return "more than 1 year ago"

        months = elapsed_timedelta.days // 30.5
        days = elapsed_timedelta.days
        seconds = elapsed_timedelta.seconds
        minutes = seconds // 60
        hours = minutes // 60

        if months > 0:
            will_round = (days // 15.25) % 2
            if will_round:
                return f"{months + 1} month{plural(months)} ago"
            else:
                return f"{months} month{plural(months)} ago"

        elif days > 0:
            will_round = (hours // 12) % 2
            if will_round:
                return f"{days + 1} day{plural(days)} ago"
            else:
                return f"{days} day{plural(days)} ago"

        elif hours > 0:
            will_round = (minutes // 30) % 2
            if will_round:
                return f"{hours + 1} hour{plural(hours)} ago"
            else:
                return f"{hours} hour{plural(hours)} ago"

        elif minutes > 0:
            will_round = (seconds // 30) % 2
            if will_round:
                return f"{minutes + 1} minute{plural(minutes)} ago"
            else:
                return f"{minutes} minute{plural(minutes)} ago"
        elif seconds > 10:
            return f"{seconds} seconds ago"

        return "just now"

    def __repr__(self):
        return f"({self.rating}) {self.author}"

    def to_json(self):
        return {"author": self.author,
                "rating": self.rating,
                "content": self.content,
                "edited": self.edited,
                "userid": self.user_id,
                "creation_time": self.creation_time
                }
