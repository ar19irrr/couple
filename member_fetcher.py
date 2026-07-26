import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsAdmins
import config

# مسیر فایل نشست
SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.session')

async def get_all_members(chat_id):
    """دریافت همه اعضای گروه با استفاده از get_participants"""
    try:
        if not os.path.exists(SESSION_FILE):
            print(f"❌ فایل نشست در مسیر {SESSION_FILE} پیدا نشد!")
            return []
            
        print(f"✅ فایل نشست در مسیر {SESSION_FILE} پیدا شد.")
        
        client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
        
        async with client:
            await client.start()
            
            print("⏳ در حال دریافت اطلاعات گروه...")
            
            # دریافت اطلاعات کامل گروه
            try:
                entity = await client.get_entity(chat_id)
                if entity is None:
                    print(f"❌ گروه با شناسه {chat_id} یافت نشد.")
                    return []
                
                # دریافت اطلاعات کامل گروه (شامل تعداد اعضا)
                full_channel = await client(GetFullChannelRequest(entity))
                total_members = full_channel.full_chat.participants_count
                print(f"📊 تعداد کل اعضای گروه: {total_members}")
                
            except Exception as e:
                print(f"⚠️ خطا در دریافت اطلاعات گروه: {e}")
                total_members = None

            # دریافت لیست اعضا
            members = []
            offset = 0
            limit = 100  # حداکثر ۱۰۰ در هر درخواست
            
            print(f"⏳ در حال دریافت اعضای گروه {chat_id}...")
            
            while True:
                try:
                    # دریافت اعضا با offset
                    participants = await asyncio.wait_for(
                        client(GetParticipantsRequest(
                            channel=entity,
                            filter=ChannelParticipantsSearch(''),  # همه اعضا
                            offset=offset,
                            limit=limit,
                            hash=0
                        )),
                        timeout=60  # زمان بیشتر برای گروه‌های بزرگ
                    )
                    
                    if not participants or not participants.users:
                        break
                        
                    for user in participants.users:
                        if not user.bot:  # حذف ربات‌ها
                            members.append({
                                "id": user.id,
                                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون نام",
                                "username": user.username or "ندارد"
                            })
                    
                    offset += limit
                    print(f"📊 تاکنون {len(members)} عضو دریافت شد...")
                    
                    # اگر تعداد برگشتی کمتر از limit بود، به انتها رسیدیم
                    if len(participants.users) < limit:
                        break
                        
                except asyncio.TimeoutError:
                    print(f"⚠️ Timeout در دریافت اعضا برای گروه {chat_id}")
                    break
                except errors.FloodWaitError as e:
                    print(f"⏳ محدودیت سرعت تلگرام. {e.seconds} ثانیه صبر کنید...")
                    await asyncio.sleep(e.seconds + 1)
                except Exception as e:
                    print(f"❌ خطا در دریافت اعضا: {e}")
                    break
            
            print(f"✅ {len(members)} عضو برای گروه {chat_id} پیدا شد.")
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

# تابع تست برای اجرای مستقل
if __name__ == "__main__":
    async def test():
        # آیدی گروه خودت رو اینجا بذار
        chat_id = -1001393393400  # <--- این رو با آیدی گروه خودت عوض کن
        members = await get_all_members(chat_id)
        print(f"\n📊 تعداد کل اعضا: {len(members)}")
        print("\n📋 ۵ نفر اول:")
        for i, m in enumerate(members[:5], 1):
            print(f"  {i}. {m['name']} (@{m['username']})")
    
    asyncio.run(test())
