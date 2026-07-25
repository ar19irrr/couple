import json
import os
from datetime import datetime

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"members": [], "last_couple": None}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_members():
    return load_data().get("members", [])

def set_members(members_list):
    data = load_data()
    data["members"] = members_list
    save_data(data)

def save_couple(user1, user2):
    data = load_data()
    data["last_couple"] = {
        "user1": user1,
        "user2": user2,
        "date": datetime.now().isoformat()
    }
    save_data(data)

def get_last_couple():
    return load_data().get("last_couple")