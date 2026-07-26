import asyncio
from telethon import TelegramClient

# اطلاعات API رو از config بگیر
try:
    import config
    API_ID = config.API_ID
    API_HASH = config.API_HASH
except:
    API_ID = 2040
    API_HASH = "b18441a1ff607e10a989891a5462e627"

async def main():
    print("🔑 در حال ساخت نشست...")
    
    client = TelegramClient('session', API_ID, API_HASH)
    
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
