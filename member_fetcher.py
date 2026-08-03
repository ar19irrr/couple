import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه با Telethon - بدون نیاز به لینک"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []
            
        print(f"✅ فایل نشست در مسیر {SESSION_FILE} پیدا شد.")
        
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        
        async with client:
            await client.start()
            
            # ===== مرحله ۱: دریافت دیالوگ‌ها (لیست همه گروه‌ها) =====
            print("🔄 در حال دریافت لیست گروه‌ها...")
            dialogs = await client.get_dialogs()
            print(f"✅ {len(dialogs)} گروه/چت پیدا شد.")
            
            # پیدا کردن گروه در دیالوگ‌ها
            entity = None
            for dialog in dialogs:
                if dialog.is_group and dialog.id == chat_id:
                    entity = dialog.entity
                    print(f"✅ گروه '{dialog.name}' در دیالوگ‌ها پیدا شد.")
                    break
            
            # ===== مرحله ۲: اگر گروه در دیالوگ‌ها نبود، مستقیم دریافتش کن =====
            if entity is None:
                print(f"⚠️ گروه {chat_id} در دیالوگ‌ها پیدا نشد. تلاش برای دریافت مستقیم...")
                try:
                    entity = await client.get_entity(chat_id)
                    print(f"✅ گروه با شناسه {chat_id} پیدا شد.")
                except Exception as e:
                    print(f"❌ خطا در دریافت گروه: {e}")
                    return []
            
            if entity is None:
                print(f"❌ گروه با شناسه {chat_id} یافت نشد.")
                return []

            # ===== مرحله ۳: دریافت اعضا =====
            members = []
            offset = 0
            limit = 200
            
            print(f"⏳ در حال دریافت اعضای گروه...")
            
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
                    print(f"📊 تاکنون {len(members)} عضو دریافت شد...")
                    
                    if len(participants.users) < limit:
                        break
                        
                except asyncio.TimeoutError:
                    print(f"⚠️ Timeout. تلاش مجدد...")
                    continue
                except errors.FloodWaitError as e:
                    wait_time = e.seconds + 1
                    print(f"⏳ محدودیت سرعت. {wait_time} ثانیه صبر کنید...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    print(f"❌ خطا در دریافت اعضا: {e}")
                    break
            
            print(f"✅ {len(members)} عضو پیدا شد.")
            return members
            
    except errors.rpcerrorlist.ApiIdInvalidError:
        print("❌ خطا: API_ID یا API_HASH نامعتبر است.")
        return []
    except FileNotFoundError:
        print(f"❌ فایل نشست {SESSION_FILE} وجود ندارد!")
        return []
    except Exception as e:
        print(f"❌ خطای کلی: {e}")
        return []
