import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه - روش مستقیم و ساده"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []
            
        print(f"✅ فایل نشست پیدا شد.")
        
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        
        async with client:
            await client.start()
            
            # ===== دریافت مستقیم گروه با chat_id =====
            try:
                # روش مستقیم با chat_id
                entity = await client.get_entity(chat_id)
                print(f"✅ گروه با شناسه {chat_id} پیدا شد.")
            except Exception as e:
                print(f"❌ خطا در دریافت گروه: {e}")
                return []
            
            # ===== دریافت اعضا =====
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
