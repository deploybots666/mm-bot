import os
import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditPhotoRequest,
    EditAdminRequest
)
from telethon.tl.functions.messages import ExportChatInviteRequest, EditChatAboutRequest
from telethon.tl.types import ChatAdminRights, InputChatUploadedPhoto

# --- ALT account credentials ---
api_id = 26532035
api_hash = 'f43d15238cf4775858955b03d5b74387'
session_name = 'alanmmd'
MAIN_USER_ID = 5045853109
GROUP_PHOTO_PATH = 'group.jpeg'

# --- Cleanup old session files ---
for file in os.listdir():
    if file.startswith(session_name) and file.endswith(('.session', '.session-journal', '.session-wal', '.session-shm')):
        os.remove(file)
        print(f"Deleted old session file: {file}")

# --- Start client ---
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(from_users=MAIN_USER_ID, pattern=r'^\.mm$'))
async def create_group(event):
    print("Received .mm command")
    try:
        result = await client(CreateChannelRequest(
            title="MM Group",
            about="",
            megagroup=True
        ))
        group = result.chats[0]
        chat = await client.get_input_entity(group.id)

        for attempt in range(6):
            try:
                uploaded_photo = await client.upload_file(GROUP_PHOTO_PATH)
                photo = InputChatUploadedPhoto(uploaded_photo)
                await client(EditPhotoRequest(channel=chat, photo=photo))
                break
            except Exception as e:
                print(f"Telegram is having internal issues {e}")
                await asyncio.sleep(5)
                if attempt == 5:
                    print("[Photo Error] Request was unsuccessful 6 time(s)")

        await client(EditChatAboutRequest(
            peer=chat,
            about="Always make sure that you’re dealing via @alans, not an impersonator"
        ))

        await client(EditAdminRequest(
            channel=chat,
            user_id=MAIN_USER_ID,
            admin_rights=ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=True,
                manage_call=True,
                other=True,
                anonymous=False
            ),
            rank="Middleman"
        ))

        msg = await client.send_message(group.id,
            "**Hey. Please state the terms of the deal:**\n\n"
            "• What is the deal?\n"
            "• Who is the buyer/seller?\n"
            "• What is the agreed price and which crypto?\n"
            "• Include any other relevant information."
        )

        try:
            await msg.pin()
        except Exception as e:
            print(f"[PIN ERROR] {e}")

        invite = await client(ExportChatInviteRequest(peer=chat))
        await event.respond(f"Share this invite with the other party:\n{invite.link}")

    except Exception as e:
        await event.respond(f"❌ Error: {e}")
        print(f"[CREATE ERROR] {e}")

@client.on(events.NewMessage(pattern=r'^\.del$'))
async def delete_group(event):
    try:
        chat = await event.get_chat()
        await event.delete()

        await client.send_message(chat.id,
            "⚠️ This group will be deleted in 30 minutes. Please save anything important."
        )

        await client(functions.messages.EditChatDefaultBannedRightsRequest(
            peer=chat.id,
            banned_rights=types.ChatBannedRights(
                until_date=None,
                send_messages=True
            )
        ))

        await asyncio.sleep(1800)
        await client(functions.messages.DeleteChatUserRequest(
            chat_id=chat.id,
            user_id='me'
        ))

    except Exception as e:
        print(f"[DELETE ERROR] {e}")

async def main():
    if not await client.is_user_authorized():
        phone = input("📱 Enter your phone number: ")
        await client.send_code_request(phone)
        code = input("💬 Enter the code you received: ")
        try:
            await client.sign_in(phone, code)
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return
    print("✅ Bot is running. Waiting for .mm or .del...")

with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
