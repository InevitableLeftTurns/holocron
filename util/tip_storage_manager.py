import pickle
import os.path


filepath = "data/tip_storage.pckl"
def load_tip_storage():
    ensure_settings_exist()

    with open(filepath, "rb") as tip_storage_file:
        tip_storage = pickle.load(tip_storage_file)

    return tip_storage

def ensure_settings_exist():
    if not os.path.exists(filepath):
        print("Tip storage did not exist. Creating empty storage.")
        tip_storage = {
            "sectors": {},
            "globals": {}
        }

        for i in range(5):
            tip_storage["sectors"][i + 1] = {}
            tip_storage["sectors"][i + 1]["boss"] = {"feats": {1: [], 2: []}, "tips": []}
            tip_storage["sectors"][i + 1]["mini"] = {"feats": {1: [], 2: []}, "tips": []}
            tip_storage["sectors"][i + 1]["nodes"] = {}
            tip_storage["sectors"][i + 1]["feats"] = {}
            for j in range(4):
                tip_storage["sectors"][i + 1]["feats"][j + 1] = []

        for i in range(8):
            tip_storage["globals"][i + 1] = []

        with open(filepath, "wb") as tip_storage_file:
            pickle.dump(tip_storage, tip_storage_file)

def save_storage_to_file(data):
    with open(filepath, "wb") as tip_storage_file:
        pickle.dump(data, tip_storage_file)
