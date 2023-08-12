import re


class HolocronLocation:

    def __init__(self, location_string, labels):
        self.address = location_string
        self.labels = labels
        self.is_group_location = False

    def get_location_name(self):
        # a name for the address for clean user interactions
        raise NotImplementedError

    def get_address_type_name(self):
        # convenience function when interacting with users to provide a friendly name for where the address is
        # e.g. feat, combat mission, counter, etc
        raise NotImplementedError

    def get_tip_title(self):
        # convenience method for retrieving the Tip title for a given address
        raise NotImplementedError

    def get_detail(self):
        # provides a complete detail of the location and its description
        raise NotImplementedError

    def get_map_name(self):
        # used to retrieve the map name from the location address for visual maps
        # not supported by all Holocrons
        raise NotImplementedError

    def parse_location(self, **kwargs):
        # parses the location according to the specific Holocron structure
        raise NotImplementedError

    def has_group_tips(self):
        # used when viewing groups if the group itself has tips
        raise NotImplementedError


class InvalidLocationError(Exception):
    pass


class ConquestLocation(HolocronLocation):

    def __init__(self, location_string, labels):
        super().__init__(location_string, labels)
        # ids are the individual components and used for labels
        # addresses are the lookups for storage lookup

        # global vs sector
        self.feat_location_id = None
        self.feat_location_address = None
        self.is_sector_location = False
        # only used if sector
        self.sector_id = None
        self.sector_address = None
        # feat, node, boss, miniboss
        self.sector_node_type_id = None
        self.sector_node_type_address = None
        self.is_boss_location = False
        # feat # or node #
        self.feat_id = None
        self.feat_address = None

    conquest_labels = {
        "g": "Global Feat",
        "s": "Sector",
        "f": "Feat",
        "m": "Mini Boss",
        "b": "Boss",
        "n": "Node",
    }

    feat_locations = {
        'g': 'globals',
        's': 'sectors',
    }

    boss_types = ['b', 'm']

    tip_types = {
        "b": "boss",
        "m": "mini",
        "n": "nodes",
        "f": "feats"
    }

    def has_group_tips(self):
        return self.is_boss_location and self.is_group_location

    def get_address_type_name(self):
        return self.conquest_labels[self.sector_node_type_id].lower()

    def parse_location(self, is_map=False, is_group=False):
        location_fragments = re.split('(\\d+)', self.address)

        try:
            self.feat_location_id = location_fragments[0]
            self.feat_address = self.feat_locations[self.feat_location_id]
        except IndexError:
            msg_data = [f"* `{feat_location_id}` for `{self.conquest_labels[feat_location_id]}`, "
                        for feat_location_id in self.feat_locations]
            msg = '\n'.join(msg_data)
            raise InvalidLocationError(f"Invalid or missing location. Queries to tips must start with:\n{msg}")

        if self.feat_location_id == 'g':
            self.is_sector_location = True
            try:
                self.feat_id = location_fragments[1]
                self.feat_address = int(self.feat_id)
            except IndexError:  # called if location_fragments[1] dne
                self.is_group_location = True
            except ValueError:  # called if feat_id not an int
                raise InvalidLocationError("The character following `g` must be a number.")

            if self.address not in self.labels:
                raise InvalidLocationError("The number following `g` must be a valid feat #.")

            return

        if self.feat_location_id == 's':
            try:
                self.sector_id = location_fragments[1]
                self.sector_address = int(self.sector_id)
            except IndexError:  # called if location_fragments[1] dne
                raise InvalidLocationError("The character following `s` for sectors must be a number indicating which "
                                           "sector to query.")
            except ValueError:  # called if sector_id not an int
                raise InvalidLocationError("The character following `s` must be a number.")

            if f"s{self.sector_id}f1" not in self.labels:
                # not the best test but trying to avoid having to access tip_storage
                raise InvalidLocationError("The number following `s` must be a valid Sector #.")

            try:
                self.sector_node_type_id = location_fragments[2]
                self.sector_node_type_address = self.tip_types[self.sector_node_type_id]
            except (IndexError, KeyError):
                raise InvalidLocationError(f"The character following `{self.sector_id}` must be `b` for boss tips,"
                                           f"`m` for miniboss tips, `n` for node tips, or `f` for sector feats.")

            self.is_boss_location = self.sector_node_type_id in self.boss_types
            try:
                self.feat_id = location_fragments[3]
                self.feat_address = int(location_fragments[3])
            except IndexError:  # location[3] dne, do standard tips
                self.is_group_location = True
                return
            except ValueError:  # called if location[3] not an int
                raise InvalidLocationError(f"The character following `{self.sector_node_type_id}` "
                                           f"must be a number indicating which feat to query.")

            if not self.is_group_location and self.address not in self.labels:
                raise InvalidLocationError(f"The number following `{self.sector_node_type_id}` "
                                           f"must be a valid feat #")

            return


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

    def get_group_address(self):
        raise NotImplementedError

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
            msg_data = [f"* `{track_id}` for `{self.labels[track_id]['name']}`, "
                        for track_id in self.tracks]
            msg = '\n'.join(msg_data)
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
            msg_data = [f"* `{mission_id}` for `{mission_label}`, "
                        for mission_id, mission_label in self.mission_labels.items()]
            msg = '\n'.join(msg_data)
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
