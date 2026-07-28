def get_top_users(chat_id, top_n=3):
    """دریافت پرتکرارترین کاربران در زوج‌ها"""
    data = load_data()
    history = data.get("history", {}).get(str(chat_id), [])
    
    if not history:
        return []
    
    # شمارش تعداد حضور هر کاربر
    user_count = {}
    for couple in history:
        if isinstance(couple, dict):
            # کاربر اول
            u1 = couple.get("user1")
            if u1 and isinstance(u1, dict):
                user_id = u1.get("id")
                if user_id:
                    user_count[user_id] = user_count.get(user_id, 0) + 1
            
            # کاربر دوم
            u2 = couple.get("user2")
            if u2 and isinstance(u2, dict):
                user_id = u2.get("id")
                if user_id:
                    user_count[user_id] = user_count.get(user_id, 0) + 1
    
    # دریافت اطلاعات کامل کاربران
    members = get_members(chat_id)
    user_map = {m["id"]: m for m in members}
    
    # تبدیل به لیست و مرتب‌سازی
    top_users = []
    for user_id, count in user_count.items():
        user_info = user_map.get(user_id, {"name": f"کاربر ناشناس {user_id}", "username": "ندارد"})
        top_users.append({
            "id": user_id,
            "name": user_info.get("name", "بدون نام"),
            "username": user_info.get("username", "ندارد"),
            "count": count
        })
    
    # مرتب‌سازی بر اساس تعداد (بیشترین اول)
    top_users.sort(key=lambda x: x["count"], reverse=True)
    
    return top_users[:top_n]
