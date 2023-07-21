import json
import os.path


def check_default_settings():
    ensure_settings_exist()
    with open("data/default_settings.json") as defaults_file:
        true_defaults = json.load(defaults_file)
    with open("data/settings.json") as current_settings_file:
        current_settings = json.load(current_settings_file)
    del defaults_file, current_settings_file

    current_defaults = current_settings["guild_id"]["0"]
    missing_settings = 0
    for key, value in true_defaults.items():
        try:
            current_defaults[key]
        except KeyError:
            current_defaults[key] = value
            missing_settings += 1

    if missing_settings > 0:
        with open("data/settings.json", "w") as current_settings_file:
            json.dump(current_settings, current_settings_file)

        print(f"Generated {missing_settings} missing settings")
        return
    print("Settings loaded successfully")

def ensure_settings_exist():
    if not os.path.exists("data/settings.json"):
        print("Settings did not exist. Creating defualt state.")
        created_settings = {
            "guild_id": {
                "0": {}
            }
        }
        with open("data/settings.json", "w") as settings_file:
            json.dump(created_settings, settings_file)
