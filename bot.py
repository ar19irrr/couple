import logging
import random
import threading
import asyncio
import os
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
    check_and_reset_blocked
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

# ==================== فال‌های روزانه ====================
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

# ==================== علایق ====================
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

# ==================== تابع دریافت اعضا ====================
def update_members_sync(chat_id):
    try:
        logger.info(f"🔄 شروع دریافت اعضا برای گروه {chat_id}")
        session_file = os.path.join(os.path.dirname(__file__), 'session.session')
        if not os.path.exists(session_file):
            logger.error(f"❌ فایل نشست در مسیر {session_file} پیدا نشد!")
            return []
        
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

def get_daily_fortune():
    return random.choice(FORTUNES)

# ==================== هوش مصنوعی (DeepSeek) ====================
def get_ai_response(prompt):
    """دریافت پاسخ از هوش مصنوعی با DeepSeek - بهینه شده برای پاسخ‌های طولانی"""
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
        
        # تلاش اول با توکن بیشتر برای پاسخ‌های طولانی
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                messages=[
                    {"role": "system", "content": "شما یک دستیار هوشمند و دقیق فارسی هستید. به سوالات کاربر به طور کامل، دقیق و مفید پاسخ دهید. اگر اطلاعاتی ندارید، صادقانه بگویید."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7,
                timeout=25
            )
            content = response.choices[0].message.content
            if content and len(content) > 10:
                return content
        except Exception as e:
            logger.warning(f"⚠️ تلاش اول با توکن بیشتر خطا داد: {e}")
        
        # تلاش دوم با توکن کمتر (در صورت خطا)
        response = client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "شما یک دستیار هوشمند فارسی هستید. به سوالات کاربر پاسخ دقیق و مختصر دهید."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7,
            timeout=15
        )
        return response.choices[0].message.content
            
    except Exception as e:
        logger.error(f"❌ خطا در AI: {e}")
        return None

# ==================== دستورات ====================
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        """🤖 ربات زوج‌یاب پیشرفته با هوش مصنوعی

📌 دستورات جدید:
/ask <سوال> - پرسش سوال از هوش مصنوعی 🧠

📌 دستورات اصلی:
/start - این پیام
/setgender - تنظیم جنسیت
/setinterest - تنظیم علاقه
/addgroup - فعال کردن ربات در این گروه
/couple - انتخاب زوج
/count - تعداد اعضا
/last - آخرین زوج
/history - تاریخچه زوج‌ها
/stats - آمار گروه
/mystats - آمار شخصی شما
/monthly_top - برترین‌های ماه
/reset - ریست دیتابیس

✨ امکانات ویژه:
• انتخاب زوج بر اساس جنسیت و علایق
• فال روزانه
• سیستم امتیازدهی ماهانه
• پرسش و پاسخ با هوش مصنوعی 🧠

⚠️ نکته: ربات باید ادمین باشد و VPN روشن باشد."""
    )

# ==================== تنظیم جنسیت ====================
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

# ==================== تنظیم علاقه ====================
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

# ==================== پردازش دکمه‌ها ====================
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

# ==================== انتخاب زوج (با ریست خودکار) ====================
def couple_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🔄 در حال انتخاب زوج...")
    
    members = get_members(chat_id)
    if not members:
        update.message.reply_text("❌ لیست اعضا خالی است. ابتدا /update را بزنید.")
        return
    
    # ===== بررسی و ریست خودکار لیست سیاه =====
    check_and_reset_blocked(chat_id)
    
    blocked = get_blocked_users(chat_id)
    user_id = update.effective_user.id
    user_profile = get_user_profile(chat_id, user_id)
    user_gender = user_profile.get("gender")
    
    # فیلتر بر اساس جنسیت
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
    
    # اگه تعداد قابل انتخاب کم بود، دوباره چک کن
    if len(available_members) < 2:
        # یه بار دیگه لیست سیاه رو ریست کن و دوباره امتحان کن
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
    
    # فیلتر بر اساس علاقه
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
    
    # امتیاز ماهانه
    update_monthly_score(chat_id, user1["id"])
    update_monthly_score(chat_id, user2["id"])
    
    fortune = get_daily_fortune()
    
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

{random.choice(CELEBRATION_MESSAGES)}

🌟 فال امروز: {fortune}"""
    
    update.message.reply_text(msg)
    clear_blocked_users(chat_id)
    logger.info(f"✅ زوج انتخاب شد برای گروه {chat_id}")

# ==================== برترین‌های ماه ====================
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

# ==================== اعلام برنده ماه با AI ====================
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

# ==================== دستور /ask ====================
def ask_command(update: Update, context: CallbackContext):
    """دستور /ask برای پرسش سوال از هوش مصنوعی"""
    user_message = ' '.join(context.args)
    
    if not user_message:
        update.message.reply_text(
            "❌ لطفاً سوال خود را بعد از /ask بنویسید.\n"
            "مثال: /ask بهترین فیلم تاریخ چیست؟"
        )
        return
    
    loading_msg = update.message.reply_text("🤔 در حال فکر کردن...")
    
    try:
        ai_response = get_ai_response(user_message)
        
        if ai_response:
            # اگه پاسخ خیلی طولانی بود، به چند بخش تقسیم کن
            if len(ai_response) > 4000:
                parts = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)]
                loading_msg.edit_text(f"🤖 پاسخ هوش مصنوعی (بخش ۱ از {len(parts)}):\n\n{parts[0]}")
                for i, part in enumerate(parts[1:], 2):
                    update.message.reply_text(f"🤖 پاسخ هوش مصنوعی (بخش {i} از {len(parts)}):\n\n{part}")
            else:
                loading_msg.edit_text(f"🤖 پاسخ هوش مصنوعی:\n\n{ai
