import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه با روش ترکیبی"""
    try:
        # ===== روش ۱: امتحان با Telethon =====
        if os.path.exists(SESSION_FILE):
            print(f"✅ فایل نشست پیدا شد. تلاش با Telethon...")
            
            client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
            
            async with client:
                await client.start()
                
                # دریافت دیالوگ‌ها
                dialogs = await client.get_dialogs()
                
                # پیدا کردن گروه
                entity = None
                for dialog in dialogs:
                    if dialog.is_group and dialog.id == chat_id:
                        entity = dialog.entity
                        print(f"✅ گروه '{dialog.name}' پیدا شد.")
                        break
                
                if entity is None:
                    print(f"⚠️ گروه در دیالوگ‌ها پیدا نشد.")
                    try:
                        entity = await client.get_entity(chat_id)
                        print(f"✅ گروه با شناسه {chat_id} پیدا شد.")
                    except:
                        print(f"❌ گروه پیدا نشد!")
                        return []
                
                # دریافت اعضا
                members = []
                offset = 0
                limit = 200
                
                print(f"⏳ در حال دریافت اعضا...")
                
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
                
                if members:
                    print(f"✅ {len(members)} عضو با Telethon پیدا شد.")
                    return members
        
        # ===== روش ۲: اگر Telethon کار نکرد، از روش جایگزین استفاده کن =====
        print("🔄 Telethon کار نکرد. استفاده از روش جایگزین...")
        print("⚠️ روش جایگزین فقط ادمین‌ها رو برمی‌گردونه")
        
        # اینجا می‌تونی از روش get_chat_members استفاده کنی
        # ولی فعلاً خالی برمی‌گردونیم
        
        return []
            
    except Exception as e:
        print(f"❌ خطای کلی: {e}")
        return []
