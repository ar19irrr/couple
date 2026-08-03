import logging
import random
import threading
import asyncio
import os
import json
import requests
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackContext, CallbackQueryHandler,
    MessageHandler, Filters
)
import config
from database import (
    get_members, set_members, save_couple, get_last_couple,
    get_couple_history, get_blocked_users, clear_blocked_users,
    get_stats, clear_data, get_groups, add_group,
    get_user_couple_stats, get_user_total_couples,
    set_user_gender, set_user_interest, get_user_profile,
    update_monthly_score, get_all_monthly_scores, reset_monthly_scores,
    check_and_reset_blocked, sync_groups, load_data,
    get_global_blocked_users, add_global_blocked_user, 
    remove_global_blocked_user, is_user_globally_blocked
)
from member_fetcher import get_all_members

# ==================== تقویم شمسی ====================
try:
    from rokh import get_today_events, get_events, DateSystem
except:
    print("⚠️ rokh نصب نیست!")

# ==================== تنظیمات لاگ ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

OWNER_ID = 1095925103

# ==================== بارگذاری فال‌ها ====================
FAL_FILE = os.path.join(os.path.dirname(__file__), 'fal.json')

def load_faals():
    try:
        with open(FAL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        logger.error(f"❌ خطا در بارگذاری فال‌ها: {e}")
        return []

FAALS = load_faals()
logger.info(f"✅ {len(FAALS)} فال بارگذاری شد")

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

FORTUNES = [
    "🌟 امروز روز عشق و مهربانی است!",
    "🌹 عشق در هواست... نفس عمیق بکش!",
    "💫 امروز یک روز خاص برای عاشق شدن است!",
    "🌺 دلت را به عشق بسپار...",
    "✨ ستاره‌های امروز به نفع عشق است!",
    "🌸 لبخند بزن، عشق در راه است!",
    "💝 امروز روزی است که قلبت را دنبال کنی!",
    "🌈 عشق مثل رنگین‌کمان است... امروز روز توست!",
    "🎈 با عشق پرواز کن!",
    "💖 امروز روزی است که عشق واقعی را پیدا می‌کنی!"
]

INTERESTS = {
    "music": {"emoji": "🎵", "label": "موسیقی"},
    "movie": {"emoji": "🎬", "label": "سینما و فیلم"},
    "sport": {"emoji": "⚽", "label": "ورزش"},
    "book": {"emoji": "📚", "label": "کتاب و مطالعه"},
    "game": {"emoji": "🎮", "label": "بازی و کامپیوتر"},
    "art": {"emoji": "🎨", "label": "هنر و نقاشی"},
    "travel": {"emoji": "✈️", "label": "سفر و گردشگری"},
    "food": {"emoji": "🍕", "label": "غذا و آشپزی"},
}

GENDERS = {
    "male": "👨 مرد",
    "female": "👩 زن",
    "other": "🌈 سایر"
}

def update_members_sync(chat_id):
    """به‌روزرسانی لیست اعضا - نسخه نهایی"""
    try:
        logger.info(f"🔄 شروع دریافت اعضا برای گروه {chat_id}")
        
        # ===== اجرای مستقیم با مدیریت Event Loop =====
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            members = loop.run_until_complete(get_all_members(chat_id))
            loop.close()
            
            if members and len(members) > 0:
                set_members(chat_id, members)
                logger.info(f"✅ {len(members)} عضو ذخیره شد")
                return members
            else:
                logger.warning(f"⚠️ هیچ عضوی پیدا نشد")
                return []
                
        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return []
            
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        return []
def get_daily_fortune():
    return random.choice(FORTUNES)

def get_ai_response_with_history(history):
    try:
        from openai import OpenAI
        
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("❌ OPENROUTER_API_KEY تنظیم نشده است!")
            return None
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        messages = [
            {"role": "system", "content": "شما یک دستیار هوشمند و دقیق فارسی هستید. به سوالات کاربر به طور کامل، دقیق و مفید پاسخ دهید. پاسخ‌های شما باید مرتبط با مکالمه قبلی باشد."}
        ]
        messages.extend(history)
        
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                messages=messages,
                max_tokens=600,
                temperature=0.7,
                timeout=25
            )
            content = response.choices[0].message.content
            if content and len(content) > 10:
                return content
        except Exception as e:
            logger.warning(f"⚠️ تلاش اول خطا داد: {e}")
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
            timeout=15
        )
        return response.choices[0].message.content
            
    except Exception as e:
        logger.error(f"❌ خطا در AI: {e}")
        return None

def get_ai_response(prompt):
    history = [{"role": "user", "content": prompt}]
    return get_ai_response_with_history(history)

def is_user_blocked(user_id):
    return is_user_globally_blocked(user_id)

