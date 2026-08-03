import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config
import random

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه با Telethon - مدیریت کامل Flood Wait"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []
            
        print(f"✅ فایل نشست در مسیر {SESSION_FILE} پیدا شد.")
        
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        
        async with client:
            await client.start()
            
            # ===== دریافت گروه با مدیریت Flood Wait =====
            entity = None
            
            # روش ۱: دریافت مستقیم
            try:
                entity = await client.get_entity(chat_id)
                print(f"✅ گروه با شناسه {chat_id} پیدا شد.")
            except Exception as e:
                print(f"⚠️ دریافت مستقیم خطا داد: {e}")
                
                # روش ۲: دریافت دیالوگ‌ها با مدیریت Flood Wait
                try:
                    print("🔄 در حال دریافت لیست گروه‌ها (با مدیریت محدودیت)...")
                    dialogs = await client.get_dialogs()
                    print(f"✅ {len(dialogs)} گروه/چت پیدا شد.")
                    
                    for dialog in dialogs:
                        if dialog.is_group and dialog.id == chat_id:
                            entity = dialog.entity
                            print(f"✅ گروه '{dialog.name}' در دیالوگ‌ها پیدا شد.")
                            break
                            
                except errors.FloodWaitError as e:
                    wait_time = e.seconds + random.randint(1, 5)
                    print(f"⏳ محدودیت سرعت. {wait_time} ثانیه صبر کنید...")
                    await asyncio.sleep(wait_time)
                    
                    # تلاش مجدد
                    try:
                        dialogs = await client.get_dialogs()
                        for dialog in dialogs:
                            if dialog.is_group and dialog.id == chat_id:
                                entity = dialog.entity
                                print(f"✅ گروه '{dialog.name}' در دیالوگ‌ها پیدا شد.")
                                break
                    except Exception as e2:
                        print(f"❌ تلاش مجدد خطا داد: {e2}")
                
                except Exception as e:
                    print(f"❌ خطا در دریافت دیالوگ‌ها: {e}")
            
            if entity is None:
                print(f"❌ گروه پیدا نشد!")
                return []

            # ===== دریافت اعضا با مدیریت Flood Wait =====
            members = []
            offset = 0
            limit = 200
            
            print(f"⏳ در حال دریافت همه اعضای گروه...")
            
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
                    wait_time = e.seconds + random.randint(1, 5)
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
