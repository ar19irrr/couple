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
    update_monthly_score, get_all_monthly_scores, reset_monthly_scores
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

# ==================== هوش مصنوعی (OpenRouter) ====================
def get_ai_response(prompt):
    """دریافت پاسخ از هوش مصنوعی با OpenRouter"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1"
        )
        
        if not os.environ.get("OPENROUTER_API_KEY"):
            return None
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-v4-flash:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطا در AI: {e}")
        return None

# ==================== دستورات ====================
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        """🤖 ربات زوج‌یاب پیشرفته با هوش مصنوعی

📌 **دستورات جدید:**
/ask <سوال> - پرسش سوال از هوش مصنوعی 🧠

📌 **دستورات اصلی:**
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

✨ **امکانات ویژه:**
• انتخاب زوج بر اساس جنسیت و علایق
• فال روزانه
• سیستم امتیازدهی ماهانه
• **پرسش و پاسخ با هوش مصنوعی** 🧠

⚠️ نکته: ربات باید ادمین باشد و VPN روشن باشد.""",
        parse_mode="Markdown"
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

# ==================== انتخاب زوج ====================
def couple_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🔄 در حال انتخاب زوج...")
    
    members = get_members(chat_id)
    if not members:
        update.message.reply_text("❌ لیست اعضا خالی است. ابتدا /update را بزنید.")
        return
    
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
    
    if len(available_members) < 2:
        update.message.reply_text(
            f"❌ تعداد اعضای قابل انتخاب کافی نیست.\n🔹 کل اعضا: {len(members)}\n🔹 در لیست سیاه: {len(blocked)}"
        )
        return
    
    # فیلتر بر اساس علاقه
    user_interest = user_profile.get("interest")
    if user_interest:
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
    
    msg = "🏆 **برترین لاورهای ماه**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    if sorted_users:
        for i, (user_id, score) in enumerate(sorted_users[:10]):
            user_info = user_map.get(int(user_id), {"name": f"کاربر ناشناس", "username": "ندارد"})
            medal = medals[i] if i < len(medals) else f"{i+1}."
            msg += f"{medal} {user_info['name']} (@{user_info['username']}) — {score} بار\n"
    else:
        msg += "📭 هنوز کسی امتیازی کسب نکرده!"
    
    update.message.reply_text(msg, parse_mode="Markdown")

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
            msg = f"🌟 **برنده لاورهای ماه** 🌟\n\n"
            msg += f"👤 {top_user['name']} با {top_score} بار لاور شدن!\n\n"
            msg += f"💬 پیام ویژه:\n{ai_message}"
        else:
            msg = f"🌟 **برنده لاورهای ماه** 🌟\n\n"
            msg += f"👤 {top_user['name']} با {top_score} بار لاور شدن!\n"
            msg += "🎉 تبریک میگم! تو بهترین لاوری! ❤️"
    except Exception as e:
        logger.error(f"❌ خطا در AI: {e}")
        msg = f"🌟 **برنده لاورهای ماه** 🌟\n\n"
        msg += f"👤 {top_user['name']} با {top_score} بار لاور شدن!\n"
        msg += "🎉 تبریک میگم! تو بهترین لاوری! ❤️"
    
    bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
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
            "مثال: `/ask بهترین فیلم تاریخ چیست؟`",
            parse_mode="Markdown"
        )
        return
    
    loading_msg = update.message.reply_text("🤔 در حال فکر کردن...")
    
    try:
        ai_response = get_ai_response(user_message)
        
        if ai_response:
            loading_msg.edit_text(f"🤖 **پاسخ هوش مصنوعی:**\n\n{ai_response}", parse_mode="Markdown")
        else:
            loading_msg.edit_text("❌ خطا در ارتباط با هوش مصنوعی. لطفاً دوباره تلاش کنید.")
            
    except Exception as e:
        logger.error(f"❌ خطا در /ask: {e}")
        loading_msg.edit_text("❌ خطایی رخ داد. لطفاً بعداً تلاش کنید.")

# ==================== بقیه دستورات ====================
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
        update.message.reply_text("✅ این گروه به لیست گروه‌های فعال اضافه شد.")
        members = update_members_sync(chat_id)
        if members:
            update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
        else:
            update.message.reply_text("❌ خطا در دریافت اعضا. لطفاً VPN را روشن کنید و ربات را ادمین کنید.")
    else:
        update.message.reply_text(f"ℹ️ این گروه قبلاً به لیست اضافه شده است.")

def update_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🔄 در حال به‌روزرسانی لیست همه اعضا... (چند لحظه)")
    
    members = update_members_sync(chat_id)
    if members:
        update.message.reply_text(f"✅ {len(members)} عضو پیدا شد و ذخیره گردید.")
    else:
        update.message.reply_text("❌ خطا در دریافت اعضا. لطفاً VPN را روشن کنید و ربات را ادمین کنید.")

def last_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    last = get_last_couple(chat_id)
    
    if last and isinstance(last, dict):
        u1 = last.get("user1", {})
        u2 = last.get("user2", {})
        date = last.get("date", "")[:10]
        update.message.reply_text(
            f"""📅 آخرین زوج ({date})

