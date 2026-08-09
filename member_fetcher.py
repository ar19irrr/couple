import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

# لینک‌های دعوت گروه‌ها (در صورت نیاز)
INVITE_LINKS = {
    -1001290218006: "https://t.me/+SFfoan-FMMBmN2Y0",
    -1001510907324: "https://t.me/+6TVF2Q1du4FmNmRk",
}

async def get_all_members(chat_id):
    """دریافت همه اعضای ممکن از گروه با pagination صحیح و مدیریت FloodWait"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []

        print(f"✅ فایل نشست پیدا شد.")
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)

        async with client:
            await client.start()

            # ===== دریافت entity گروه =====
            entity = None
            try:
                entity = await client.get_entity(chat_id)
                print(f"✅ گروه با شناسه {chat_id} پیدا شد.")
            except Exception as e:
                print(f"⚠️ دریافت مستقیم خطا داد: {e}")
                invite_link = INVITE_LINKS.get(chat_id)
                if invite_link:
                    try:
                        print(f"🔄 تلاش با لینک دعوت...")
                        entity = await client.get_entity(invite_link)
                        print(f"✅ گروه با لینک دعوت پیدا شد.")
                    except Exception as e2:
                        print(f"❌ خطا در دریافت با لینک: {e2}")
                        return []
                else:
                    print(f"❌ لینک دعوتی برای گروه {chat_id} تعریف نشده.")
                    return []

            if entity is None:
                print("❌ گروه پیدا نشد!")
                return []

            # ===== دریافت اعضا با pagination صحیح =====
            members = []
            offset = 0
            limit = 200
            max_empty = 3          # اگر چند بار پشت‌سرهم خالی برگشت، تمام کن
            empty_count = 0

            print(f"⏳ در حال دریافت اعضا از گروه {chat_id}...")

            while True:
                try:
                    participants = await client(GetParticipantsRequest(
                        channel=entity,
                        filter=ChannelParticipantsSearch(''),
                        offset=offset,
                        limit=limit,
                        hash=0
                    ))

                    if not participants or not participants.users:
                        empty_count += 1
                        if empty_count >= max_empty:
                            break
                        offset += limit
                        continue

                    empty_count = 0  # ریست کردن شمارنده

                    new_users = 0
                    for user in participants.users:
                        if user.bot:
                            continue
                        members.append({
                            "id": user.id,
                            "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون نام",
                            "username": user.username or "ندارد"
                        })
                        new_users += 1

                    # ===== مهم‌ترین اصلاح =====
                    offset += len(participants.users)

                    print(f"📊 {len(members)} عضو دریافت شد (این صفحه: {new_users})")

                    # اگر کمتر از limit برگشت، احتمالاً تمام شده
                    if len(participants.users) < limit:
                        break

                    # تأخیر برای جلوگیری از FloodWait
                    await asyncio.sleep(1.8)

                except errors.FloodWaitError as e:
                    wait = e.seconds + 3
                    print(f"⏳ FloodWait! {wait} ثانیه صبر می‌کنم...")
                    await asyncio.sleep(wait)
                    continue

                except Exception as e:
                    print(f"❌ خطا در دریافت صفحه: {e}")
                    break

            # حذف تکراری‌ها
            unique = {m["id"]: m for m in members}
            final_members = list(unique.values())

            print(f"✅ در مجموع {len(final_members)} عضو یکتا پیدا شد.")
            return final_members

    except Exception as e:
        print(f"❌ خطای کلی: {e}")
        return []
