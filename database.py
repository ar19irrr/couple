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
                    return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "monthly_scores": {}}
                if "members" not in data:
                    data["members"] = {}
                if "last_couple" not in data:
                    data["last_couple"] = {}
                if "history" not in data:
                    data["history"] = {}
                if "blocked" not in data:
                    data["blocked"] = {}
                if "groups" not in data:
                    data["groups"] = []
                if "profiles" not in data:
                    data["profiles"] = {}
                if "monthly_scores" not in data:
                    data["monthly_scores"] = {}
                return data
        except:
            return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "monthly_scores": {}}
    return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "monthly_scores": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره دیتابیس: {e}")

# ==================== گروه‌ها ====================
def get_groups():
    data = load_data()
    return data.get("groups", [])

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

def get_all_chats_from_members():
    """دریافت لیست همه گروه‌هایی که در دیتابیس وجود دارند"""
    data = load_data()
    chats = set()
    
    for chat_id in data.get("members", {}).keys():
        chats.add(int(chat_id))
    for chat_id in data.get("last_couple", {}).keys():
        chats.add(int(chat_id))
    for chat_id in data.get("history", {}).keys():
        chats.add(int(chat_id))
    for chat_id in data.get("blocked", {}).keys():
        chats.add(int(chat_id))
    for chat_id in data.get("monthly_scores", {}).keys():
        chats.add(int(chat_id))
    for chat_id in data.get("profiles", {}).keys():
        chats.add(int(chat_id))
    
    return list(chats)

def sync_groups():
    """همگام‌سازی لیست گروه‌ها با دیتابیس (اضافه کردن گروه‌های موجود)"""
    data = load_data()
    existing_groups = set(data.get("groups", []))
    
    all_chats = get_all_chats_from_members()
    
    new_groups = 0
    for chat_id in all_chats:
        if chat_id not in existing_groups:
            existing_groups.add(chat_id)
            new_groups += 1
    
    if new_groups > 0:
        data["groups"] = list(existing_groups)
        save_data(data)
        print(f"✅ {new_groups} گروه جدید به لیست گروه‌های فعال اضافه شد.")
    
    return list(existing_groups)

# ==================== اعضا ====================
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

# ==================== پروفایل کاربران ====================
def get_user_profile(chat_id, user_id):
    data = load_data()
    profiles = data.get("profiles", {}).get(str(chat_id), {})
    return profiles.get(str(user_id), {})

def set_user_profile(chat_id, user_id, profile_data):
    data = load_data()
    chat_id_str = str(chat_id)
    if "profiles" not in data:
        data["profiles"] = {}
    if chat_id_str not in data["profiles"]:
        data["profiles"][chat_id_str] = {}
    data["profiles"][chat_id_str][str(user_id)] = profile_data
    save_data(data)

def set_user_gender(chat_id, user_id, gender):
    profile = get_user_profile(chat_id, user_id)
    profile["gender"] = gender
    set_user_profile(chat_id, user_id, profile)

def set_user_interest(chat_id, user_id, interest):
    profile = get_user_profile(chat_id, user_id)
    profile["interest"] = interest
    set_user_profile(chat_id, user_id, profile)

# ==================== امتیازات ماهانه ====================
def get_monthly_score(chat_id, user_id):
    data = load_data()
    monthly = data.get("monthly_scores", {}).get(str(chat_id), {})
    return monthly.get(str(user_id), 0)

def update_monthly_score(chat_id, user_id, points=1):
    data = load_data()
    chat_id_str = str(chat_id)
    user_id_str = str(user_id)
    
    if "monthly_scores" not in data:
        data["monthly_scores"] = {}
    if chat_id_str not in data["monthly_scores"]:
        data["monthly_scores"][chat_id_str] = {}
    
    data["monthly_scores"][chat_id_str][user_id_str] = \
        data["monthly_scores"][chat_id_str].get(user_id_str, 0) + points
    save_data(data)

def reset_monthly_scores(chat_id):
    data = load_data()
    chat_id_str = str(chat_id)
    if "monthly_scores" in data and chat_id_str in data["monthly_scores"]:
        data["monthly_scores"][chat_id_str] = {}
        save_data(data)

def get_all_monthly_scores(chat_id):
    data = load_data()
    return data.get("monthly_scores", {}).get(str(chat_id), {})

# ==================== زوج‌ها ====================
def save_couple(chat_id, user1, user2):
    data = load_data()
    chat_id_str = str(chat_id)
    
    data["last_couple"][chat_id_str] = {
        "user1": user1,
        "user2": user2,
        "date": datetime.now().isoformat()
    }
    
    if "history" not in data:
        data["history"] = {}
    if chat_id_str not in data["history"]:
        data["history"][chat_id_str] = []
    
    data["history"][chat_id_str].append({
        "user1": user1,
        "user2": user2,
        "date": datetime.now().isoformat()
    })
    if len(data["history"][chat_id_str]) > 50:
        data["history"][chat_id_str] = data["history"][chat_id_str][-50:]
    
    if "blocked" not in data:
        data["blocked"] = {}
    if chat_id_str not in data["blocked"]:
        data["blocked"][chat_id_str] = []
    
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

