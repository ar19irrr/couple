import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import config
from database import set_members

async def get_all_members():
    try:
        client = TelegramClient('session', config.API_ID, config.API_HASH)
        await client.start()
        
        entity = await client.get_entity(config.GROUP_ID)
        
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
        
        set_members(members)
        print(f"✅ {len(members)} عضو پیدا شد")
        await client.disconnect()
        return members
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(get_all_members())