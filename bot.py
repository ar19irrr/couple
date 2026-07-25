import logging
import random
import asyncio
from datetime import timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import config
from database import get_members, set_members, save_couple, get_last_couple
from member_fetcher import get_all_members

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

GROUP_ID = config.GROUP_ID

async def update_members():
    """به‌روزرسانی لیست اعضا با Telethon (اصلاح شده)"""
    try:
        members = await get_all_members()
        return members
    except Exception as e:
        logger.error(f"❌ خطا در دریافت اعضا: {e}")
        return []

async def select_couple(application, chat_id):
    members = get_members()
    
    if len(members) < 2:
        await application.bot.send_message(
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
    
    await application.bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode="Markdown"
    )
    
    logger.info(f"✅ زوج انتخاب شد: {user1['name']} و {user2['name']}")

async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    application = context.application
    
    logger.info("🔄 انتخاب زوج روزانه...")
    await update_members()
    await select_couple(application, chat_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **ربات زوج‌یاب**\n\n"
        "دستورات:\n"
        "/start - این پیام\n"
        "/couple - انتخاب زوج\n"
        "/update - به‌روزرسانی لیست\n"
        "/last - آخرین زوج\n"
        "/count - تعداد اعضا",
        parse_mode="Markdown"
    )

async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != GROUP_ID:
        await update.message.reply_text("❌ فقط در گروه کار می‌کند.")
        return
    
    await update.message.reply_text("🔄 در حال انتخاب...")
    await update_members()
    await select_couple(context.application, chat_id)

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != GROUP_ID:
        await update.message.reply_text("❌ فقط در گروه کار می‌کند.")
        return
    
    await update.message.reply_text("🔄 در حال به‌روزرسانی...")
    members = await update_members()
    await update.message.reply_text(f"✅ {len(members)} عضو پیدا شد.")

async def last_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = get_last_couple()
    if last and last.get("user1"):
        u1 = last["user1"]
        u2 = last["user2"]
        msg = f"📅 آخرین زوج:\n\n👤 {u1['name']} (@{u1['username']})\n❤️ با\n👤 {u2['name']} (@{u2['username']})"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    members = get_members()
    await update.message.reply_text(f"👥 تعداد اعضا: {len(members)} نفر")

def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("couple", couple_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("last", last_command))
    application.add_handler(CommandHandler("count", count_command))
    
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(
            daily_job,
            interval=86400,
            first=10,
            chat_id=GROUP_ID
        )
        logger.info("✅ کار روزانه تنظیم شد.")
    
    logger.info("🚀 ربات شروع به کار کرد...")
    application.run_polling()

if __name__ == "__main__":
    main()
