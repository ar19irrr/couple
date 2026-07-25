import asyncio
from telethon import TelegramClient
import config

async def main():
    # یک کلاینت جدید با نام فایل نشست دلخواه بسازید
    client = TelegramClient('session', config.API_ID, config.API_HASH)
    
    # شروع به کار و درخواست ورود (این کار را در ترمینال خودتان انجام می‌دهید)
    await client.start()
    
    # پس از ورود موفق، نشست ذخیره می‌شود
    print("✅ نشست با موفقیت ساخته شد!")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())