# ==================== دستورات ====================
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id == OWNER_ID:
        start_text = """🤖 **ربات زوج‌یاب پیشرفته با هوش مصنوعی**

📌 دستورات سریع:
/ask <سوال> - پرسش از هوش مصنوعی 🧠
/event - مناسبت‌های امروز 📅
/fall - فال حافظ 🕌
/couple - انتخاب زوج تصادفی 💞

👑 **دستورات مالک:**
/block <id> - بلاک کردن کاربر
/unblock <id> - آنبلاک کردن کاربر
/blocked_list - لیست کاربران بلاک شده
/owner_stats - آمار کلی ربات
/owner_users - لیست کاربران
"""
    else:
        start_text = """🤖 **ربات زوج‌یاب پیشرفته با هوش مصنوعی**

📌 برای مشاهده راهنمای کامل دستورات، از دستور /help استفاده کنید.

📌 دستورات سریع:
/ask <سوال> - پرسش از هوش مصنوعی 🧠
/event - مناسبت‌های امروز 📅
/fall - فال حافظ 🕌
/couple - انتخاب زوج تصادفی 💞
/stats - آمار گروه 📊
/mystats - آمار شخصی شما 👤
/monthly_top - برترین‌های ماه 🏆

⚠️ نکته: ربات باید ادمین باشد و VPN روشن باشد."""
    
    update.message.reply_text(start_text, parse_mode="Markdown")

def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    help_text = """
📖 راهنمای کامل ربات زوج‌یاب + هوش مصنوعی

━━━━━━━━━━━━━━━━━━━━━
🤖 دستورات عمومی
━━━━━━━━━━━━━━━━━━━━━

📌 /start - نمایش این پیام
📌 /help - نمایش راهنمای کامل

━━━━━━━━━━━━━━━━━━━━━
🎯 بخش زوج‌یابی
━━━━━━━━━━━━━━━━━━━━━

📌 /couple - انتخاب یک زوج تصادفی
📌 /count - تعداد اعضای گروه
📌 /last - آخرین زوج انتخاب شده
📌 /history - تاریخچه ۱۰ زوج آخر
📌 /stats - آمار کلی گروه
📌 /mystats - آمار شخصی شما
📌 /monthly_top - برترین‌های ماه

━━━━━━━━━━━━━━━━━━━━━
🧠 بخش هوش مصنوعی
━━━━━━━━━━━━━━━━━━━━━

📌 /ask <سوال> - پرسش سوال از هوش مصنوعی
   مثال: /ask بهترین فیلم تاریخ چیست؟

📌 ریپلی کنید - روی پیام ربات ریپلی کنید
   تا مکالمه ادامه پیدا کند (بدون نیاز به /ask)

📌 /clear_history - پاک کردن تاریخچه مکالمه

━━━━━━━━━━━━━━━━━━━━━
📅 بخش تقویم و مناسبت‌ها
━━━━━━━━━━━━━━━━━━━━━

📌 /event - نمایش مناسبت‌های امروز
📌 /event 1405/1/1 - نمایش مناسبت‌های تاریخ مشخص

━━━━━━━━━━━━━━━━━━━━━
🕌 بخش فال و استخاره
━━━━━━━━━━━━━━━━━━━━━

📌 /fall - گرفتن فال حافظ با تفسیر
📌 **کلمه "فال"** - فقط کلمه "فال" رو بفرستید تا فال دریافت کنید

━━━━━━━━━━━━━━━━━━━━━
⚙️ تنظیمات پروفایل
━━━━━━━━━━━━━━━━━━━━━

📌 /setgender - تنظیم جنسیت (با دکمه)
📌 /setinterest - تنظیم علاقه (با دکمه)

━━━━━━━━━━━━━━━━━━━━━
🔧 مدیریت گروه (فقط ادمین)
━━━━━━━━━━━━━━━━━━━━━

📌 /addgroup - فعال کردن ربات در این گروه
📌 /reset - ریست کامل دیتابیس

━━━━━━━━━━━━━━━━━━━━━
💡 نکات مهم
━━━━━━━━━━━━━━━━━━━━━

✅ ربات باید ادمین گروه باشد
✅ برای دریافت اعضا و AI، VPN روشن باشد
✅ هر کاربر بعد از لاور شدن، ۷ روز در لیست سیاه می‌رود
✅ با تمام شدن اعضا، لیست سیاه خودکار ریست می‌شود
✅ هوش مصنوعی ۱۰ پیام آخر را به خاطر می‌سپارد
"""
    
    if user_id == OWNER_ID:
        help_text += """
━━━━━━━━━━━━━━━━━━━━━
👑 **دستورات مالک**
━━━━━━━━━━━━━━━━━━━━━

📌 /block <id> - بلاک کردن یک کاربر
📌 /unblock <id> - آنبلاک کردن یک کاربر
📌 /blocked_list - لیست کاربران بلاک شده
📌 /owner_stats - آمار کلی ربات
📌 /owner_users - لیست کاربران ثبت‌شده
"""
    
    help_text += """
━━━━━━━━━━━━━━━━━━━━━
🎉 ربات شما کامل است! لذت ببرید!
    """
    update.message.reply_text(help_text)

