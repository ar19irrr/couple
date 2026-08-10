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
                    return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "weekly_scores": {}, "global_blocked": []}
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
                if "weekly_scores" not in data:
                    data["weekly_scores"] = {}
                if "global_blocked" not in data:
                    data["global_blocked"] = []
                return data
        except:
            return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "weekly_scores": {}, "global_blocked": []}
    return {"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "weekly_scores": {}, "global_blocked": []}

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
    for chat_id in data.get("weekly_scores", {}).keys():
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

# ==================== امتیازات هفتگی ====================
def get_weekly_score(chat_id, user_id):
    """دریافت امتیاز هفتگی یک کاربر"""
    data = load_data()
    weekly = data.get("weekly_scores", {}).get(str(chat_id), {})
    return weekly.get(str(user_id), 0)

def update_weekly_score(chat_id, user_id, points=1):
    """افزایش امتیاز هفتگی کاربر"""
    data = load_data()
    chat_id_str = str(chat_id)
    user_id_str = str(user_id)
    
    if "weekly_scores" not in data:
        data["weekly_scores"] = {}
    if chat_id_str not in data["weekly_scores"]:
        data["weekly_scores"][chat_id_str] = {}
    
    data["weekly_scores"][chat_id_str][user_id_str] = \
        data["weekly_scores"][chat_id_str].get(user_id_str, 0) + points
    save_data(data)

def reset_weekly_scores(chat_id):
    """ریست کردن امتیازات هفتگی"""
    data = load_data()
    chat_id_str = str(chat_id)
    if "weekly_scores" in data and chat_id_str in data["weekly_scores"]:
        data["weekly_scores"][chat_id_str] = {}
        save_data(data)

def get_all_weekly_scores(chat_id):
    """دریافت همه امتیازات هفتگی یک گروه"""
    data = load_data()
    return data.get("weekly_scores", {}).get(str(chat_id), {})

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


# ==================== بلاک جهانی ====================
def get_global_blocked_users():
    """دریافت لیست کاربران بلاک شده در سراسر ربات"""
    data = load_data()
    return data.get("global_blocked", [])

def add_global_blocked_user(user_id):
    """افزودن کاربر به لیست بلاک جهانی"""
    data = load_data()
    if "global_blocked" not in data:
        data["global_blocked"] = []
    if user_id not in data["global_blocked"]:
        data["global_blocked"].append(user_id)
        save_data(data)
        return True
    return False

def remove_global_blocked_user(user_id):
    """حذف کاربر از لیست بلاک جهانی"""
    data = load_data()
    if "global_blocked" in data and user_id in data["global_blocked"]:
        data["global_blocked"].remove(user_id)
        save_data(data)
        return True
    return False

def is_user_globally_blocked(user_id):
    """بررسی بلاک بودن یک کاربر"""
    blocked = get_global_blocked_users()
    return user_id in blocked

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

# ==================== سیستم دستاورد ====================

ACHIEVEMENTS = {
    # --- سری اول (۱ تا ۱۵) ---
    "first_love": {"name": "تازه‌وارد", "emoji": "🌱", "description": "اولین بار لاور شدی"},
    "beginner": {"name": "عاشق مبتدی", "emoji": "💘", "description": "۵ بار لاور شدی"},
    "pro": {"name": "لاور حرفه‌ای", "emoji": "🔥", "description": "۱۵ بار لاور شدی"},
    "legend": {"name": "افسانه عشق", "emoji": "🏆", "description": "۵۰ بار لاور شدی"},
    "king": {"name": "پادشاه/ملکه عشق", "emoji": "👑", "description": "۱۰۰ بار لاور شدی"},
    "loyal": {"name": "وفادار", "emoji": "💍", "description": "۳ بار با یک نفر خاص لاور شدی"},
    "super_loyal": {"name": "خیلی وفادار", "emoji": "💖", "description": "۷ بار با یک نفر خاص لاور شدی"},
    "diverse": {"name": "تنوع‌طلب", "emoji": "🌈", "description": "با ۱۰ نفر مختلف لاور شدی"},
    "super_diverse": {"name": "پادشاه تنوع", "emoji": "🌟", "description": "با ۲۵ نفر مختلف لاور شدی"},
    "weekly_winner": {"name": "زوج طلایی", "emoji": "🥇", "description": "برنده لاورهای هفته شدی"},
    "monthly_hero": {"name": "قهرمان ماه", "emoji": "🏅", "description": "۳ بار برنده هفته شدی"},
    "consistent": {"name": "ستاره گروه", "emoji": "⭐", "description": "۱۰ بار جزو ۱۰ نفر برتر هفته بودی"},
    "pioneer": {"name": "اولین جرقه", "emoji": "✨", "description": "اولین لاور گروه بودی"},
    "night_owl": {"name": "شب‌زنده‌دار", "emoji": "🌙", "description": "بین ۱۲ تا ۵ صبح لاور شدی"},
    "lucky": {"name": "خوش‌شانس", "emoji": "🍀", "description": "۳ بار پشت‌سرهم لاور شدی"},

    # --- سری دوم و سوم (۱۶ تا ۵۰) ---
    "early_bird": {"name": "سحرخیز", "emoji": "🌅", "description": "بین ۵ تا ۸ صبح لاور شدی"},
    "weekend_lover": {"name": "عاشق آخر هفته", "emoji": "🎉", "description": "در جمعه یا شنبه لاور شدی"},
    "comeback": {"name": "بازگشت قهرمان", "emoji": "🔄", "description": "بعد از ۱۴ روز غیبت دوباره لاور شدی"},
    "popular": {"name": "محبوب گروه", "emoji": "😍", "description": "با ۱۵ نفر مختلف لاور شدی"},
    "legend_plus": {"name": "افسانه زنده", "emoji": "🏛️", "description": "۲۰۰ بار لاور شدی"},
    "perfect_match": {"name": "مچ کامل", "emoji": "🎯", "description": "با کسی که علاقه‌اش یکی بود لاور شدی"},
    "opposite_attract": {"name": "تضاد جذاب", "emoji": "💑", "description": "با جنسیت مخالف لاور شدی"},
    "serial_lover": {"name": "لاور سریالی", "emoji": "⚡", "description": "۵ بار در یک روز لاور شدی"},
    "ghost": {"name": "روح", "emoji": "👻", "description": "۱۰ بار فقط از طریق انتخاب خودکار لاور شدی"},
    "announcer": {"name": "اعلام‌کننده", "emoji": "📢", "description": "اولین نفری بودی که /couple زدی"},
    "collector": {"name": "جمع‌کننده مدال", "emoji": "🏅", "description": "۱۰ دستاورد گرفتی"},
    "master_collector": {"name": "استاد مدال‌ها", "emoji": "🥇", "description": "۲۰ دستاورد گرفتی"},
    "unstoppable": {"name": "توقف‌ناپذیر", "emoji": "🔥", "description": "۷ روز پشت‌سرهم لاور شدی"},
    "social_butterfly": {"name": "پروانه اجتماعی", "emoji": "🦋", "description": "با ۳۰ نفر مختلف لاور شدی"},
    "immortal": {"name": "جاودانه", "emoji": "♾️", "description": "۵۰۰ بار لاور شدی"},
    "first_blood": {"name": "اولین خون", "emoji": "🩸", "description": "اولین لاور روز بودی"},
    "last_dance": {"name": "آخرین رقص", "emoji": "🕺", "description": "آخرین لاور روز بودی"},
    "twin_flame": {"name": "شعله دوقلو", "emoji": "🔥🔥", "description": "۲ بار پشت‌سرهم با یک نفر لاور شدی"},
    "forbidden": {"name": "عشق ممنوعه", "emoji": "😈", "description": "با کسی که بیشتر از ۵ بار باهاش لاور شدی دوباره لاور شدی"},
    "underdog": {"name": "اسب سیاه", "emoji": "🐴", "description": "با کمتر از ۳ لاور برنده هفته شدی"},
    "veteran": {"name": "کهنه‌کار", "emoji": "🎖️", "description": "۳۰ روز عضویت + حداقل ۱۰ لاور"},
    "silent_lover": {"name": "عاشق ساکت", "emoji": "🤫", "description": "۱۰ بار بدون زدن دستور لاور شدی"},
    "command_king": {"name": "پادشاه دستورات", "emoji": "👑", "description": "۵۰ بار دستور /couple زدی"},
    "fortune_teller": {"name": "فال‌بین", "emoji": "🔮", "description": "۲۰ بار فال گرفتی"},
    "curious": {"name": "کنجکاو", "emoji": "🧠", "description": "۳۰ بار از هوش مصنوعی سوال پرسیدی"},
    "profile_master": {"name": "استاد پروفایل", "emoji": "📝", "description": "هم جنسیت و هم علاقه را تنظیم کردی"},
    "night_king": {"name": "پادشاه شب", "emoji": "👑🌙", "description": "۱۰ بار بین ۱۲ تا ۵ صبح لاور شدی"},
    "morning_person": {"name": "آدم صبح", "emoji": "☀️", "description": "۱۰ بار بین ۵ تا ۹ صبح لاور شدی"},
    "streak_3": {"name": "رگبار ۳ تایی", "emoji": "🔥", "description": "۳ روز پشت‌سرهم لاور شدی"},
    "streak_7": {"name": "رگبار هفتگی", "emoji": "💥", "description": "۷ روز پشت‌سرهم لاور شدی"},
    "streak_15": {"name": "رگبار افسانه‌ای", "emoji": "🚀", "description": "۱۵ روز پشت‌سرهم لاور شدی"},
    "matchmaker": {"name": "واسطه‌گر", "emoji": "💘", "description": "با دستور تو دیگران لاور شدند"},
    "unlucky": {"name": "بدشانس", "emoji": "😢", "description": "۲۰ بار لاور شدی ولی برنده هفته نشدی"},
    "comeback_king": {"name": "پادشاه بازگشت", "emoji": "👑🔄", "description": "بعد از ۳۰ روز غیبت برنده هفته شدی"},
    "god_of_love": {"name": "خدای عشق", "emoji": "🕊️", "description": "۱۰۰۰ بار لاور شدی"},
}

def get_user_achievements(chat_id, user_id):
    data = load_data()
    achievements = data.get("achievements", {}).get(str(chat_id), {}).get(str(user_id), [])
    return achievements if isinstance(achievements, list) else []

def unlock_achievement(chat_id, user_id, achievement_id):
    """اگر دستاورد جدید باشه، آنلاک می‌کنه و True برمی‌گردونه"""
    data = load_data()
    chat_id_str = str(chat_id)
    user_id_str = str(user_id)

    if "achievements" not in data:
        data["achievements"] = {}
    if chat_id_str not in data["achievements"]:
        data["achievements"][chat_id_str] = {}
    if user_id_str not in data["achievements"][chat_id_str]:
        data["achievements"][chat_id_str][user_id_str] = []

    current = data["achievements"][chat_id_str][user_id_str]
    
    if achievement_id in current:
        return False  # قبلاً داشته

    current.append(achievement_id)
    data["achievements"][chat_id_str][user_id_str] = current
    save_data(data)
    return True

def get_all_achievements_info():
    return ACHIEVEMENTS

# ==================== آمار پیشرفته برای دستاوردها ====================

def get_user_extra_stats(chat_id, user_id):
    """دریافت آمار اضافی کاربر برای دستاوردها"""
    data = load_data()
    chat_id_str = str(chat_id)
    user_id_str = str(user_id)
    
    default = {
        "last_couple_date": None,          # آخرین تاریخ لاور شدن
        "current_streak": 0,               # رگبار فعلی
        "max_streak": 0,                   # بیشترین رگبار
        "daily_count": {},                 # تعداد لاور در هر روز (کلید: YYYY-MM-DD)
        "auto_count": 0,                   # تعداد لاور از طریق Job خودکار
        "manual_count": 0,                 # تعداد لاور از طریق دستور
        "couple_commands": 0,              # تعداد دفعات زدن /couple
        "fall_commands": 0,                # تعداد دفعات زدن /fall
        "ask_commands": 0,                 # تعداد دفعات زدن /ask
        "weekly_wins": 0,                  # تعداد برد هفته
        "top10_count": 0,                  # تعداد دفعات حضور در ۱۰ نفر برتر
        "first_activity": None,            # اولین فعالیت در گروه
        "night_count": 0,                  # تعداد لاور شبانه (۰-۵)
        "morning_count": 0,                # تعداد لاور صبح (۵-۹)
        "last_partners": [],               # آخرین چند شریک (برای twin_flame و ...)
    }
    
    stats = data.get("user_extra_stats", {}).get(chat_id_str, {}).get(user_id_str, {})
    
    # پر کردن مقادیر پیش‌فرض اگر وجود نداشت
    for key, value in default.items():
        if key not in stats:
            stats[key] = value
            
    return stats

def update_user_extra_stats(chat_id, user_id, **kwargs):
    """به‌روزرسانی آمار اضافی کاربر"""
    data = load_data()
    chat_id_str = str(chat_id)
    user_id_str = str(user_id)
    
    if "user_extra_stats" not in data:
        data["user_extra_stats"] = {}
    if chat_id_str not in data["user_extra_stats"]:
        data["user_extra_stats"][chat_id_str] = {}
    if user_id_str not in data["user_extra_stats"][chat_id_str]:
        data["user_extra_stats"][chat_id_str][user_id_str] = get_user_extra_stats(chat_id, user_id)
    
    stats = data["user_extra_stats"][chat_id_str][user_id_str]
    stats.update(kwargs)
    data["user_extra_stats"][chat_id_str][user_id_str] = stats
    save_data(data)

def increment_command_count(chat_id, user_id, command_type):
    """افزایش شمارنده دستورات (couple / fall / ask)"""
    stats = get_user_extra_stats(chat_id, user_id)
    
    if command_type == "couple":
        stats["couple_commands"] = stats.get("couple_commands", 0) + 1
    elif command_type == "fall":
        stats["fall_commands"] = stats.get("fall_commands", 0) + 1
    elif command_type == "ask":
        stats["ask_commands"] = stats.get("ask_commands", 0) + 1
        
    update_user_extra_stats(chat_id, user_id, **stats)

def record_couple_for_achievements(chat_id, user_id, partner_id, is_auto=False):
    """ثبت اطلاعات لاور شدن برای محاسبه دستاوردها"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    stats = get_user_extra_stats(chat_id, user_id)
    
    # تاریخ اولین فعالیت
    if not stats.get("first_activity"):
        stats["first_activity"] = now.isoformat()
    
    # شمارش روزانه
    daily = stats.get("daily_count", {})
    daily[today_str] = daily.get(today_str, 0) + 1
    stats["daily_count"] = daily
    
    # خودکار یا دستی
    if is_auto:
        stats["auto_count"] = stats.get("auto_count", 0) + 1
    else:
        stats["manual_count"] = stats.get("manual_count", 0) + 1
    
    # شب یا صبح
    hour = now.hour
    if 0 <= hour < 5:
        stats["night_count"] = stats.get("night_count", 0) + 1
    elif 5 <= hour < 9:
        stats["morning_count"] = stats.get("morning_count", 0) + 1
    
    # رگبار (Streak)
    last_date_str = stats.get("last_couple_date")
    if last_date_str:
        try:
            last_date = datetime.fromisoformat(last_date_str).date()
            today = now.date()
            diff = (today - last_date).days
            
            if diff == 1:
                stats["current_streak"] = stats.get("current_streak", 0) + 1
            elif diff == 0:
                pass  # همان روز
            else:
                stats["current_streak"] = 1
        except:
            stats["current_streak"] = 1
    else:
        stats["current_streak"] = 1
    
    # به‌روزرسانی max streak
    if stats["current_streak"] > stats.get("max_streak", 0):
        stats["max_streak"] = stats["current_streak"]
    
    # آخرین تاریخ
    stats["last_couple_date"] = now.isoformat()
    
    # آخرین شرکا (برای twin_flame و forbidden)
    last_partners = stats.get("last_partners", [])
    last_partners.insert(0, partner_id)
    stats["last_partners"] = last_partners[:10]  # فقط ۱۰ تای آخر
    
    update_user_extra_stats(chat_id, user_id, **stats)

def clear_data():
    save_data({"members": {}, "last_couple": {}, "history": {}, "blocked": {}, "groups": [], "profiles": {}, "weekly_scores": {}, "global_blocked": []})
    print("✅ دیتابیس پاک شد")
