import re


class HolocronLocation:

    def __init__(self, location_string, labels):
        self.address = location_string
        self.labels = labels

    def get_location_name(self):
        raise NotImplementedError

    def get_tip_title(self):
        raise NotImplementedError

    def get_detail(self):
        raise NotImplementedError

    def get_map_name(self):
        raise NotImplementedError

    def parse_location(self, **kwargs):
        raise NotImplementedError

    def is_group_location(self):
        return False



class InvalidLocationError(Exception):
    pass


class ConquestLocation(HolocronLocation):
    pass


class RiseLocation(HolocronLocation):
    def __init__(self, location_string, labels):
        super().__init__(location_string, labels)
        # ids are the individual components and used for labels
        # addresses are the lookups for storage lookup
        self.track_id = None
        self.track_address = None
        self.planet_id = None
        self.planet_address = None
        self.mission_type_id = None
        self.mission_type_address = None
        self.mission_id = None
        self.mission_address = None
        self.is_group = False

    mission_labels = {
        "cm": "Combat Mission",
        "sm": "Special Mission",
        "f": "Fleet Mission",
    }

    tracks = {
        "ds": "darkside",
        "mx": "mixed",
        "ls": "lightside",
        "lsb": "lightsidebonus"
    }

    missions = {
        "cm": "cm",
        "f": "fleet",
        "sm": "sm"
    }

    def is_group_location(self):
        return False

    def get_map_name(self):
        return self.labels[self.track_id][self.planet_address]['name'].lower()

    def get_location_name(self):
        return f"{self.labels[self.track_id]['name']} - " \
               f"{self.labels[self.track_id][self.planet_id]['name']} " \
               f"{self.mission_labels[self.mission_type_id]} {self.mission_id} " \
               f"(`{self.address}`)"

    def get_tip_title(self):
        return f"{self.mission_labels[self.mission_type_id]} {self.mission_id}"

    def get_detail(self):
        planet_data = self.labels[self.track_id][self.planet_id]
        label_data = planet_data[self.address]

        planet_name = planet_data['name']
        reqs = label_data['reqs']
        waves = label_data['enemies']
        if isinstance(waves, list):
            waves = [f"Wave {idx + 1}: {wave}" for idx, wave in enumerate(waves)]
            waves = '\n'.join(waves)

        return f"{planet_name}\nRequirements: {reqs}\n{waves}"

    def parse_location(self, is_map=False, is_group=False):
        # parses the location address and raises errors if the address is invalid
        location_fragments = re.split('(\\d+)', self.address)
        self.track_id = location_fragments[0]

        try:
            self.track_address = self.tracks[self.track_id]
        except (IndexError, KeyError):
            msg = [f"* `{track_id}` for `{self.labels['ds']['name']}`, "
                   for track_id in self.tracks]
            raise InvalidLocationError(f"Invalid or missing location. Queries to tips must start with:\n{msg}")

        try:
            planet_num = location_fragments[1]
            self.planet_id = self.track_address + planet_num
            self.planet_address = int(self.planet_id)
        except (IndexError, ValueError, TypeError):
            raise InvalidLocationError("The character following your side must be a number identifying "
                                       "which planet to query.")

        if self.planet_id not in self.labels[self.track_id]:
            raise InvalidLocationError("The number following track must be between 1 and 3 (inclusive). "
                                       "All planets 4, 5, and 6 in all tracks are currently unsupported.")

        # map does not check the mission data
        if is_map:
            return

        try:
            self.mission_type_id = location_fragments[2]
            self.mission_type_address = self.missions[self.mission_type_id]
        except (IndexError, KeyError, TypeError):
            msg = [f"* `{mission_id}` for `{mission_label}`, "
                   for mission_id, mission_label in self.mission_labels.items()]
            raise InvalidLocationError(f"Characters following planet number must be:\n{msg}")

        self.mission_id = ''
        try:
            if not is_group and self.mission_type_id in ['cm', 'sm']:
                self.mission_id = location_fragments[3]
                self.mission_address = int(self.mission_id)
        except (IndexError, ValueError, TypeError):
            raise InvalidLocationError("Combat missions require numbers indicating which mission to query. Combat "
                                       "missions are numbered from left to right. Use `map` for a visual reference.")

        if self.address not in self.labels[self.track_id][self.planet_id]:
            raise InvalidLocationError("The number following your mission type match a valid battles number. "
                                       "Battles are numbered left to right. Use `map` for a visual reference.")

        return
