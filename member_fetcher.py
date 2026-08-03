import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest, JoinChannelRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

# ==================== لینک‌های دعوت گروه‌ها ====================
# برای هر گروه جدید، لینک دعوت رو اینجا اضافه کن
INVITE_LINKS = {
    -1001290218006: "https://t.me/joinchat/AAAAAAAAAAAAAAAAAAAA",  # لینک گروه اول
    -1001429243657: "https://t.me/+SFfoan-FMMBmN2Y0",  # لینک گروه دوم
}

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه - با پشتیبانی از لینک دعوت"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []
            
        print(f"✅ فایل نشست پیدا شد.")
        
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        
        async with client:
            await client.start()
            
            # ===== مرحله ۱: دریافت گروه =====
            entity = None
            
            # روش ۱: تلاش با chat_id مستقیم
            try:
                entity = await client.get_entity(chat_id)
                print(f"✅ گروه با شناسه {chat_id} پیدا شد.")
            except Exception as e:
                print(f"⚠️ دریافت مستقیم خطا داد: {e}")
                
                # روش ۲: استفاده از لینک دعوت
                invite_link = INVITE_LINKS.get(chat_id)
                if invite_link:
                    try:
                        print(f"🔄 تلاش با لینک دعوت: {invite_link}")
                        entity = await client.get_entity(invite_link)
                        print(f"✅ گروه با لینک دعوت پیدا شد.")
                        
                        # ذخیره گروه در نشست برای دفعات بعد
                        await client.get_input_entity(entity)
                        
                    except Exception as e2:
                        print(f"❌ خطا در دریافت با لینک: {e2}")
                else:
                    print(f"❌ لینک دعوتی برای گروه {chat_id} پیدا نشد!")
                    print(f"⚠️ لطفاً لینک دعوت گروه رو به INVITE_LINKS اضافه کن.")
                    return []
            
            if entity is None:
                print(f"❌ گروه پیدا نشد!")
                return []

            # ===== مرحله ۲: دریافت اعضا =====
            members = []
            offset = 0
            limit = 200
            
            print(f"⏳ در حال دریافت اعضا...")
            
            while True:
                try:
                    participants = await asyncio.wait_for(
                        client(GetParticipantsRequest(
                            channel=entity,
                            filter=ChannelParticipantsSearch(''),
                            offset=offset,
                            limit=limit,
                            hash=0
                        )),
                        timeout=60
                    )
                    
                    if not participants or not participants.users:
                        break
                        
                    for user in participants.users:
                        if not user.bot:
                            members.append({
                                "id": user.id,
                                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون نام",
                                "username": user.username or "ندارد"
                            })
                    
                    offset += limit
                    print(f"📊 {len(members)} عضو دریافت شد...")
                    
                    if len(participants.users) < limit:
                        break
                        
                except errors.FloodWaitError as e:
                    print(f"⏳ محدودیت سرعت. {e.seconds} ثانیه صبر کنید...")
                    await asyncio.sleep(e.seconds + 1)
                except Exception as e:
                    print(f"❌ خطا: {e}")
                    break
            
            print(f"✅ {len(members)} عضو پیدا شد.")
            return members
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        return []
