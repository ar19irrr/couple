import logging
import random
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import config
from database import (
    get_members, set_members, save_couple, get_last_couple,
    get_couple_history, get_blocked_users, clear_blocked_users,
    get_stats, clear_data
)
from member_fetcher import get_all_members

# ==================== راه‌اندازی Flask ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات زوج‌یاب فعال است! 🚀"

def run_flask():
    """اجرای وب‌سرور Flask در پورت ۱۰۰۰۰"""
    port = 10000
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== تنظیمات لاگ ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== پیام‌های متنوع ====================
COUPLE_MESSAGES = [
    "💞 **زوج جذاب امروز** 💞",
    "🔥 **عشق امروز** 🔥",
    "💖 **این دو تا عاشق شدن** 💖",
    "🎯 **قرعه‌کشی امروز** 🎯",
    "💘 **زوج منتخب امروز** 💘"
]

CELEBRATION_MESSAGES = [
    "🎉 به این دو عزیز تبریک میگم! 🎉",
    "😍 آفرین به این دو! 😍",
    "🥳 قدماشون پر از برکت! 🥳",
    "💐 تبریک به این دو قشنگ! 💐",
    "🎊 این دو تا بهترینن! 🎊"
]

JOKE_MESSAGES = [
    "بچه هاتون از سر کولتون بالا برن یا کوه 😄",
    "اگه یکی مرد اونی یکی رو هم زنده زنده خاک کنید 😊🔥🎀",
    "پایدار تا پای دار، باهم بمیرید زنده شوید 🫂",
    "به پای هم پیر سیر دیر و عاشق باشید 🫂",
    "دنیا رو به هم ببافید و عاشق باشید 🌍❤️"
]

# ==================== توابع کمکی ====================
def is_admin(update, context):
    """بررسی ادمین بودن کاربر (شامل مالک گروه) - نسخه ساده شده"""
    try:
        # دریافت اطلاعات کاربر
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # دریافت وضعیت کاربر از تلگرام
        bot = context.bot
        member = bot.get_chat_member(chat_id, user_id)
        
        # اگه کاربر مالک (creator) یا ادمین (administrator) باشه
        if member.status in ['creator', 'administrator']:
            return True
        return False
        
    except Exception as e:
        # در صورت بروز خطا، لاگ می‌کنیم و False برمی‌گردونیم
        logger.error(f"خطا در بررسی ادمین: {e}")
        return False

