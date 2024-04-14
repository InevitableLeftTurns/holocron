import json
from collections import defaultdict

import requests
from bs4 import BeautifulSoup


def run_parser(characters: dict) -> dict:
    season_id = 51
    counter_lead_id = "dr"
    counter_lead = "DARTHREVAN"

    print(f"Len: {len(characters)}")
    print(f"{characters[counter_lead]['id']}:{characters[counter_lead]['name']}")

    site_response = get_site_data(season_id, counter_lead_id, counter_lead)
    counters = parse_counter_response(counter_lead, site_response)
    print_counter_output(counter_lead, counters)
    return counters


def get_site_data(season_id, counter_lead_id, counter_lead):
    url = f"https://swgoh.gg/gac/counters/{counter_lead}/?season={season_id}"

    # response = requests.get(url,
    #                         headers={
    #                             "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
    #                                       "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;,v=b3;q=0.7",
    #                             "accept-language": "en-US,en;q=0.9",
    #                             "cache-control": "max-age=0",
    #                             "referer": "https://swgoh.gg/gac/counters/",
    #                             'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    #                             'sec-ch-ua-platform': "macOS",
    #                             "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    #                                           "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    #                         })

    class Response():
        def __init__(self):
            self.text = ""
            self.status = 200
            with open(f"data/counter/{counter_lead_id}.html", "r") as f:
                line = f.readline()
                while line:
                    self.text += line
                    line = f.readline()

    response = Response()

    if response.status != 200:
        raise IOError(f"URL '{url}' did not return successfully")
    return response


def print_counter_output(counter_lead, counters: dict):
    for grouped_counters in counters.values():
        idx = 0
        for actual_counter in grouped_counters:
            idx += 1
            if idx == 1:
                d_lead = characters[counter_lead]['name']
                print(f"Counters for {d_lead}:"
                      f"{[characters[defender]['name'] for defender in actual_counter.defenders]}\n")
            print(f"{[characters[ac]['name'] for ac in actual_counter.attackers]}\n")


def parse_character_file() -> dict:
    char_map = {}
    with open("data/counter/characters.json", "r") as char_file:
        result = json.load(char_file)
        for char_json_obj in result:
            char_map[char_json_obj["base_id"]] = {"id": char_json_obj["base_id"],
                                                  "name": char_json_obj["name"]}
    return char_map


def parse_counter_response(counter_lead, response) -> dict:
    soup = BeautifulSoup(response.text, "html.parser")

    counter_data = defaultdict(set)

    panels = soup.find_all("div", class_="panel")
    for panel in panels:
        counter_obj = ParsedCounter(counter_lead)
        cols = panel.find_all("div", class_="col-md-4")
        if len(cols) == 3:
            attackers, stats, defense = cols
            for attacker in attackers.find_all("a"):
                counter_obj.add_attacker(attacker.get("href"))
            #     print(f'{attacker.get("href")} ||')
            # print("\n")
            # print(stats)
            # print("defense\n")
            for defender in defense.find_all("a"):
                counter_obj.add_defender(defender.get("href"))
                # print(f'{defender.get("href")} ||')
            # print(counterobj)
            counter_data[counter_obj.defense()].add(counter_obj)

    return counter_data


class ParsedCounter():

    def __init__(self, lead_id):
        self.lead_id = lead_id
        self.lead_attacker = None
        self.attackers = []
        self.defenders = [self.lead_id]
        self.seen = None
        self.wins = None

    def defense(self) -> str:
        return "/".join(self.defenders)

    def __hash__(self):
        return hash(self.lead_id + "|" + self.lead_attacker)

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return False

        if self.lead_id == other.lead_id and \
                self.lead_attacker == other.lead_attacker and \
                set(self.attackers).difference(other.attackers):
            return True

        return False

    def __repr__(self):
        return f"Lead: {self.lead_id}\n" \
               f"Defense: {self.defenders}\n" \
               f"Attack Lead: {self.lead_attacker}\n" \
               f"Attackers: {self.attackers}\n"

    def _add(self, attribute: list, key: str, data: str):
        start = data.find(key) + len(key)
        toon = data[start:]
        attribute.append(toon)

    def _add_attacker_lead(self, data):
        key = "a_lead="
        lead_start = data.find(key) + len(key)
        lead = data[lead_start:]
        self.lead_attacker = lead
        self.attackers.insert(0, lead)

    def add_attacker(self, attacker_data):
        if "a_lead=" in attacker_data:
            self._add_attacker_lead(attacker_data)
        else:
            self._add(self.attackers, "a_unit=", attacker_data)

    def add_defender(self, defender_data):
        self._add(self.defenders, "d_unit=", defender_data)


if __name__ == '__main__':
    characters = parse_character_file()
    run_parser(characters)
