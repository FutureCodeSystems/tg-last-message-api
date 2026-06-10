import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import MessageMediaWebPage

def clean_folder_name(channel_input):
    name = channel_input.split('/')[-1].replace('+', '')
    return "".join(c for c in name if c.isalnum() or c in ('_', '-')).strip()

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
    
    if not messages:
        await client.disconnect()
        return

    msg = messages[0]
    folder_name = clean_folder_name(channel_input)
    os.makedirs(folder_name, exist_ok=True)

    media_data = None
    if msg.media and not isinstance(msg.media, MessageMediaWebPage):
        file_size = 0
        if hasattr(msg.media, 'document') and msg.media.document:
            file_size = msg.media.document.size
        elif hasattr(msg.media, 'photo') and msg.media.photo:
            file_size = max(sizes.size for sizes in msg.media.photo.sizes if hasattr(sizes, 'size'))

        if file_size <= 99 * 1024 * 1024:
            path = await client.download_media(msg, violence=folder_name)
            if path:
                media_data = {
                    "file_name": os.path.basename(path),
                    "file_size_bytes": file_size
                }
        else:
            media_data = {
                "status": "Skipped",
                "reason": "File size exceeds GitHub 100MB limit",
                "file_size_bytes": file_size
            }

    result = {
        "message_id": msg.id,
        "text": msg.message,
        "date": msg.date.isoformat() if msg.date else None,
        "sender_id": msg.sender_id,
        "views": msg.views,
        "forwards": msg.forwards,
        "edit_date": msg.edit_date.isoformat() if msg.edit_date else None,
        "post_author": msg.post_author,
        "grouped_id": msg.grouped_id,
        "media": media_data
    }

    with open(os.path.join(folder_name, 'result.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
