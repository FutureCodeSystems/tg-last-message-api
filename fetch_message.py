import os
import json
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import MessageMediaWebPage


def clean_folder_name(channel_input):
    name = channel_input.split('/')[-1].replace('+', '')
    return "".join(c for c in name if c.isalnum() or c in ('_', '-')).strip()


def get_media_size(msg):
    """اندازه فایل media رو برمی‌گردونه (بایت). اگه نداشت 0."""
    if not msg.media or isinstance(msg.media, MessageMediaWebPage):
        return 0
    if hasattr(msg.media, 'document') and msg.media.document:
        return msg.media.document.size
    if hasattr(msg.media, 'photo') and msg.media.photo:
        sizes = [s.size for s in msg.media.photo.sizes if hasattr(s, 'size')]
        return max(sizes) if sizes else 0
    return 0


def serialize_message(msg):
    """یک پیام تلگرام رو به dict ساده تبدیل می‌کنه (بدون media سنگین)."""
    size = get_media_size(msg)
    has_real_media = bool(msg.media) and not isinstance(msg.media, MessageMediaWebPage)
    
    return {
        "message_id": msg.id,
        "text": msg.message or "",
        "date": msg.date.isoformat() if msg.date else None,
        "sender_id": msg.sender_id,
        "views": msg.views,
        "forwards": msg.forwards,
        "edit_date": msg.edit_date.isoformat() if msg.edit_date else None,
        "post_author": msg.post_author,
        "grouped_id": msg.grouped_id,
        "media": {
            "file_name": None,
            "file_size_bytes": size,
            "pending": has_real_media
        } if has_real_media else None
    }


async def download_one(client, msg, folder_name):
    """media یک پیام رو دانلود می‌کنه. اگه > 99MB باشه، Skipped برمی‌گردونه."""
    size = get_media_size(msg)
    
    if size > 99 * 1024 * 1024:
        return {
            "status": "Skipped",
            "reason": "File size exceeds GitHub 100MB limit",
            "file_size_bytes": size,
            "file_name": None
        }
    
    try:
        path = await client.download_media(msg, file=folder_name)
        if path:
            return {
                "file_name": os.path.basename(path),
                "file_size_bytes": size
            }
    except Exception as e:
        return {
            "status": "Error",
            "reason": f"Download failed: {str(e)[:200]}",
            "file_size_bytes": size,
            "file_name": None
        }
    
    return None


async def main():
    api_id = int(os.environ['API_ID'])
    api_hash = os.environ['API_HASH']
    session_string = os.environ['SESSION_STRING']
    channel_input = os.environ['CHANNEL']
    
    # LIMIT اختیاریه — default = 5 (می‌خوای 1 کنی یا 50، بعداً عوضش کن)
    raw_limit = os.environ.get('LIMIT', '5')
    try:
        limit = max(1, min(50, int(raw_limit)))
    except ValueError:
        limit = 5

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()

    # جوین کانال (بی‌صدا، اگه قبلاً عضو بودیم)
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
    messages = await client.get_messages(entity, limit=limit)
    
    if not messages:
        await client.disconnect()
        return

    folder_name = clean_folder_name(channel_input)
    os.makedirs(folder_name, exist_ok=True)

    posts = []
    for msg in messages:
        post = serialize_message(msg)
        # دانلود media (اگه داشت و هنوز دانلود نشده)
        if post["media"] and post["media"].get("pending"):
            downloaded = await download_one(client, msg, folder_name)
            if downloaded:
                post["media"] = downloaded
        posts.append(post)

    result = {
        "channel": channel_input,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(posts),
        "limit": limit,
        "posts": posts
    }

    with open(os.path.join(folder_name, 'result.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