👤 {u1.get('name', 'نامشخص')}
یوزرنیم: @{u1.get('username', 'ندارد')}
❤️ با ❤️
👤 {u2.get('name', 'نامشخص')}
یوزرنیم: @{u2.get('username', 'ندارد')}"""
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
            msg += f"{i}. {u1.get('name', 'نامشخص')} ❤️ {u2.get('name', 'نامشخص')} ({date})\n"
    
    update.message.reply_text(msg)

def stats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    stats = get_stats(chat_id)
    
    msg = f"📊 **آمار کلی گروه:**\n\n"
    msg += f"👥 تعداد اعضا: {stats['total_members']} نفر\n"
    msg += f"💞 تعداد زوج‌ها: {stats['total_couples']} بار\n"
    msg += f"🌟 کاربران منحصر‌به‌فرد: {stats['unique_users']} نفر\n"
    
    if stats.get('last_couple') and isinstance(stats['last_couple'], dict):
        u1 = stats['last_couple'].get('user1', {})
        u2 = stats['last_couple'].get('user2', {})
        msg += f"\n💖 آخرین زوج:\n👤 {u1.get('name', 'نامشخص')} ❤️ {u2.get('name', 'نامشخص')}"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def mystats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "کاربر"
    
    total_couples = get_user_total_couples(chat_id, user_id)
    partner_stats = get_user_couple_stats(chat_id, user_id)
    
    msg = f"📊 **آمار شخصی {user_name}**\n\n"
    msg += f"💞 تعداد کل لاورها: {total_couples} بار\n"
    
    if partner_stats:
        msg += f"\n👥 **شریک‌های لاور:**\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, partner in enumerate(partner_stats[:5]):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            msg += f"{medal} {partner['name']} (@{partner['username']}) — {partner['count']} بار\n"
        
        if len(partner_stats) > 5:
            msg += f"\nو {len(partner_stats) - 5} نفر دیگر..."
    else:
        msg += f"\n📭 هنوز با کسی لاور نشدی!"
    
    update.message.reply_text(msg, parse_mode="Markdown")

def reset_command(update: Update, context: CallbackContext):
    clear_data()
    update.message.reply_text("✅ دیتابیس با موفقیت ریست شد.")

# ==================== AI Message Handler (اصلاح شده) ====================
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
    """مدیریت پیام‌های هوشمند با بررسی وجود پیام"""
    try:
        # بررسی اینکه پیام وجود داره
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

👤 {user1['name']}
یوزرنیم: @{user1['username']}
❤️ با ❤️
👤 {user2['name']}
یوزرنیم: @{user2['username']}

{random.choice(CELEBRATION_MESSAGES)}

🌟 فال امروز: {fortune}"""
    
    bot.send_message(chat_id=chat_id, text=msg)
    clear_blocked_users(chat_id)
    logger.info(f"✅ زوج روزانه انتخاب شد برای گروه {chat_id}")

# ==================== زمان‌بندی ====================
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
    
    # دستورات
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("ask", ask_command))
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
    
    # Callback و Message Handler
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_ai_message))
    
    # زمان‌بندی‌ها
    schedule_daily_jobs(dp)
    schedule_monthly_announcement(dp)
    
    logger.info("🚀 ربات شروع به کار کرد...")
    updater.start_polling(drop_pending_updates=True, timeout=30)
    updater.idle()

if __name__ == "__main__":
    main()
