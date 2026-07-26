import logging
import random
import threading
import asyncio
import os
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import config
from database import (
    get_members, set_members, save_couple, get_last_couple,
    get_couple_history, get_blocked_users, clear_blocked_users,
    get_stats, clear_data, get_groups, add_group
)
from member_fetcher import get_all_members

# ==================== Flask ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات زوج‌یاب فعال است! 🚀"

@app.route('/ping')
def ping():
    return "", 204

def run_flask():
    port = 10000
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== تنظیمات ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== پیام‌ها ====================
COUPLE_MESSAGES = [
    "💞 زوج جذاب امروز 💞",
    "🔥 عشق امروز 🔥",
    "💖 این دو تا عاشق شدن 💖",
    "🎯 قرعه‌کشی امروز 🎯",
    "💘 زوج منتخب امروز 💘"
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

# ==================== تابع دریافت اعضا با Telethon ====================
def update_members_sync(chat_id):
    """به‌روزرسانی لیست اعضا با Telethon"""
    try:
        logger.info(f"🔄 شروع دریافت اعضا برای گروه {chat_id}")
        
        # بررسی فایل نشست
        session_file = os.path.join(os.path.dirname(__file__), 'session.session')
        if not os.path.exists(session_file):
            logger.error(f"❌ فایل نشست در مسیر {session_file} پیدا نشد!")
            return []
        
        # اجرای Telethon
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        members = loop.run_until_complete(get_all_members(chat_id))
        loop.close()
        
        if members and isinstance(members, list) and len(members) > 0:
            set_members(chat_id, members)
            logger.info(f"✅ {len(members)} عضو برای گروه {chat_id} ذخیره شد")
            return members
        else:
            logger.warning(f"⚠️ هیچ عضوی برای گروه {chat_id} پیدا نشد")
            return []
            
    except Exception as e:
        logger.error(f"❌ خطا در دریافت اعضا برای گروه {chat_id}: {e}")
        return []

# ==================== دستورات ====================
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        """🤖 ربات زوج‌یاب حرفه‌ای

📌 دستورات:
/start - این پیام
/addgroup - فعال کردن ربات در این گروه
/couple - انتخاب زوج
/count - تعداد اعضا
/last - آخرین زوج
/history - تاریخچه زوج‌ها
/stats - آمار گروه
/reset - ریست دیتابیس

⚠️ نکته: ربات باید ادمین باشد و VPN روشن باشد."""
    )

def addgroup_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    logger.info(f"📌 تلاش برای افزودن گروه: {chat_id}")
    
    if add_group(chat_id):
        update.message.reply_text(f"✅ این گروه به لیست گروه‌های فعال اضافه شد. در حال دریافت اعضا...")
        
        members = update_members_sync(chat_id)
        if members and len(members) > 0:
            update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
        else:
            update.message.reply_text(
                "❌ خطا در دریافت اعضا.\n"
                "لطفاً موارد زیر را بررسی کنید:\n"
                "1️⃣ VPN روشن است\n"
                "2️⃣ ربات ادمین گروه است\n"
                "3️⃣ فایل session.session در گیت‌هاب وجود دارد"
            )
    else:
        chat_id_str = str(chat_id)
        update.message.reply_text(f"ℹ️ این گروه قبلاً به لیست اضافه شده است. (ID: {chat_id_str})")

def couple_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🔄 در حال انتخاب زوج...")
    
    members = get_members(chat_id)
    if not members or len(members) == 0:
        update.message.reply_text("❌ لیست اعضا خالی است. ابتدا دستور /addgroup و سپس /update را بزنید.")
        return
    
    blocked = get_blocked_users(chat_id)
    available_members = [m for m in members if m["id"] not in blocked]
    
    if len(available_members) < 2:
        update.message.reply_text(
            "❌ تعداد اعضای قابل انتخاب کافی نیست (حداقل ۲ نفر).\n"
            f"🔹 کل اعضا: {len(members)}\n"
            f"🔹 در لیست سیاه: {len(blocked)}"
        )
        return
    
    user1, user2 = random.sample(available_members, 2)
    save_couple(chat_id, user1, user2)
    
    msg = f"""{random.choice(COUPLE_MESSAGES)}

به پای هم پیر سیر دیر و عاشق باشید 🫂
پایدار تا پای دار 
باهم بمیرید زنده شوید 
{random.choice(JOKE_MESSAGES)}

👤 {user1['name']}
یوزرنیم: @{user1['username']}
❤️ با ❤️
👤 {user2['name']}
یوزرنیم: @{user2['username']}

{random.choice(CELEBRATION_MESSAGES)}"""
    
    update.message.reply_text(msg)
    clear_blocked_users(chat_id)
    
    logger.info(f"✅ زوج انتخاب شد برای گروه {chat_id}")

def update_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🔄 در حال به‌روزرسانی لیست همه اعضا... (چند لحظه)")
    
    members = update_members_sync(chat_id)
    if members and len(members) > 0:
        update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
    else:
        update.message.reply_text(
            "❌ خطا در دریافت اعضا.\n"
            "لطفاً موارد زیر را بررسی کنید:\n"
            "1️⃣ VPN روشن است\n"
            "2️⃣ ربات ادمین گروه است\n"
            "3️⃣ فایل session.session در گیت‌هاب وجود دارد"
        )