# ==================== دستورات بلاک ====================
def block_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        update.message.reply_text("⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return
    
    args = context.args
    if not args:
        update.message.reply_text(
            "❌ لطفاً آیدی کاربر مورد نظر را وارد کنید.\n"
            "مثال: `/block 123456789`\n"
            "💡 برای گرفتن آیدی کاربر، روی اسمش در گروه کلیک کنید و گزینه Copy ID را بزنید."
        )
        return
    
    try:
        target_user_id = int(args[0])
    except ValueError:
        update.message.reply_text("❌ آیدی کاربر باید عدد باشد.")
        return
    
    if target_user_id == OWNER_ID:
        update.message.reply_text("❌ نمی‌توانید خودتان را بلاک کنید!")
        return
    
    if add_global_blocked_user(target_user_id):
        try:
            user = context.bot.get_chat(target_user_id)
            user_name = user.first_name or "کاربر ناشناس"
        except:
            user_name = "کاربر ناشناس"
        
        update.message.reply_text(
            f"✅ کاربر {user_name} (ID: {target_user_id}) با موفقیت بلاک شد.\n"
            f"🔹 این کاربر دیگر نمی‌تواند از ربات استفاده کند."
        )
        logger.info(f"👑 مالک ربات کاربر {target_user_id} را بلاک کرد.")
    else:
        update.message.reply_text(f"ℹ️ کاربر {target_user_id} قبلاً بلاک شده است.")

def unblock_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        update.message.reply_text("⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return
    
    args = context.args
    if not args:
        update.message.reply_text(
            "❌ لطفاً آیدی کاربر مورد نظر را وارد کنید.\n"
            "مثال: `/unblock 123456789`"
        )
        return
    
    try:
        target_user_id = int(args[0])
    except ValueError:
        update.message.reply_text("❌ آیدی کاربر باید عدد باشد.")
        return
    
    if remove_global_blocked_user(target_user_id):
        try:
            user = context.bot.get_chat(target_user_id)
            user_name = user.first_name or "کاربر ناشناس"
        except:
            user_name = "کاربر ناشناس"
        
        update.message.reply_text(
            f"✅ کاربر {user_name} (ID: {target_user_id}) با موفقیت آنبلاک شد.\n"
            f"🔹 این کاربر دوباره می‌تواند از ربات استفاده کند."
        )
        logger.info(f"👑 مالک ربات کاربر {target_user_id} را آنبلاک کرد.")
    else:
        update.message.reply_text(f"ℹ️ کاربر {target_user_id} در لیست بلاک نیست.")

def blocked_list_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        update.message.reply_text("⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return
    
    blocked_users = get_global_blocked_users()
    
    if not blocked_users:
        update.message.reply_text("📭 هیچ کاربری در لیست بلاک نیست.")
        return
    
    msg = "🚫 **لیست کاربران بلاک شده:**\n\n"
    for i, uid in enumerate(blocked_users, 1):
        try:
            user = context.bot.get_chat(uid)
            user_name = user.first_name or "کاربر ناشناس"
            username = f"@{user.username}" if user.username else "بدون یوزرنیم"
            msg += f"{i}. {user_name} {username} (ID: {uid})\n"
        except:
            msg += f"{i}. کاربر ناشناس (ID: {uid})\n"
    
    update.message.reply_text(msg, parse_mode="Markdown")

# ==================== دستور /fall (فال حافظ) ====================
def fall_command(update: Update, context: CallbackContext):
    """دریافت فال حافظ از فایل JSON"""
    msg = update.message.reply_text("🔮 در حال گرفتن فال حافظ...")
    
    try:
        if not FAALS:
            msg.edit_text("❌ فایل فال‌ها پیدا نشد! لطفاً با ادمین تماس بگیرید.")
            return
        
        choice = random.choice(FAALS)
        title = choice.get('title', 'غزل حافظ')
        interpreter = choice.get('interpreter', '')
        
        final_msg = f"🕌 **فال حافظ**\n\n"
        final_msg += f"📜 **{title}**\n\n"
        final_msg += f"💬 **تفسیر:**\n{interpreter}\n\n"
        final_msg += "— حافظ"
        
        msg.edit_text(final_msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ خطا در فال: {e}")
        msg.edit_text("❌ خطا در دریافت فال. لطفاً دوباره تلاش کنید.")

# ==================== Handler برای کلمه "فال" ====================
def handle_fall_keyword(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    if text == "فال" or text.startswith("فال "):
        fall_command(update, context)
        return True
    return False

# ==================== بقیه دستورات ====================
def event_command(update: Update, context: CallbackContext):
    user_message = ' '.join(context.args)
    
    try:
        if user_message:
            parts = user_message.split('/')
            if len(parts) == 3:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                events_data = get_events(
                    day=day, 
                    month=month, 
                    year=year, 
                    input_date_system=DateSystem.JALALI
                )
                date_str = f"{year}/{month}/{day}"
            else:
                update.message.reply_text("❌ فرمت تاریخ اشتباه است. مثال: /event 1405/1/1")
                return
        else:
            events_data = get_today_events()
            jalali_date = events_data.get('jalali_date', {})
            date_str = f"{jalali_date.get('year', '')}/{jalali_date.get('month', '')}/{jalali_date.get('day', '')}"
        
        events = events_data.get('events', {})
        is_holiday = events_data.get('is_holiday', False)
        
        msg = f"📅 **تقویم روز {date_str}**\n\n"
        
        jalali_events = events.get('jalali', [])
        if jalali_events:
            msg += "🟢 **مناسبت‌های شمسی:**\n"
            for e in jalali_events:
                desc = e.get('description', '')
                is_holiday_event = e.get('is_holiday', False)
                holiday_tag = "🔴 (تعطیل)" if is_holiday_event else ""
                msg += f"  • {desc} {holiday_tag}\n"
            msg += "\n"
        
        gregorian_events = events.get('gregorian', [])
        if gregorian_events:
            msg += "🔵 **مناسبت‌های میلادی:**\n"
            for e in gregorian_events:
                desc = e.get('description', '')
                is_holiday_event = e.get('is_holiday', False)
                holiday_tag = "🔴 (تعطیل)" if is_holiday_event else ""
                msg += f"  • {desc} {holiday_tag}\n"
            msg += "\n"
        
        hijri_events = events.get('hijri', [])
        if hijri_events:
            msg += "🟡 **مناسبت‌های هجری قمری:**\n"
            for e in hijri_events:
                desc = e.get('description', '')
                is_holiday_event = e.get('is_holiday', False)
                holiday_tag = "🔴 (تعطیل)" if is_holiday_event else ""
                msg += f"  • {desc} {holiday_tag}\n"
            msg += "\n"
        
        if is_holiday:
            msg += "🎉 **امروز تعطیل رسمی است!** 🎉"
        
        if not jalali_events and not gregorian_events and not hijri_events:
            msg += "📭 هیچ مناسبت خاصی برای این تاریخ ثبت نشده است."
        
        update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ خطا در /event: {e}")
        update.message.reply_text("❌ خطا در دریافت مناسبت‌ها. لطفاً دوباره تلاش کنید.")

def ask_command(update: Update, context: CallbackContext):
    user_message = ' '.join(context.args)
    reply_to_message = update.message.reply_to_message
    
    if reply_to_message and not user_message:
        if reply_to_message.from_user.is_bot:
            user_message = reply_to_message.text
            if user_message and "🤖 پاسخ هوش مصنوعی" in user_message:
                user_message = user_message.split("\n\n")[-1] if "\n\n" in user_message else user_message
        else:
            user_message = reply_to_message.text
    
    if not user_message:
        update.message.reply_text(
            "❌ لطفاً سوال خود را بعد از /ask بنویسید یا روی یک پیام ریپلی کنید.\n"
            "مثال: /ask بهترین فیلم تاریخ چیست؟"
        )
        return
    
    loading_msg = update.message.reply_text("🤔 در حال فکر کردن...")
    
    try:
        history = context.user_data.get("chat_history", [])
        history.append({"role": "user", "content": user_message})
        
        if len(history) > 10:
            history = history[-10:]
        
        ai_response = get_ai_response_with_history(history)
        
        if ai_response:
            history.append({"role": "assistant", "content": ai_response})
            context.user_data["chat_history"] = history
            
            if len(ai_response) > 4000:
                parts = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)]
                loading_msg.edit_text(f"🤖 پاسخ هوش مصنوعی (بخش ۱ از {len(parts)}):\n\n{parts[0]}")
                for i, part in enumerate(parts[1:], 2):
                    update.message.reply_text(f"🤖 پاسخ هوش مصنوعی (بخش {i} از {len(parts)}):\n\n{part}")
            else:
                loading_msg.edit_text(f"🤖 پاسخ هوش مصنوعی:\n\n{ai_response}")
        else:
            loading_msg.edit_text(
                "❌ خطا در دریافت پاسخ.\n"
                "لطفاً چند دقیقه دیگر تلاش کنید یا سوال خود را کوتاه‌تر کنید."
            )
            
    except Exception as e:
        logger.error(f"❌ خطا در /ask: {e}")
        loading_msg.edit_text("❌ خطایی رخ داد. لطفاً بعداً تلاش کنید.")

def handle_reply(update: Update, context: CallbackContext):
    try:
        if not update.message.reply_to_message:
            return
        
        replied_msg = update.message.reply_to_message
        if not replied_msg.from_user.is_bot:
            return
        
        bot_username = context.bot.username
        if replied_msg.from_user.username != bot_username:
            return
        
        user_message = update.message.text
        if not user_message:
            return
        
        loading_msg = update.message.reply_text("🤔 در حال فکر کردن...")
        
        history = context.user_data.get("chat_history", [])
        history.append({"role": "user", "content": user_message})
        
        if len(history) > 10:
            history = history[-10:]
        
        ai_response = get_ai_response_with_history(history)
        
        if ai_response:
            history.append({"role": "assistant", "content": ai_response})
            context.user_data["chat_history"] = history
            
            if len(ai_response) > 4000:
                parts = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)]
                loading_msg.edit_text(f"🤖 پاسخ هوش مصنوعی (بخش ۱ از {len(parts)}):\n\n{parts[0]}")
                for i, part in enumerate(parts[1:], 2):
                    update.message.reply_text(f"🤖 پاسخ هوش مصنوعی (بخش {i} از {len(parts)}):\n\n{part}")
            else:
                loading_msg.edit_text(f"🤖 پاسخ هوش مصنوعی:\n\n{ai_response}")
        else:
            loading_msg.edit_text(
                "❌ خطا در دریافت پاسخ.\n"
                "لطفاً چند دقیقه دیگر تلاش کنید."
            )
            
    except Exception as e:
        logger.error(f"❌ خطا در handle_reply: {e}")
        update.message.reply_text("❌ خطایی رخ داد. لطفاً بعداً تلاش کنید.")

def clear_history_command(update: Update, context: CallbackContext):
    context.user_data["chat_history"] = []
    update.message.reply_text("✅ تاریخچه مکالمه پاک شد!")

def setgender_command(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="gender_male")],
        [InlineKeyboardButton("👩 زن", callback_data="gender_female")],
        [InlineKeyboardButton("🌈 سایر", callback_data="gender_other")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "🧑‍🤝‍🧑 لطفاً جنسیت خود را انتخاب کنید:\n\nاین اطلاعات برای انتخاب زوج بر اساس جنسیت استفاده می‌شود.",
        reply_markup=reply_markup
    )

