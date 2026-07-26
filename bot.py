import logging
import random
import threading
import asyncio
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import config
from database import (
    get_members, set_members, save_couple, get_last_couple,
    get_couple_history, get_blocked_users, clear_blocked_users,
    get_stats, clear_data, get_groups, add_group
)

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

# ==================== تابع دریافت اعضا (برای نسخه ۲۰.۸) ====================
async def get_members_from_group(bot, chat_id):
    """دریافت همه اعضای گروه با استفاده از get_chat_members (نسخه ۲۰.۸)"""
    try:
        logger.info(f"🔄 در حال دریافت اعضای گروه {chat_id}...")
        members = []
        
        # دریافت اعضا با استفاده از get_chat_members (نسخه ۲۰.۸)
        try:
            offset = 0
            limit = 200
            while True:
                chat_members = await bot.get_chat_members(
                    chat_id=chat_id,
                    offset=offset,
                    limit=limit
                )
                
                if not chat_members:
                    break
                    
                for member in chat_members:
                    user = member.user
                    if not user.is_bot:
                        members.append({
                            "id": user.id,
                            "name": user.full_name or "بدون نام",
                            "username": user.username or "ندارد"
                        })
                
                offset += limit
                if len(chat_members) < limit:
                    break
                    
                logger.info(f"📊 تاکنون {len(members)} عضو دریافت شد...")
                
        except Exception as e:
            logger.error(f"❌ خطا در دریافت اعضا: {e}")
            return []
        
        logger.info(f"✅ {len(members)} عضو پیدا شد")
        return members
        
    except Exception as e:
        logger.error(f"❌ خطای کلی در دریافت اعضا: {e}")
        return []

async def update_members(bot, chat_id):
    """به‌روزرسانی لیست اعضا و ذخیره در دیتابیس"""
    members = await get_members_from_group(bot, chat_id)
    if members:
        set_members(chat_id, members)
        logger.info(f"✅ {len(members)} عضو در دیتابیس ذخیره شد")
    return members

# ==================== دستورات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """🤖 ربات زوج‌یاب حرفه‌ای

📌 دستورات:
/start - این پیام
/addgroup - فعال کردن ربات در این گروه
/couple - انتخاب زوج
/count - تعداد اعضا
/last - آخرین زوج
/history - تاریخچه زوج‌ها
/stats - آمار گروه

⚠️ نکته: ربات باید ادمین باشد."""
    )

async def addgroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if add_group(chat_id):
        await update.message.reply_text("✅ این گروه به لیست گروه‌های فعال اضافه شد.")
        members = await update_members(context.bot, chat_id)
        if members:
            await update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
        else:
            await update.message.reply_text("❌ خطا در دریافت اعضا. مطمئن شو که ربات ادمین است.")
    else:
        await update.message.reply_text("ℹ️ این گروه قبلاً اضافه شده است.")

async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("🔄 در حال انتخاب زوج...")
    
    members = get_members(chat_id)
    if not members:
        await update.message.reply_text("❌ لیست اعضا خالی است. ابتدا دستور /update را بزنید.")
        return
    
    blocked = get_blocked_users(chat_id)
    available_members = [m for m in members if m["id"] not in blocked]
    
    if len(available_members) < 2:
        await update.message.reply_text(
            "❌ تعداد اعضای قابل انتخاب کافی نیست (حداقل ۲ نفر)."
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
    
    await update.message.reply_text(msg)
    clear_blocked_users(chat_id)
    
    logger.info(f"✅ زوج انتخاب شد برای گروه {chat_id}")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("🔄 در حال به‌روزرسانی لیست همه اعضا... (چند لحظه)")
    
    members = await update_members(context.bot, chat_id)
    if members and len(members) > 0:
        await update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
    else:
        await update.message.reply_text("❌ خطا در دریافت اعضا. مطمئن شو که ربات ادمین است.")

async def last_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    last = get_last_couple(chat_id)
    
    if last and isinstance(last, dict) and last.get("user1"):
        u1 = last["user1"]
        u2 = last["user2"]
        date = last.get("date", "")[:10]
        await update.message.reply_text(
            f"""📅 آخرین زوج ({date})

👤 {u1['name']}
یوزرنیم: @{u1['username']}
❤️ با ❤️
👤 {u2['name']}
یوزرنیم: @{u2['username']}"""
        )
    else:
        await update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    members = get_members(chat_id)
    blocked = get_blocked_users(chat_id)
    
    await update.message.reply_text(
        f"""👥 آمار اعضا:

🔹 کل اعضا: {len(members)} نفر
🔹 اعضای قابل انتخاب: {len(members) - len(blocked)} نفر
🔹 در لیست سیاه: {len(blocked)} نفر (۷ روزه)"""
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    history = get_couple_history(chat_id, 10)
    
    if not history:
        await update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")
        return
    
    msg = "📜 تاریخچه ۱۰ زوج آخر:\n\n"
    for i, couple in enumerate(reversed(history), 1):
        if isinstance(couple, dict) and "user1" in couple and "user2" in couple:
            u1 = couple["user1"]
            u2 = couple["user2"]
            date = couple.get("date", "")[:10]
            msg += f"{i}. {u1['name']} ❤️ {u2['name']} ({date})\n"
    
    await update.message.reply_text(msg)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    await update.message.reply_text(msg)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_data()
    await update.message.reply_text("✅ دیتابیس با موفقیت ریست شد.")

# ==================== کار روزانه ====================
async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    bot = context.bot
    
    logger.info(f"🔄 انتخاب زوج روزانه برای گروه {chat_id}...")
    
    members = await update_members(bot, chat_id)
    if not members:
        logger.error(f"❌ خطا در دریافت اعضا برای گروه {chat_id}")
        return
    
    blocked = get_blocked_users(chat_id)
    available_members = [m for m in members if m["id"] not in blocked]
    
    if len(available_members) < 2:
        await bot.send_message(
            chat_id=chat_id,
            text="❌ تعداد اعضای قابل انتخاب کافی نیست."
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
    
    await bot.send_message(chat_id=chat_id, text=msg)
    clear_blocked_users(chat_id)
    
    logger.info(f"✅ زوج روزانه انتخاب شد برای گروه {chat_id}")

# ==================== زمان‌بندی برای همه گروه‌ها ====================
def schedule_daily_jobs(application):
    job_queue = application.job_queue
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
            interval=86400,  # ۲۴ ساعت
            first=10,
            chat_id=chat_id
        )
        logger.info(f"✅ کار روزانه برای گروه {chat_id} تنظیم شد.")

# ==================== اجرا ====================
async def main():
    # اجرای Flask در یک ترد جداگانه
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 وب‌سرور Flask روی پورت ۱۰۰۰۰ شروع به کار کرد...")
    
    # اجرای ربات با نسخه ۲۰.۸
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addgroup", addgroup_command))
    application.add_handler(CommandHandler("couple", couple_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("last", last_command))
    application.add_handler(CommandHandler("count", count_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    schedule_daily_jobs(application)
    
    logger.info("🚀 ربات شروع به کار کرد...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
