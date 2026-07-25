import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

async def get_all_members(chat_id):
    """دریافت همه اعضای یک گروه با Telethon با مدیریت صحیح اتصال"""
    client = TelegramClient('session', config.API_ID, config.API_HASH)
    try:
        # استفاده از async with برای مدیریت خودکار اتصال
        async with client:
            # اطمینان از اینکه client آماده است
            await client.start()
            
            # دریافت entity گروه
            entity = await client.get_entity(chat_id)
            if entity is None:
                print(f"❌ گروه با شناسه {chat_id} یافت نشد.")
                return []

            members = []
            offset = 0
            limit = 100
            
            while True:
                try:
                    # دریافت لیست اعضا با timeout
                    participants = await asyncio.wait_for(
                        client(GetParticipantsRequest(
                            channel=entity,
                            filter=ChannelParticipantsSearch(''),
                            offset=offset,
                            limit=limit,
                            hash=0
                        )),
                        timeout=30  # 30 ثانیه timeout
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
    except Exception as e:
        print(f"❌ خطای کلی در دریافت اعضا: {e}")
        return []

# تابع تست برای اجرای مستقل
async def main():
    # اینجا می‌توانید یک chat_id را برای تست وارد کنید
    chat_id = config.GROUP_ID  # در صورت نیاز متغیر GROUP_ID را در config تعریف کنید
    members = await get_all_members(chat_id)
    print(f"تعداد کل اعضا: {len(members)}")

if __name__ == "__main__":
    asyncio.run(main())