def update_members_sync(chat_id):
    """به‌روزرسانی لیست اعضا"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        members = loop.run_until_complete(get_all_members(chat_id))
        loop.close()
        
        if members and isinstance(members, list):
            set_members(chat_id, members)
            return members
        return []
    except Exception as e:
        logger.error(f"❌ خطا در دریافت اعضا: {e}")
        return []

# ==================== دستورات اصلی ====================
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🤖 **ربات زوج‌یاب حرفه‌ای**\n\n"
        "📌 **دستورات عمومی:**\n"
        "/start - این پیام\n"
        "/couple - انتخاب زوج (فقط ادمین‌ها)\n"
        "/count - تعداد اعضا\n"
        "/last - آخرین زوج\n"
        "/history - تاریخچه زوج‌ها\n"
        "/stats - آمار گروه\n\n"
        "⚠️ نکته: ربات باید ادمین باشد.",
        parse_mode="Markdown"
    )

def couple_command(update: Update, context: CallbackContext):
    """انتخاب زوج (فقط ادمین‌ها)"""
    chat_id = update.effective_chat.id
    
    if not is_admin(update, context):
        update.message.reply_text("⛔ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند.")
        return
    
    update.message.reply_text("🔄 در حال انتخاب زوج...")
    
    members = update_members_sync(chat_id)
    if not members:
        update.message.reply_text("❌ خطا در دریافت اعضا. مطمئن شو که ربات ادمین است.")
        return
    
    blocked = get_blocked_users(chat_id)
    available_members = [m for m in members if m["id"] not in blocked]
    
    if len(available_members) < 2:
        update.message.reply_text(
            "❌ تعداد اعضای قابل انتخاب کافی نیست (حداقل ۲ نفر).\n"
            "⏳ ممکن است اعضا در لیست سیاه ۷ روزه باشند."
        )
        return
    
    user1, user2 = random.sample(available_members, 2)
    save_couple(chat_id, user1, user2)
    
    msg = random.choice(COUPLE_MESSAGES) + "\n\n"
    msg += f"به پای هم پیر سیر دیر و عاشق باشید 🫂\n"
    msg += f"پایدار تا پای دار \n"
    msg += f"باهم بمیرید زنده شوید \n"
    msg += f"{random.choice(JOKE_MESSAGES)}\n\n"
    msg += f"👤 {user1['name']}\n"
    msg += f"یوزرنیم: @{user1['username']}\n"
    msg += f"❤️ با ❤️\n"
    msg += f"👤 {user2['name']}\n"
    msg += f"یوزرنیم: @{user2['username']}\n\n"
    msg += random.choice(CELEBRATION_MESSAGES)
    
    update.message.reply_text(msg, parse_mode="Markdown")
    clear_blocked_users(chat_id)
    
    logger.info(f"✅ زوج انتخاب شد برای گروه {chat_id}: {user1['name']} و {user2['name']}")

def update_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    if not is_admin(update, context):
        update.message.reply_text("⛔ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند.")
        return
    
    update.message.reply_text("🔄 در حال به‌روزرسانی لیست همه اعضا... (چند ثانیه)")
    
    members = update_members_sync(chat_id)
    if members and len(members) > 0:
        update.message.reply_text(f"✅ {len(members)} عضو پیدا شد.")
    else:
        update.message.reply_text("❌ خطا در دریافت اعضا. مطمئن شو که ربات ادمین است.")

def last_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    last = get_last_couple(chat_id)
    
    if last and isinstance(last, dict) and last.get("user1"):
        u1 = last["user1"]
        u2 = last["user2"]
        date = last.get("date", "")
        date_str = date[:10] if date else "نامشخص"
        
        msg = f"📅 **آخرین زوج ({date_str})**\n\n"
        msg += f"👤 {u1['name']} (@{u1['username']})\n"
        msg += f"❤️ با ❤️\n"
        msg += f"👤 {u2['name']} (@{u2['username']})"
        
        update.message.reply_text(msg, parse_mode="Markdown")
    else:
        update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")

def count_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    members = get_members(chat_id)
    blocked = get_blocked_users(chat_id)
    
    msg = f"👥 **آمار اعضا:**\n\n"
    msg += f"🔹 کل اعضا: {len(members)} نفر\n"
    msg += f"🔹 اعضای قابل انتخاب: {len(members) - len(blocked)} نفر\n"
    msg += f"🔹 در لیست سیاه: {len(blocked)} نفر (۷ روزه)"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def history_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    history = get_couple_history(chat_id, 10)
    
    if not history:
        update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")
        return
    
    msg = "📜 **تاریخچه ۱۰ زوج آخر:**\n\n"
    for i, couple in enumerate(reversed(history), 1):
        if isinstance(couple, dict) and "user1" in couple and "user2" in couple:
            u1 = couple["user1"]
            u2 = couple["user2"]
            date = couple.get("date", "")
            date_str = date[:10] if date else ""
            msg += f"{i}. {u1['name']} ❤️ {u2['name']} ({date_str})\n"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def stats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    stats = get_stats(chat_id)
    
    msg = f"📊 **آمار گروه:**\n\n"
    msg += f"👥 تعداد اعضا: {stats['total_members']} نفر\n"
    msg += f"💞 تعداد زوج‌ها: {stats['total_couples']} بار\n"
    msg += f"🌟 کاربران منحصر‌به‌فرد: {stats['unique_users']} نفر\n"
    
    if stats['last_couple'] and isinstance(stats['last_couple'], dict):
        u1 = stats['last_couple'].get('user1', {})
        u2 = stats['last_couple'].get('user2', {})
        msg += f"\n💖 آخرین زوج:\n"
        msg += f"👤 {u1.get('name', 'نامشخص')} ❤️ {u2.get('name', 'نامشخص')}"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def reset_command(update: Update, context: CallbackContext):
    if not is_admin(update, context):
        update.message.reply_text("⛔ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند.")
        return
    
    clear_data()
    update.message.reply_text("✅ دیتابیس با موفقیت ریست شد.")

def daily_job(context: CallbackContext):
    chat_id = context.job.context
    bot = context.bot
    
    logger.info(f"🔄 انتخاب زوج روزانه برای گروه {chat_id}...")
    
    members = update_members_sync(chat_id)
    if not members:
        logger.error(f"❌ خطا در دریافت اعضا برای گروه {chat_id}")
        return
    
    blocked = get_blocked_users(chat_id)
    available_members = [m for m in members if m["id"] not in blocked]
    
    if len(available_members) < 2:
        bot.send_message(
            chat_id=chat_id,
            text="❌ تعداد اعضای قابل انتخاب کافی نیست."
        )
        return
    
    user1, user2 = random.sample(available_members, 2)
    save_couple(chat_id, user1, user2)
    
    msg = random.choice(COUPLE_MESSAGES) + "\n\n"
    msg += f"به پای هم پیر سیر دیر و عاشق باشید 🫂\n"
    msg += f"پایدار تا پای دار \n"
    msg += f"باهم بمیرید زنده شوید \n"
    msg += f"{random.choice(JOKE_MESSAGES)}\n\n"
    msg += f"👤 {user1['name']}\n"
    msg += f"یوزرنیم: @{user1['username']}\n"
    msg += f"❤️ با ❤️\n"
    msg += f"👤 {user2['name']}\n"
    msg += f"یوزرنیم: @{user2['username']}\n\n"
    msg += random.choice(CELEBRATION_MESSAGES)
    
    bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    clear_blocked_users(chat_id)
    
    logger.info(f"✅ زوج روزانه انتخاب شد برای گروه {chat_id}")

# ==================== اجرای اصلی ====================
def main():
    # 1. اجرای وب‌سرور Flask در یک ترد جداگانه
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # با بسته شدن برنامه، ترد هم بسته میشه
    flask_thread.start()
    logger.info("🌐 وب‌سرور Flask روی پورت ۱۰۰۰۰ شروع به کار کرد...")
    
    # 2. اجرای ربات تلگرام
    updater = Updater(token=config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("couple", couple_command))
    dp.add_handler(CommandHandler("update", update_command))
    dp.add_handler(CommandHandler("last", last_command))
    dp.add_handler(CommandHandler("count", count_command))
    dp.add_handler(CommandHandler("history", history_command))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("reset", reset_command))
    
    job_queue = updater.job_queue
    if job_queue:
        # برای فعال کردن انتخاب خودکار روزانه، این بخش رو فعال کن
        # job_queue.run_repeating(
        #     daily_job,
        #     interval=86400,
        #     first=10,
        #     context=config.GROUP_ID  # اگر GROUP_ID داری
        # )
        pass
    
    logger.info("🚀 ربات شروع به کار کرد...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
