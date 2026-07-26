import asyncio
from telethon import TelegramClient
import config

async def main():
    print("🔑 در حال ساخت نشست...")
    client = TelegramClient('session', config.API_ID, config.API_HASH)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ نشست با موفقیت ساخته شد!")
        print(f"👤 کاربر: {me.first_name} (ID: {me.id})")
    except Exception as e:
        print(f"❌ خطا: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
