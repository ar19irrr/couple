import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def save_entity_to_session(client, chat_id):
    """گروه جدید را به فایل نشست اضافه می‌کند تا access_hash آن ذخیره شود."""
    try:
        # دریافت مستقیم گروه با chat_id
        entity = await client.get_entity(chat_id)
        # این خط باعث می‌شود که entity در فایل نشست ذخیره شود
        await client.get_input_entity(entity)
        print(f"✅ گروه {chat_id} با موفقیت در نشست ذخیره شد.")
        return entity
    except Exception as e:
        print(f"⚠️ خطا در ذخیره گروه در نشست: {e}")
        return None

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه - با ذخیره فعال گروه در نشست"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []
            
        print(f"✅ فایل نشست پیدا شد.")
        
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        
        async with client:
            await client.start()
            
            # ===== مرحله ۱: ذخیره فعال گروه در نشست =====
            # این کار باعث می‌شود که access_hash گروه جدید در فایل نشست ثبت شود
            entity = await save_entity_to_session(client, chat_id)
            if entity is None:
                # اگر روش مستقیم کار نکرد، از دیالوگ‌ها استفاده کن
                print("🔄 تلاش برای پیدا کردن گروه در دیالوگ‌ها...")
                dialogs = await client.get_dialogs()
                for dialog in dialogs:
                    if dialog.is_group and dialog.id == chat_id:
                        entity = dialog.entity
                        # ذخیره در نشست
                        await client.get_input_entity(entity)
                        print(f"✅ گروه {chat_id} از دیالوگ‌ها در نشست ذخیره شد.")
                        break
                
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
