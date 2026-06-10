from telethon import TelegramClient
from telethon.sessions import StringSession
import json
import os

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session = os.environ["SESSION_STRING"]

channel = os.environ["CHANNEL"]

client = TelegramClient(StringSession(session), api_id, api_hash)

async def main():
    async for msg in client.iter_messages(channel, limit=1):
        data = {
            "text": msg.text,
            "id": msg.id,
            "date": str(msg.date)
        }

        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

with client:
    client.loop.run_until_complete(main())
