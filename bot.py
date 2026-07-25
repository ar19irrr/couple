import logging
import random
from datetime import timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import config
from database import (
    get_groups, add_group, remove_group,
    get_members, set_members, save_couple, get_last_couple
)
from member_fetcher import get_all_members

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def is_admin(update: Update):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        admins = await update.get_bot().get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id == user_id:
                return True
        return False
    except Exception as e:
        logger.error(f"خطا در بررسی ادمین: {e}")
        return False

async def update_members(chat_id):
    try:
        members = await get_all_members(chat_id)
        if members:
            set_members(chat_id, members)
        return members
    except Exception as e:
        logger.error(f"❌ خطا در دریافت اعضا برای گروه {chat_id}: {e}")
        return []

async def select_couple(application, chat_id):
    members = get_members(chat_id)
    
    if len(members) < 2:
        await application.bot.send_message(
            chat_id=chat_id,
            text="❌ تعداد اعضا کافی نیست (حداقل ۲ نفر)"
        )
        return
    
    user1, user2 = random.sample(members, 2)
    save_couple(chat_id, user1, user2)
    
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
    
    logger.info(f"✅ زوج انتخاب شد برای گروه {chat_id}: {user1['name']} و {user2['name']}")

async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    # این تابع برای هر گروه به طور جداگانه اجرا می‌شود
    chat_id = context.job.chat_id
    application = context.application
    
    logger.info(f"🔄 انتخاب زوج روزانه برای گروه {chat_id}...")
    await update_members(chat_id)
    await select_couple(application, chat_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **ربات زوج‌یاب**\n\n"
        "برای فعال کردن ربات در این گروه، ادمین گروه باید دستور /addgroup را ارسال کند.\n\n"
        "📌 **دستورات ادمین:**\n"
        "/addgroup - فعال کردن ربات در این گروه\n"
        "/removegroup - غیرفعال کردن ربات در این گروه\n"
        "/couple - انتخاب زوج (فقط ادمین‌ها)\n"
        "/update - به‌روزرسانی لیست (فقط ادمین‌ها)\n\n"
        "📌 **دستورات عمومی:**\n"
        "/last - آخرین زوج\n"
        "/count - تعداد اعضا",
        parse_mode="Markdown"
    )

async def add_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not await is_admin(update):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌توانند ربات را فعال کنند.")
        return
    
    if add_group(chat_id):
        await update.message.reply_text("✅ ربات در این گروه فعال شد!")
        # به‌روزرسانی اولیه اعضا
        await update_members(chat_id)
        
        # تنظیم Job برای این گروه
        job_queue = context.application.job_queue
        if job_queue:
            job_queue.run_repeating(
                daily_job,
                interval=86400,
                first=10,
                chat_id=chat_id
            )
            logger.info(f"✅ کار روزانه برای گروه {chat_id} تنظیم شد.")
    else:
        await update.message.reply_text("ℹ️ ربات قبلاً در این گروه فعال است.")

async def remove_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not await is_admin(update):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌توانند ربات را غیرفعال کنند.")
        return
    
    if remove_group(chat_id):
        await update.message.reply_text("✅ ربات در این گروه غیرفعال شد!")
        # حذف Jobهای این گروه
        job_queue = context.application.job_queue
        if job_queue:
            jobs = job_queue.jobs()
            for job in jobs:
                if job.chat_id == chat_id:
                    job.schedule_removal()
    else:
        await update.message.reply_text("ℹ️ ربات در این گروه فعال نیست.")

async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in get_groups():
        await update.message.reply_text("❌ ربات در این گروه فعال نیست. ادمین باید دستور /addgroup را بزند.")
        return
    
    if not await is_admin(update):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند.")
        return
    
    await update.message.reply_text("🔄 در حال انتخاب...")
    await update_members(chat_id)
    await select_couple(context.application, chat_id)

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in get_groups():
        await update.message.reply_text("❌ ربات در این گروه فعال نیست. ادمین باید دستور /addgroup را بزند.")
        return
    
    if not await is_admin(update):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند.")
        return
    
    await update.message.reply_text("🔄 در حال به‌روزرسانی...")
    members = await update_members(chat_id)
    await update.message.reply_text(f"✅ {len(members)} عضو پیدا شد.")

async def last_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in get_groups():
        await update.message.reply_text("❌ ربات در این گروه فعال نیست.")
        return
    
    last = get_last_couple(chat_id)
    if last and last.get("user1"):
        u1 = last["user1"]
        u2 = last["user2"]
        msg = f"📅 آخرین زوج:\n\n👤 {u1['name']} (@{u1['username']})\n❤️ با\n👤 {u2['name']} (@{u2['username']})"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ هنوز زوجی انتخاب نشده.")

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in get_groups():
        await update.message.reply_text("❌ ربات در این گروه فعال نیست.")
        return
    
    members = get_members(chat_id)
    await update.message.reply_text(f"👥 تعداد اعضا: {len(members)} نفر")

def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addgroup", add_group_command))
    application.add_handler(CommandHandler("removegroup", remove_group_command))
    application.add_handler(CommandHandler("couple", couple_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("last", last_command))
    application.add_handler(CommandHandler("count", count_command))
    
    logger.info("🚀 ربات شروع به کار کرد...")
    application.run_polling()

if __name__ == "__main__":
    main()
