import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def get_all_members(chat_id):
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست پیدا نشد!")
            return []

        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        await client.start()

        # گرفتن entity گروه
        entity = await client.get_entity(chat_id)
        if entity is None:
            print("❌ گروه پیدا نشد.")
            return []

        # دریافت تعداد کل اعضا
        full_channel = await client.get_entity(chat_id)
        total = full_channel.participants_count if hasattr(full_channel, 'participants_count') else "نامشخص"
        print(f"📊 تعداد کل اعضا: {total}")

        members = []
        offset = 0
        limit = 200  # حداکثر ۲۰۰ برای سرعت بیشتر

        while True:
            try:
                participants = await client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=limit,
                    hash=0
                ))

                if not participants.users:
                    break

                for user in participants.users:
                    if not user.bot:
                        members.append({
                            "id": user.id,
                            "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون نام",
                            "username": user.username or "ندارد"
                        })

                offset += limit
                print(f"📊 تاکنون {len(members)} عضو دریافت شد...")

                if len(participants.users) < limit:
                    break

            except errors.FloodWaitError as e:
                print(f"⏳ صبر کن {e.seconds} ثانیه...")
                await asyncio.sleep(e.seconds + 1)
            except Exception as e:
                print(f"⚠️ خطا: {e}")
                break

        print(f"✅ {len(members)} عضو پیدا شد.")
        return members

    except Exception as e:
        print(f"❌ خطا: {e}")
        return []
