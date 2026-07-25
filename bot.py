import logging
import random
import asyncio
from datetime import timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import config
from database import get_members, set_members, save_couple, get_last_couple
from member_fetcher import get_all_members

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

GROUP_ID = config.GROUP_ID

def update_members():
    """به‌روزرسانی لیست اعضا با Telethon"""
    try:
        members = asyncio.run(get_all_members())
        return members
    except Exception as e:
        logger.error(f"❌ خطا در دریافت اعضا: {e}")
        return []

def select_couple(bot, chat_id):
    members = get_members()
    
    if len(members) < 2:
        bot.send_message(
            chat_id=chat_id,
            text="❌ تعداد اعضا کافی نیست (حداقل ۲ نفر)"
        )
        return
    
    user1, user2 = random.sample(members, 2)
    save_couple(user1, user2)
    
    msg = (
        f"💞 **زوج جذاب امروز** 💞\n\n"
        f"به پای هم پیر سیر دیر و عاشق باشید 🫂\n"
        f"پایدار تا پای دار \n"
        f"باهم بمیرید زنده شوید \n"
        f"اگه یکی مرد اونی یکی رو هم زنده زنده خاک کنید 😊🔥🎀\n\n"
        f"👤 {user1['name']}\n"
        f"یوزرنیم: @{user1['username']}\n"
        f"❤️ با ❤️\n"
        f"👤 {user2['name']}\n"
        f"یوزرنیم: @{user2['username']}\n\n"
        f"🎉 تبریک میگم بهتون! 🎉\n"
        f"بچه هاتون از سر کولتون بالا برن یا کوه 😄"
    )
    
    bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode="Markdown"
    )
    
    logger.info(f"✅ زوج انتخاب شد: {user1['name']} و {user2['name']}")

def daily_job(context: CallbackContext):
    chat_id = context.job.context
    bot = context.bot
    
    logger.info("🔄 انتخاب زوج روزانه...")
    update_members()
    select_couple(bot, chat_id)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🤖 **ربات زوج‌یاب**\n\n"
        "دستورات:\n"
        "/start - این پیام\n"
        "/couple - انتخاب زوج\n"
        "/update - به‌روزرسانی لیست\n"
        "/last - آخرین زوج\n"
        "/count - تعداد اعضا",
        parse_mode="Markdown"
    )

def couple_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id != GROUP_ID:
        update.message.reply_text("❌ فقط در گروه کار می‌کند.")
        return
    
    update.message.reply_text("🔄 در حال انتخاب...")
    update_members()
    select_couple(context.bot, chat_id)

def update_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id != GROUP_ID:
        update.message.reply_text("❌ فقط در گروه کار می‌کند.")
        return
    
    update.message.reply_text("🔄 در حال به‌روزرسانی...")
    members = update_members()
    update.message.reply_text(f"✅ {len(members)} عضو پیدا شد.")

def last_command(update: Update, context: CallbackContext):
    last = get_last_couple()
    if last and last.get("user1"):
        u1 = last["user1"]
        u2 = last["user2"]
        msg = f"📅 آخرین زوج:\n\n👤 {u1['name']} (@{u1['username']})\n❤️ با\n👤 {u2['name']} (@{u2['username']})"
        update.message.reply_text(msg)
    else:
        update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")

def count_command(update: Update, context: CallbackContext):
    members = get_members()
    update.message.reply_text(f"👥 تعداد اعضا: {len(members)} نفر")

def main():
    updater = Updater(token=config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("couple", couple_command))
    dp.add_handler(CommandHandler("update", update_command))
    dp.add_handler(CommandHandler("last", last_command))
    dp.add_handler(CommandHandler("count", count_command))
    
    job_queue = updater.job_queue
    if job_queue:
        job_queue.run_repeating(
            daily_job,
            interval=86400,
            first=10,
            context=GROUP_ID
        )
        logger.info("✅ کار روزانه تنظیم شد.")
    
    # به‌روزرسانی اولیه
    logger.info("🔄 در حال دریافت لیست اعضا...")
    update_members()
    
    logger.info("🚀 ربات شروع به کار کرد...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()