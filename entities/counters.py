import datetime
import uuid

from entities.tip import Tip


class Squad:

    def __init__(self, lead_id: str, lead: str, squad: str, author="n/a", user_id=0, variants=None):
        self.uid = uuid.uuid4()
        self.lead_id = lead_id.lower()
        self.lead = lead.title()
        self.squad = squad
        self.variants = variants or []
        self.author = author
        self.user_id = user_id
        self.edited = False
        self.creation_time = datetime.datetime.utcnow()

    def update_squad(self, new_squad: str):
        self.squad = new_squad
        self.edited = True

    def add_variant(self, variant: str):
        self.variants.append(variant)
        self.variants = sorted(self.variants)

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
            "uuid": self.uid,
            "lead_id": self.lead_id,
            "lead": self.lead,
            "squad": self.squad,
            "variants": self.variants,
            "edited": self.edited,
            "author": self.author,
            "userid": self.user_id,
            "creation_time": self.creation_time
        }


class CounterTip(Tip):

    def __init__(self, squad_uuid, content: str, activity=None, author="n/a", rating=0, user_id=0):
        super().__init__(content=content, author=author, rating=rating, user_id=user_id)
        self.squad_uuid = squad_uuid
        self.activity: str = activity.upper() if activity else None

    def create_tip_message(self, rating=False):
        edited, rating = self._create_tip_message_info(rating=rating)
        activity = ""
        if self.activity:
            activity = f"\t[{self.activity}] "
        return f"{self.content} {activity} {edited} \t*(author: {self.author}*{rating})"

    def to_json(self):
        base = super().to_json()
        base["squad_uuid"] = self.squad_uuid
        base["activity"] = self.activity


class Alias:

    def __init__(self, alias, squad_lead_id):
        self.alias = alias
        self.squad_lead_id = squad_lead_id

    def to_json(self):
        return {
            "alias": self.alias,
            "squad_lead_id": self.squad_lead_id,
        }