# ==================== لیست سیاه ====================
def get_blocked_users(chat_id):
    data = load_data()
    blocked = data.get("blocked", {}).get(str(chat_id), [])
    if not isinstance(blocked, list):
        return []
    
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

def check_and_reset_blocked(chat_id):
    members = get_members(chat_id)
    blocked = get_blocked_users(chat_id)
    
    available = [m for m in members if m["id"] not in blocked]
    
    if len(available) < 2 and len(members) >= 2:
        data = load_data()
        chat_id_str = str(chat_id)
        if chat_id_str in data.get("blocked", {}):
            data["blocked"][chat_id_str] = []
            save_data(data)
            logger.info(f"✅ لیست سیاه برای گروه {chat_id} به دلیل اتمام اعضا ریست شد.")
            return True
    return False

# ==================== آمار ====================
def get_stats(chat_id):
    data = load_data()
    chat_id_str = str(chat_id)
    members = get_members(chat_id)
    history = data.get("history", {}).get(chat_id_str, [])
    
    total_couples = len(history) if isinstance(history, list) else 0
    
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

# ==================== پرتکرارترین کاربران ====================
def get_top_users(chat_id, top_n=3):
    data = load_data()
    history = data.get("history", {}).get(str(chat_id), [])
    
    if not history:
        return []
    
    user_count = {}
    for couple in history:
        if isinstance(couple, dict):
            u1 = couple.get("user1")
            if u1 and isinstance(u1, dict):
                user_id = u1.get("id")
                if user_id:
                    user_count[user_id] = user_count.get(user_id, 0) + 1
            u2 = couple.get("user2")
            if u2 and isinstance(u2, dict):
                user_id = u2.get("id")
                if user_id:
                    user_count[user_id] = user_count.get(user_id, 0) + 1
    
    members = get_members(chat_id)
    user_map = {m["id"]: m for m in members}
    
    top_users = []
    for user_id, count in user_count.items():
        user_info = user_map.get(user_id, {"name": f"کاربر ناشناس {user_id}", "username": "ندارد"})
        top_users.append({
            "id": user_id,
            "name": user_info.get("name", "بدون نام"),
            "username": user_info.get("username", "ندارد"),
            "count": count
        })
    
    top_users.sort(key=lambda x: x["count"], reverse=True)
    return top_users[:top_n]

# ==================== آمار شخصی کاربر ====================
def get_user_couple_stats(chat_id, user_id):
    data = load_data()
    history = data.get("history", {}).get(str(chat_id), [])
    
    if not history:
        return []
    
    couple_count = {}
    for couple in history:
        if not isinstance(couple, dict):
            continue
            
        u1 = couple.get("user1")
        u2 = couple.get("user2")
        
        if u1 and isinstance(u1, dict) and u1.get("id") == user_id:
            partner = u2
            if partner and isinstance(partner, dict):
                partner_id = partner.get("id")
                if partner_id:
                    couple_count[partner_id] = couple_count.get(partner_id, 0) + 1
                    
        elif u2 and isinstance(u2, dict) and u2.get("id") == user_id:
            partner = u1
            if partner and isinstance(partner, dict):
                partner_id = partner.get("id")
                if partner_id:
                    couple_count[partner_id] = couple_count.get(partner_id, 0) + 1
    
    members = get_members(chat_id)
    user_map = {m["id"]: m for m in members}
    
    result = []
    for partner_id, count in couple_count.items():
        partner_info = user_map.get(partner_id, {"name": f"کاربر ناشناس", "username": "ندارد"})
        result.append({
            "id": partner_id,
            "name": partner_info.get("name", "بدون نام"),
            "username": partner_info.get("username", "ندارد"),
            "count": count
        })
    
    result.sort(key=lambda x: x["count"], reverse=True)
    return result

def get_user_total_couples(chat_id, user_id):
    data = load_data()
    history = data.get("history", {}).get(str(chat_id), [])
    
    total = 0
    for couple in history:
        if not isinstance(couple, dict):
            continue
        u1 = couple.get("user1")
        u2 = couple.get("user2")
        if (u1 and isinstance(u1, dict) and u1.get("id") == user_id) or \
           (u2 and isinstance(u2, dict) and u2.get("id") == user_id):
            total += 1
    
    return total

def clear_data():
    save_data({"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "monthly_scores": {}})
    print("✅ دیتابیس پاک شد")
