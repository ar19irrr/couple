import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config
import time

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه با Telethon - بهینه برای گروه‌های بزرگ"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []
            
        print(f"✅ فایل نشست در مسیر {SESSION_FILE} پیدا شد.")
        
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        
        async with client:
            await client.start()
            
            # ====== مرحله ۱: دریافت دیالوگ‌ها ======
            print("🔄 در حال دریافت دیالوگ‌ها...")
            dialogs = await client.get_dialogs()
            print(f"✅ {len(dialogs)} دیالوگ دریافت شد.")
            
            # پیدا کردن گروه در دیالوگ‌ها
            entity = None
            for dialog in dialogs:
                if dialog.is_group and dialog.id == chat_id:
                    entity = dialog.entity
                    print(f"✅ گروه {dialog.name} در دیالوگ‌ها پیدا شد.")
                    break
            
            # ====== مرحله ۲: اگر گروه در دیالوگ نبود، با لینک دعوت ======
            if entity is None:
                print(f"⚠️ گروه {chat_id} در دیالوگ‌ها پیدا نشد.")
                
                # لینک دعوت گروه رو اینجا بذار
                invite_link = "https://t.me/+SFfoan-FMMBmN2Y0"  # <--- عوض کن
                
                print(f"🔄 تلاش برای دریافت گروه با لینک دعوت: {invite_link}")
                try:
                    entity = await client.get_entity(invite_link)
                    print(f"✅ گروه با لینک دعوت پیدا شد.")
                except Exception as e:
                    print(f"❌ خطا در دریافت گروه با لینک دعوت: {e}")
                    return []
            
            # ====== مرحله ۳: دریافت اعضا (بهینه برای گروه‌های بزرگ) ======
            members = []
            offset = 0
            limit = 200  # افزایش به ۲۰۰ برای سرعت بیشتر
            total_members = 0
            
            # دریافت تعداد کل اعضا
            try:
                full_channel = await client.get_entity(chat_id)
                if hasattr(full_channel, 'participants_count'):
                    total_members = full_channel.participants_count
                    print(f"📊 تعداد کل اعضای گروه: {total_members}")
            except:
                total_members = None
            
            print(f"⏳ در حال دریافت اعضای گروه... (این کار ممکن است چند دقیقه طول بکشد)")
            
            while True:
                try:
                    start_time = time.time()
                    
                    participants = await asyncio.wait_for(
                        client(GetParticipantsRequest(
                            channel=entity,
                            filter=ChannelParticipantsSearch(''),
                            offset=offset,
                            limit=limit,
                            hash=0
                        )),
                        timeout=60  # افزایش timeout برای گروه‌های بزرگ
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
                    elapsed = time.time() - start_time
                    print(f"📊 {len(members)}/{total_members if total_members else '?'} عضو دریافت شد... (زمان: {elapsed:.1f}s)")
                    
                    # ====== تاخیر هوشمند برای جلوگیری از محدودیت ======
                    if len(participants.users) == limit:
                        await asyncio.sleep(0.5)  # تاخیر ۰.۵ ثانیه‌ای بین درخواست‌ها
                    
                    if len(participants.users) < limit:
                        break
                        
                except asyncio.TimeoutError:
                    print(f"⚠️ Timeout در دریافت اعضا. تلاش مجدد...")
                    continue
                except errors.FloodWaitError as e:
                    wait_time = e.seconds + 1
                    print(f"⏳ محدودیت سرعت تلگرام. {wait_time} ثانیه صبر کنید...")
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
        print(f"❌ خطای کلی در دریافت اعضا: {e}")
        return []
