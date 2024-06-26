import datetime
import uuid

from entities.tip import Tip


class Squad:

    def __init__(self, lead_id: str, lead: str, squad: str, variants=None, author="n/a", user_id=0):
        self.lead_id = lead_id.lower()
        self.lead = lead.title()
        self.squad = squad
        self.variants = variants or []
        self.author = author
        self.user_id = user_id
        self.edited = False
        self.creation_time = datetime.datetime.utcnow()
        self.tips = []

    def create_squad_header_message(self) -> str:
        return f"{self.lead} (`{self.lead_id}`)"

    def create_squad_detail_message(self) -> str:
        variants = ""
        if self.variants:
            variant_str = ", ".join([variant for variant in self.variants])
            variants = f"***variants***: {variant_str}\n"
        output = f"**Squad:** {self.squad}\n{variants}"
        return output

    def to_json(self):
        return {
            "lead_id": self.lead_id,
            "lead": self.lead,
            "squad": self.squad,
            "variants": self.variants,
            "tips": self.tips,
            "edited": self.edited,
            "author": self.author,
            "user_id": self.user_id,
            "creation_time": self.creation_time
        }


class CounterTip(Tip):

    def __init__(self, squad: str, content: str, activity=None, author="n/a", rating=0, user_id=0, edited=False):
        super().__init__(content=content, author=author, rating=rating, user_id=user_id)
        self.squad = squad
        self.activity: str = activity.upper() if activity else None
        self.edited = edited

    def create_tip_message(self, rating=False):
        edited, rating = self._create_tip_message_info(rating=rating)
        activity = ""
        if self.activity:
            activity = f"\t[{self.activity}] "
        return f"**{self.squad}**\t{activity}\n\t {self.content} {edited}\t*(author: {self.author}*{rating})"

    def to_json(self):
        out_json = super().to_json()
        out_json["squad"] = self.squad
        out_json["activity"] = self.activity
        return out_json


class Alias:

    def __init__(self, alias, squad_lead_id, author, user_id=None):
        self.alias = alias
        self.squad_lead_id = squad_lead_id
        self.author = author
        self.user_id = user_id
        self.creation_time = datetime.datetime.utcnow()

    def to_json(self):
        return {
            "alias": self.alias,
            "squad_lead_id": self.squad_lead_id,
            "author": self.author,
            "user_id": self.user_id,
            "creation_time": self.creation_time
        }