def last_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    last = get_last_couple(chat_id)
    
    if last and isinstance(last, dict) and last.get("user1"):
        u1 = last["user1"]
        u2 = last["user2"]
        date = last.get("date", "")[:10]
        update.message.reply_text(
            f"""📅 آخرین زوج ({date})

👤 {u1['name']}
یوزرنیم: @{u1['username']}
❤️ با ❤️
👤 {u2['name']}
یوزرنیم: @{u2['username']}"""
        )
    else:
        update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")

def count_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    members = get_members(chat_id)
    blocked = get_blocked_users(chat_id)
    
    update.message.reply_text(
        f"""👥 آمار اعضا:

🔹 کل اعضا: {len(members)} نفر
🔹 اعضای قابل انتخاب: {len(members) - len(blocked)} نفر
🔹 در لیست سیاه: {len(blocked)} نفر (۷ روزه)"""
    )

def history_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    history = get_couple_history(chat_id, 10)
    
    if not history:
        update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")
        return
    
    msg = "📜 تاریخچه ۱۰ زوج آخر:\n\n"
    for i, couple in enumerate(reversed(history), 1):
        if isinstance(couple, dict) and "user1" in couple and "user2" in couple:
            u1 = couple["user1"]
            u2 = couple["user2"]
            date = couple.get("date", "")[:10]
            msg += f"{i}. {u1['name']} ❤️ {u2['name']} ({date})\n"
    
    update.message.reply_text(msg)

def stats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    stats = get_stats(chat_id)
    
    msg = f"""📊 آمار گروه:

👥 تعداد اعضا: {stats['total_members']} نفر
💞 تعداد زوج‌ها: {stats['total_couples']} بار
🌟 کاربران منحصر‌به‌فرد: {stats['unique_users']} نفر"""
    
    if stats['last_couple'] and isinstance(stats['last_couple'], dict):
        u1 = stats['last_couple'].get('user1', {})
        u2 = stats['last_couple'].get('user2', {})
        msg += f"\n\n💖 آخرین زوج:\n👤 {u1.get('name', 'نامشخص')} ❤️ {u2.get('name', 'نامشخص')}"
    
    update.message.reply_text(msg)

def reset_command(update: Update, context: CallbackContext):
    clear_data()
    update.message.reply_text("✅ دیتابیس با موفقیت ریست شد. حالا می‌توانید دوباره /addgroup بزنید.")

# ==================== کار روزانه ====================
def daily_job(context: CallbackContext):
    chat_id = context.job.context
    bot = context.bot
    
    logger.info(f"🔄 انتخاب زوج روزانه برای گروه {chat_id}...")
    
    members = update_members_sync(chat_id)
    if not members or len(members) == 0:
        logger.error(f"❌ خطا در دریافت اعضا برای گروه {chat_id}")
        bot.send_message(
            chat_id=chat_id,
            text="❌ خطا در دریافت لیست اعضا. لطفاً دستور /update را بزنید."
        )
        return
    
    blocked = get_blocked_users(chat_id)
    available_members = [m for m in members if m["id"] not in blocked]
    
    if len(available_members) < 2:
        bot.send_message(
            chat_id=chat_id,
            text=f"❌ تعداد اعضای قابل انتخاب کافی نیست. (کل: {len(members)}, لیست سیاه: {len(blocked)})"
        )
        return
    
    user1, user2 = random.sample(available_members, 2)
    save_couple(chat_id, user1, user2)
    
    msg = f"""{random.choice(COUPLE_MESSAGES)}

به پای هم پیر سیر دیر و عاشق باشید 🫂
پایدار تا پای دار 
باهم بمیرید زنده شوید 
{random.choice(JOKE_MESSAGES)}

👤 {user1['name']}
یوزرنیم: @{user1['username']}
❤️ با ❤️
👤 {user2['name']}
یوزرنیم: @{user2['username']}

{random.choice(CELEBRATION_MESSAGES)}"""
    
    bot.send_message(chat_id=chat_id, text=msg)
    clear_blocked_users(chat_id)
    
    logger.info(f"✅ زوج روزانه انتخاب شد برای گروه {chat_id}")

# ==================== زمان‌بندی برای همه گروه‌ها ====================
def schedule_daily_jobs(dispatcher):
    job_queue = dispatcher.job_queue
    if not job_queue:
        logger.warning("⚠️ JobQueue در دسترس نیست!")
        return
    
    groups = get_groups()
    if not groups:
        logger.info("ℹ️ هیچ گروه فعالی برای زمان‌بندی یافت نشد.")
        return
    
    for chat_id in groups:
        job_queue.run_repeating(
            daily_job,
            interval=86400,
            first=10,
            context=chat_id
        )
        logger.info(f"✅ کار روزانه برای گروه {chat_id} تنظیم شد.")

# ==================== اجرا ====================
def main():
    # اجرای Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 وب‌سرور Flask روی پورت ۱۰۰۰۰ شروع به کار کرد...")
    
    # اجرای ربات
    updater = Updater(token=config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addgroup", addgroup_command))
    dp.add_handler(CommandHandler("couple", couple_command))
    dp.add_handler(CommandHandler("update", update_command))
    dp.add_handler(CommandHandler("last", last_command))
    dp.add_handler(CommandHandler("count", count_command))
    dp.add_handler(CommandHandler("history", history_command))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("reset", reset_command))
    
    schedule_daily_jobs(dp)
    
    logger.info("🚀 ربات شروع به کار کرد...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