def setinterest_command(update: Update, context: CallbackContext):
    keyboard = []
    for key, value in INTERESTS.items():
        keyboard.append([InlineKeyboardButton(
            f"{value['emoji']} {value['label']}",
            callback_data=f"interest_{key}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "🎯 لطفاً علاقه‌مندی خود را انتخاب کنید:\n\nاین اطلاعات برای انتخاب زوج بر اساس علایق مشترک استفاده می‌شود.",
        reply_markup=reply_markup
    )

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("gender_"):
        gender = data.replace("gender_", "")
        set_user_gender(chat_id, user_id, gender)
        gender_label = GENDERS.get(gender, gender)
        query.edit_message_text(f"✅ جنسیت شما به {gender_label} تنظیم شد!")
    
    elif data.startswith("interest_"):
        interest = data.replace("interest_", "")
        set_user_interest(chat_id, user_id, interest)
        interest_label = INTERESTS.get(interest, {}).get("label", interest)
        query.edit_message_text(f"✅ علاقه شما به {interest_label} تنظیم شد!")

def couple_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🔄 در حال انتخاب زوج...")
    
    members = get_members(chat_id)
    if not members:
        update.message.reply_text("❌ لیست اعضا خالی است. ابتدا /update را بزنید.")
        return
    
    check_and_reset_blocked(chat_id)
    
    blocked = get_blocked_users(chat_id)
    user_id = update.effective_user.id
    user_profile = get_user_profile(chat_id, user_id)
    user_gender = user_profile.get("gender")
    
    if user_gender:
        opposite_gender = "female" if user_gender == "male" else "male" if user_gender == "female" else None
        if opposite_gender:
            filtered_members = []
            for m in members:
                if m["id"] in blocked or m["id"] == user_id:
                    continue
                profile = get_user_profile(chat_id, m["id"])
                if profile.get("gender") == opposite_gender:
                    filtered_members.append(m)
            
            available_members = filtered_members if len(filtered_members) >= 2 else [m for m in members if m["id"] not in blocked and m["id"] != user_id]
        else:
            available_members = [m for m in members if m["id"] not in blocked and m["id"] != user_id]
    else:
        available_members = [m for m in members if m["id"] not in blocked and m["id"] != user_id]
    
    if len(available_members) < 2:
        check_and_reset_blocked(chat_id)
        blocked = get_blocked_users(chat_id)
        available_members = [m for m in members if m["id"] not in blocked and m["id"] != user_id]
        
        if len(available_members) < 2:
            update.message.reply_text(
                f"❌ تعداد اعضای قابل انتخاب کافی نیست.\n"
                f"🔹 کل اعضا: {len(members)} نفر\n"
                f"🔹 در لیست سیاه: {len(blocked)} نفر\n"
                f"🔄 لیست سیاه به‌طور خودکار ریست شد."
            )
            return
    
    user_interest = user_profile.get("interest")
    if user_interest and len(available_members) >= 2:
        interest_matched = []
        for m in available_members:
            profile = get_user_profile(chat_id, m["id"])
            if profile.get("interest") == user_interest:
                interest_matched.append(m)
        
        selected = random.sample(interest_matched, 2) if len(interest_matched) >= 2 else random.sample(available_members, 2)
    else:
        selected = random.sample(available_members, 2)
    
    user1, user2 = selected[0], selected[1]
    save_couple(chat_id, user1, user2)
    
    update_monthly_score(chat_id, user1["id"])
    update_monthly_score(chat_id, user2["id"])
    
    fortune = get_daily_fortune()
    
    msg = f"""{random.choice(COUPLE_MESSAGES)}

به پای هم پیر سیر دیر و عاشق باشید 🫂
پایدار تا پای دار 
باهم بمیرید زنده شوید 
{random.choice(JOKE_MESSAGES)}

👤 [{user1['name']}](tg://user?id={user1['id']})
❤️ با ❤️
👤 [{user2['name']}](tg://user?id={user2['id']})

{random.choice(CELEBRATION_MESSAGES)}

🌟 فال امروز: {fortune}"""
    
    update.message.reply_text(msg, parse_mode="Markdown")
    clear_blocked_users(chat_id)
    logger.info(f"✅ زوج انتخاب شد برای گروه {chat_id}")

def monthly_top_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    members = get_members(chat_id)
    user_map = {m["id"]: m for m in members}
    
    monthly_scores = get_all_monthly_scores(chat_id)
    sorted_users = sorted(monthly_scores.items(), key=lambda x: x[1], reverse=True)
    
    msg = "🏆 برترین لاورهای ماه\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    if sorted_users:
        for i, (user_id, score) in enumerate(sorted_users[:10]):
            user_info = user_map.get(int(user_id), {"name": f"کاربر ناشناس", "username": "ندارد"})
            medal = medals[i] if i < len(medals) else f"{i+1}."
            msg += f"{medal} {user_info['name']} (@{user_info['username']}) — {score} بار\n"
    else:
        msg += "📭 هنوز کسی امتیازی کسب نکرده!"
    
    update.message.reply_text(msg)

def announce_monthly_winners(chat_id, bot):
    monthly_scores = get_all_monthly_scores(chat_id)
    
    if not monthly_scores:
        return
    
    top_user_id = max(monthly_scores, key=monthly_scores.get)
    top_score = monthly_scores[top_user_id]
    members = get_members(chat_id)
    user_map = {m["id"]: m for m in members}
    top_user = user_map.get(int(top_user_id), {"name": "کاربر ناشناس"})
    
    try:
        ai_prompt = f"یک پیام تبریک عاشقانه و شاد برای {top_user['name']} بنویس که برنده لاورهای ماه شده با {top_score} بار لاور شدن. پیام باید کوتاه، احساسی و پر از انرژی مثبت باشه."
        ai_message = get_ai_response(ai_prompt)
        
        if ai_message:
            msg = f"🌟 برنده لاورهای ماه 🌟\n\n"
            msg += f"👤 {top_user['name']} با {top_score} بار لاور شدن!\n\n"
            msg += f"💬 پیام ویژه:\n{ai_message}"
        else:
            msg = f"🌟 برنده لاورهای ماه 🌟\n\n"
            msg += f"👤 {top_user['name']} با {top_score} بار لاور شدن!\n"
            msg += "🎉 تبریک میگم! تو بهترین لاوری! ❤️"
    except Exception as e:
        logger.error(f"❌ خطا در AI: {e}")
        msg = f"🌟 برنده لاورهای ماه 🌟\n\n"
        msg += f"👤 {top_user['name']} با {top_score} بار لاور شدن!\n"
        msg += "🎉 تبریک میگم! تو بهترین لاوری! ❤️"
    
    bot.send_message(chat_id=chat_id, text=msg)
    reset_monthly_scores(chat_id)

def monthly_announcement_job(context):
    bot = context.job.context.bot
    groups = get_groups()
    for chat_id in groups:
        announce_monthly_winners(chat_id, bot)

def schedule_monthly_announcement(dispatcher):
    job_queue = dispatcher.job_queue
    if not job_queue:
        return
    
    now = datetime.now()
    next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
    time_until_next_month = (next_month - now).total_seconds()
    
    job_queue.run_once(
        monthly_announcement_job,
        when=time_until_next_month,
        context=dispatcher
    )

def addgroup_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    logger.info(f"📌 تلاش برای افزودن گروه: {chat_id}")
    
    try:
        bot_member = context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            update.message.reply_text(
                "❌ ربات ادمین گروه نیست!\n"
                "لطفاً مراحل زیر را انجام دهید:\n"
                "1️⃣ روی اسم ربات در گروه کلیک کنید\n"
                "2️⃣ گزینه Make Admin را بزنید\n"
                "3️⃣ تمام دسترسی‌ها را فعال کنید\n"
                "4️⃣ دوباره /addgroup را بزنید"
            )
            return
    except Exception as e:
        logger.error(f"❌ خطا در بررسی ادمین: {e}")
        update.message.reply_text("❌ خطا در بررسی دسترسی ربات.")
        return
    
    if add_group(chat_id):
        update.message.reply_text(f"✅ این گروه به لیست گروه‌های فعال اضافه شد.")
        members = update_members_sync(chat_id)
        if members:
            update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
        else:
            update.message.reply_text(
                "❌ خطا در دریافت اعضا.\n"
                "لطفاً موارد زیر را بررسی کنید:\n"
                "1️⃣ VPN روشن است\n"
                "2️⃣ ربات ادمین گروه است (با تمام دسترسی‌ها)\n"
                "3️⃣ فایل session.session در گیت‌هاب وجود دارد"
            )
    else:
        update.message.reply_text(f"ℹ️ این گروه قبلاً به لیست اضافه شده است.")

def update_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🔄 در حال به‌روزرسانی لیست همه اعضا...")
    
    try:
        bot_member = context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            update.message.reply_text(
                "❌ ربات ادمین گروه نیست!\n"
                "لطفاً مراحل زیر را انجام دهید:\n"
                "1️⃣ روی اسم ربات در گروه کلیک کنید\n"
                "2️⃣ گزینه Make Admin را بزنید\n"
                "3️⃣ تمام دسترسی‌ها را فعال کنید\n"
                "4️⃣ دوباره /update را بزنید"
            )
            return
    except Exception as e:
        logger.error(f"❌ خطا در بررسی ادمین: {e}")
        update.message.reply_text("❌ خطا در بررسی دسترسی ربات.")
        return
    
    members = update_members_sync(chat_id)
    if members:
        update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
    else:
        update.message.reply_text(
            "❌ خطا در دریافت اعضا.\n"
            "لطفاً موارد زیر را بررسی کنید:\n"
            "1️⃣ VPN روشن است\n"
            "2️⃣ ربات ادمین گروه است (با تمام دسترسی‌ها)\n"
            "3️⃣ فایل session.session در گیت‌هاب وجود دارد"
        )

def last_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    last = get_last_couple(chat_id)
    
    if last and isinstance(last, dict):
        u1 = last.get("user1", {})
        u2 = last.get("user2", {})
        date = last.get("date", "")[:10]
        update.message.reply_text(
            f"""📅 آخرین زوج ({date})

👤 [{u1.get('name', 'نامشخص')}](tg://user?id={u1.get('id')})
❤️ با ❤️
👤 [{u2.get('name', 'نامشخص')}](tg://user?id={u2.get('id')})"""
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
        if isinstance(couple, dict):
            u1 = couple.get("user1", {})
            u2 = couple.get("user2", {})
            date = couple.get("date", "")[:10]
            msg += f"{i}. [{u1.get('name', 'نامشخص')}](tg://user?id={u1.get('id')}) ❤️ [{u2.get('name', 'نامشخص')}](tg://user?id={u2.get('id')}) ({date})\n"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def stats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    stats = get_stats(chat_id)
    
    msg = f"📊 آمار کلی گروه:\n\n"
    msg += f"👥 تعداد اعضا: {stats['total_members']} نفر\n"
    msg += f"💞 تعداد زوج‌ها: {stats['total_couples']} بار\n"
    msg += f"🌟 کاربران منحصر‌به‌فرد: {stats['unique_users']} نفر\n"
    
    if stats.get('last_couple') and isinstance(stats['last_couple'], dict):
        u1 = stats['last_couple'].get('user1', {})
        u2 = stats['last_couple'].get('user2', {})
        msg += f"\n💖 آخرین زوج:\n👤 [{u1.get('name', 'نامشخص')}](tg://user?id={u1.get('id')}) ❤️ [{u2.get('name', 'نامشخص')}](tg://user?id={u2.get('id')})"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def mystats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "کاربر"
    
    total_couples = get_user_total_couples(chat_id, user_id)
    partner_stats = get_user_couple_stats(chat_id, user_id)
    
    msg = f"📊 آمار شخصی {user_name}\n\n"
    msg += f"💞 تعداد کل لاورها: {total_couples} بار\n"
    
    if partner_stats:
        msg += f"\n👥 شریک‌های لاور:\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, partner in enumerate(partner_stats[:5]):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            msg += f"{medal} [{partner['name']}](tg://user?id={partner['id']}) — {partner['count']} بار\n"
        
        if len(partner_stats) > 5:
            msg += f"\nو {len(partner_stats) - 5} نفر دیگر..."
    else:
        msg += f"\n📭 هنوز با کسی لاور نشدی!"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def reset_command(update: Update, context: CallbackContext):
    clear_data()
    update.message.reply_text("✅ دیتابیس با موفقیت ریست شد.")

# ==================== دستورات ویژه مالک ====================
def owner_stats_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        update.message.reply_text("⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return
    
    groups = sync_groups()
    data = load_data()
    
    total_users = set()
    for chat_id in groups:
        members = get_members(chat_id)
        for m in members:
            total_users.add(m.get("id"))
    
    msg = f"📊 آمار کلی ربات\n\n"
    msg += f"👥 تعداد گروه‌های فعال: {len(groups)} گروه\n"
    msg += f"👤 تعداد کل کاربران ثبت‌شده: {len(total_users)} نفر\n"
    
    total_couples = 0
    for chat_id in groups:
        history = get_couple_history(chat_id, 1000)
        total_couples += len(history)
    msg += f"💞 تعداد کل زوج‌ها: {total_couples} بار\n"
    
    if groups:
        msg += f"\n📌 لیست گروه‌های فعال:\n"
        for i, chat_id in enumerate(groups, 1):
            try:
                chat = context.bot.get_chat(chat_id)
                chat_name = chat.title or chat.first_name or "گروه ناشناس"
                member_count = len(get_members(chat_id))
                msg += f"{i}. {chat_name} (ID: {chat_id}) — {member_count} عضو\n"
            except:
                msg += f"{i}. گروه ناشناس (ID: {chat_id})\n"
    else:
        msg += "\n📭 هیچ گروه فعالی یافت نشد."
    
    update.message.reply_text(msg)

def owner_users_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        update.message.reply_text("⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return
    
    groups = get_groups()
    all_users = {}
    
    for chat_id in groups:
        members = get_members(chat_id)
        for m in members:
            user_id_key = m.get("id")
            if user_id_key:
                if user_id_key not in all_users:
                    all_users[user_id_key] = {
                        "name": m.get("name", "بدون نام"),
                        "username": m.get("username", "ندارد"),
                        "groups": []
                    }
                all_users[user_id_key]["groups"].append(chat_id)
    
    msg = "👥 لیست کاربران ثبت‌شده در ربات\n\n"
    
    if all_users:
        for i, (uid, info) in enumerate(list(all_users.items())[:20], 1):
            groups_count = len(info["groups"])
            msg += f"{i}. {info['name']} (@{info['username']}) — {groups_count} گروه\n"
        
        if len(all_users) > 20:
            msg += f"\n... و {len(all_users) - 20} نفر دیگر"
    else:
        msg += "📭 هنوز کاربری ثبت نشده است."
    
    update.message.reply_text(msg)

# ==================== AI Message Handler ====================
def ai_response(text):
    text_lower = text.lower()
    
    if "عشق" in text_lower or "دوست" in text_lower:
        return random.choice([
            "💖 عشق زیباترین احساس دنیاست!",
            "❤️ عشق یعنی همین...",
            "💕 عشق همیشه در قلب‌ها جاری است!"
        ])
    elif "خنده" in text_lower or "شوخی" in text_lower:
        return random.choice([
            "😂 خنده بهترین داروی دنیاست!",
            "😄 شوخی با عشق قشنگ‌تر میشه!",
            "🤣 میدونستم که میخندی!"
        ])
    elif "سلام" in text_lower:
        return "👋 سلام! چطور می‌تونم کمکت کنم؟"
    elif "خوبی" in text_lower or "چطوری" in text_lower:
        return "❤️ خوبم، ممنون! تو چطوری؟"
    else:
        return None

def handle_ai_message(update: Update, context: CallbackContext):
    try:
        if not update.message:
            return
        
        user_message = update.message.text
        if not user_message:
            return
        
        response = ai_response(user_message)
        if response:
            update.message.reply_text(response)
    except Exception as e:
        logger.error(f"❌ خطا در handle_ai_message: {e}")

# ==================== کار روزانه ====================
def daily_job(context: CallbackContext):
    chat_id = context.job.context
    bot = context.bot
    
    logger.info(f"🔄 انتخاب زوج روزانه برای گروه {chat_id}...")
    members = update_members_sync(chat_id)
    if not members:
        bot.send_message(chat_id=chat_id, text="❌ خطا در دریافت لیست اعضا.")
        return
    
    check_and_reset_blocked(chat_id)
    
    blocked = get_blocked_users(chat_id)
    available_members = [m for m in members if m["id"] not in blocked]
    
    if len(available_members) < 2:
        check_and_reset_blocked(chat_id)
        blocked = get_blocked_users(chat_id)
        available_members = [m for m in members if m["id"] not in blocked]
        
        if len(available_members) < 2:
            bot.send_message(chat_id=chat_id, text="❌ تعداد اعضای قابل انتخاب کافی نیست.")
            return
    
    user1, user2 = random.sample(available_members, 2)
    save_couple(chat_id, user1, user2)
    
    update_monthly_score(chat_id, user1["id"])
    update_monthly_score(chat_id, user2["id"])
    
    fortune = get_daily_fortune()
    
    msg = f"""{random.choice(COUPLE_MESSAGES)}
به پای هم پیر سیر دیر و عاشق باشید 🫂
پایدار تا پای دار 
باهم بمیرید زنده شوید 
{random.choice(JOKE_MESSAGES)}

👤 [{user1['name']}](tg://user?id={user1['id']})
❤️ با ❤️
👤 [{user2['name']}](tg://user?id={user2['id']})

{random.choice(CELEBRATION_MESSAGES)}

🌟 فال امروز: {fortune}"""
    
    bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    clear_blocked_users(chat_id)
    logger.info(f"✅ زوج روزانه انتخاب شد برای گروه {chat_id}")

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
        job_queue.run_repeating(daily_job, interval=86400, first=10, context=chat_id)
        logger.info(f"✅ کار روزانه برای گروه {chat_id} تنظیم شد.")

# ==================== اجرا ====================
def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 وب‌سرور Flask روی پورت ۱۰۰۰۰ شروع به کار کرد...")
    
    updater = Updater(token=config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    try:
        updater.bot.delete_webhook()
        logger.info("✅ Webhook قبلی پاک شد.")
    except Exception as e:
        logger.warning(f"⚠️ خطا در پاک کردن Webhook: {e}")
    
    # ===== Handler برای ریپلی =====
    dp.add_handler(MessageHandler(Filters.text & Filters.reply, handle_reply))
    
    # ===== Handler برای کلمه "فال" =====
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_fall_keyword))
    
    # ===== دستورات =====
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("fall", fall_command))
    dp.add_handler(CommandHandler("event", event_command))
    dp.add_handler(CommandHandler("ask", ask_command))
    dp.add_handler(CommandHandler("clear_history", clear_history_command))
    dp.add_handler(CommandHandler("setgender", setgender_command))
    dp.add_handler(CommandHandler("setinterest", setinterest_command))
    dp.add_handler(CommandHandler("addgroup", addgroup_command))
    dp.add_handler(CommandHandler("couple", couple_command))
    dp.add_handler(CommandHandler("update", update_command))
    dp.add_handler(CommandHandler("last", last_command))
    dp.add_handler(CommandHandler("count", count_command))
    dp.add_handler(CommandHandler("history", history_command))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("mystats", mystats_command))
    dp.add_handler(CommandHandler("monthly_top", monthly_top_command))
    dp.add_handler(CommandHandler("reset", reset_command))
    
    # ===== دستورات بلاک =====
    dp.add_handler(CommandHandler("block", block_command))
    dp.add_handler(CommandHandler("unblock", unblock_command))
    dp.add_handler(CommandHandler("blocked_list", blocked_list_command))
    
    # ===== دستورات مالک =====
    dp.add_handler(CommandHandler("owner_stats", owner_stats_command))
    dp.add_handler(CommandHandler("owner_users", owner_users_command))
    
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_ai_message))
    
    schedule_daily_jobs(dp)
    schedule_monthly_announcement(dp)
    
    logger.info("🚀 ربات شروع به کار کرد...")
    updater.start_polling(drop_pending_updates=True, timeout=20)
    updater.idle()

if __name__ == "__main__":
    main()
