import json
import os
from datetime import datetime

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"members": {}, "last_couple": {}, "groups": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_groups():
    return load_data().get("groups", [])

def add_group(chat_id):
    data = load_data()
    if chat_id not in data["groups"]:
        data["groups"].append(chat_id)
        save_data(data)
        return True
    return False

def remove_group(chat_id):
    data = load_data()
    if chat_id in data["groups"]:
        data["groups"].remove(chat_id)
        save_data(data)
        return True
    return False

def get_members(chat_id):
    data = load_data()
    return data.get("members", {}).get(str(chat_id), [])

def set_members(chat_id, members_list):
    data = load_data()
    data["members"][str(chat_id)] = members_list
    save_data(data)

def save_couple(chat_id, user1, user2):
    data = load_data()
    data["last_couple"][str(chat_id)] = {
        "user1": user1,
        "user2": user2,
        "date": datetime.now().isoformat()
    }
    save_data(data)

def get_last_couple(chat_id):
    data = load_data()
    return data.get("last_couple", {}).get(str(chat_id))
