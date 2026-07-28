def stats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    stats = get_stats(chat_id)
    top_users = get_top_users(chat_id, top_n=3)  # ۳ نفر برتر
    
    msg = f"📊 **آمار گروه:**\n\n"
    msg += f"👥 تعداد اعضا: {stats['total_members']} نفر\n"
    msg += f"💞 تعداد زوج‌ها: {stats['total_couples']} بار\n"
    msg += f"🌟 کاربران منحصر‌به‌فرد: {stats['unique_users']} نفر\n"
    
    if stats['last_couple'] and isinstance(stats['last_couple'], dict):
        u1 = stats['last_couple'].get('user1', {})
        u2 = stats['last_couple'].get('user2', {})
        msg += f"\n💖 آخرین زوج:\n👤 {u1.get('name', 'نامشخص')} ❤️ {u2.get('name', 'نامشخص')}"
    
    # ====== اضافه کردن پرتکرارترین کاربران ======
    if top_users:
        msg += f"\n\n🏆 **پرتکرارترین کاربران:**\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, user in enumerate(top_users):
            if i < len(medals):
                medal = medals[i]
            else:
                medal = f"{i+1}."
            msg += f"{medal} {user['name']} (@{user['username']}) — {user['count']} بار\n"
    else:
        msg += f"\n\n📭 هنوز آمار کافی برای نمایش وجود ندارد."
    
    update.message.reply_text(msg, parse_mode="Markdown")
