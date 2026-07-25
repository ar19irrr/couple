from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config

async def get_all_members(chat_id):
    """دریافت همه اعضای یک گروه با Telethon"""
    try:
        client = TelegramClient('session', config.API_ID, config.API_HASH)
        await client.start()
        
        entity = await client.get_entity(chat_id)
        
        members = []
        offset = 0
        limit = 100
        
        while True:
            participants = await client(GetParticipantsRequest(
                channel=entity,
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=limit,
                hash=0
            ))
            
            if not participants.users:
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
        
        await client.disconnect()
        return members
        
    except Exception as e:
        print(f"❌ خطا در دریافت اعضا: {e}")
        return []
