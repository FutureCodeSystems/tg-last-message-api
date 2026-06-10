import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest

async def main():
    api_id = int(os.environ['API_ID'])
    api_hash = os.environ['API_HASH']
    session_string = os.environ['SESSION_STRING']
    channel_input = os.environ['CHANNEL']

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()

    if 'joinchat/' in channel_input or '+' in channel_input:
        invite_hash = channel_input.split('/')[-1].replace('+', '')
        try:
            await client(ImportChatInviteRequest(invite_hash))
        except Exception:
            pass
    else:
        try:
            await client(JoinChannelRequest(channel_input))
        except Exception:
            pass

    entity = await client.get_entity(channel_input)
    messages = await client.get_messages(entity, limit=1)
    
    result = {}
    if messages:
        msg = messages[0]
        result = {
            "id": msg.id,
            "text": msg.message,
            "date": msg.date.isoformat() if msg.date else None
        }

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
