import json
import os
from datetime import datetime, timedelta

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}}
                if "members" not in data:
                    data["members"] = {}
                if "last_couple" not in data:
                    data["last_couple"] = {}
                if "history" not in data:
                    data["history"] = {}
                if "blocked" not in data:
                    data["blocked"] = {}
                return data
        except:
            return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}}
    return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره دیتابیس: {e}")

def get_members(chat_id):
    data = load_data()
    members = data.get("members", {}).get(str(chat_id), [])
    if not isinstance(members, list):
        return []
    return members

def set_members(chat_id, members_list):
    data = load_data()
    if not isinstance(members_list, list):
        members_list = []
    data["members"][str(chat_id)] = members_list
    save_data(data)

def save_couple(chat_id, user1, user2):
    data = load_data()
    chat_id_str = str(chat_id)
    
    # ذخیره زوج فعلی
    data["last_couple"][chat_id_str] = {
        "user1": user1,
        "user2": user2,
        "date": datetime.now().isoformat()
    }
    
    # ذخیره در تاریخچه
    if "history" not in data:
        data["history"] = {}
    if chat_id_str not in data["history"]:
        data["history"][chat_id_str] = []
    
    # اضافه کردن به تاریخچه (حداکثر ۵۰ تا)
    data["history"][chat_id_str].append({
        "user1": user1,
        "user2": user2,
        "date": datetime.now().isoformat()
    })
    if len(data["history"][chat_id_str]) > 50:
        data["history"][chat_id_str] = data["history"][chat_id_str][-50:]
    
    # اضافه کردن به لیست سیاه (برای جلوگیری از تکرار به مدت ۷ روز)
    if "blocked" not in data:
        data["blocked"] = {}
    if chat_id_str not in data["blocked"]:
        data["blocked"][chat_id_str] = []
    
    # اضافه کردن هر دو کاربر به لیست سیاه
    blocked_until = (datetime.now() + timedelta(days=7)).isoformat()
    data["blocked"][chat_id_str].append({
        "user_id": user1["id"],
        "blocked_until": blocked_until
    })
    data["blocked"][chat_id_str].append({
        "user_id": user2["id"],
        "blocked_until": blocked_until
    })
    
    save_data(data)

def get_last_couple(chat_id):
    data = load_data()
    last = data.get("last_couple", {}).get(str(chat_id))
    if last and isinstance(last, dict):
        return last
    return None

def get_couple_history(chat_id, limit=10):
    data = load_data()
    history = data.get("history", {}).get(str(chat_id), [])
    if isinstance(history, list):
        return history[-limit:] if history else []
    return []

def get_blocked_users(chat_id):
    data = load_data()
    blocked = data.get("blocked", {}).get(str(chat_id), [])
    if not isinstance(blocked, list):
        return []
    
    # پاک کردن کاربرانی که زمانشون گذشته
    now = datetime.now()
    active_blocked = []
    for item in blocked:
        if isinstance(item, dict) and "blocked_until" in item:
            try:
                blocked_until = datetime.fromisoformat(item["blocked_until"])
                if blocked_until > now:
                    active_blocked.append(item["user_id"])
            except:
                continue
    return active_blocked

def clear_blocked_users(chat_id):
    """پاک کردن لیست سیاه بعد از ۷ روز"""
    data = load_data()
    chat_id_str = str(chat_id)
    if chat_id_str in data.get("blocked", {}):
        now = datetime.now()
        new_blocked = []
        for item in data["blocked"][chat_id_str]:
            if isinstance(item, dict) and "blocked_until" in item:
                try:
                    blocked_until = datetime.fromisoformat(item["blocked_until"])
                    if blocked_until > now:
                        new_blocked.append(item)
                except:
                    continue
        data["blocked"][chat_id_str] = new_blocked
        save_data(data)

def get_stats(chat_id):
    """دریافت آمار گروه"""
    data = load_data()
    chat_id_str = str(chat_id)
    members = get_members(chat_id)
    history = data.get("history", {}).get(chat_id_str, [])
    
    # محاسبه تعداد کل انتخاب‌ها
    total_couples = len(history) if isinstance(history, list) else 0
    
    # محاسبه تعداد کاربران منحصر به فرد
    unique_users = set()
    if isinstance(history, list):
        for couple in history:
            if isinstance(couple, dict):
                if "user1" in couple:
                    unique_users.add(couple["user1"].get("id"))
                if "user2" in couple:
                    unique_users.add(couple["user2"].get("id"))
    
    return {
        "total_members": len(members),
        "total_couples": total_couples,
        "unique_users": len(unique_users) - 1 if unique_users else 0,
        "last_couple": get_last_couple(chat_id)
    }

def clear_data():
    save_data({"members": {}, "last_couple": {}, "history": {}, "blocked": {}})
    print("✅ دیتابیس پاک شد")
