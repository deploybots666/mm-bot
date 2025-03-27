from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditPhotoRequest,
    EditAdminRequest
)
from telethon.tl.functions.messages import ExportChatInviteRequest, EditChatAboutRequest
from telethon.tl.types import ChatAdminRights, InputChatUploadedPhoto
import asyncio

# --- Your ALT account credentials ---
api_id = 26532035
api_hash = 'f43d15238cf4775858955b03d5b74387'
session_name = 'alanmmd'

# --- Main admin user ID ---
MAIN_USER_ID = 5045853109
GROUP_PHOTO_PATH = 'group.jpeg'  # Make sure this file exists in Replit or Koyeb environment

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(from_users=MAIN_USER_ID, pattern=r'^\.mm$'))
async def create_group(event):
    print("Received .mm command")  # Log to confirm command is received

    try:
        # Step 1: Create the megagroup
        result = await client(CreateChannelRequest(
            title="MM Group",
            about="",
            megagroup=True
        ))

        group = result.chats[0]
        chat = await client.get_input_entity(group.id)

        # Step 2: Upload group photo with retries
        for attempt in range(6):
            try:
                uploaded_photo = await client.upload_file(GROUP_PHOTO_PATH)
                photo = InputChatUploadedPhoto(uploaded_photo)
                await client(EditPhotoRequest(
                    channel=chat,
                    photo=photo
                ))
                break
            except Exception as e:
                print(f"Telegram is having internal issues {e}")
                await asyncio.sleep(5)
                if attempt == 5:
                    print("[Photo Error] Request was unsuccessful 6 time(s)")

        # Step 3: Set group bio
        await client(EditChatAboutRequest(
            peer=chat,
            about="Always make sure that you’re dealing via @alans, not an impersonator"
        ))

        # Step 4: Promote main user to admin with title
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

        # Step 5: Send instruction message
        msg = await client.send_message(group.id,
            "**Hey. Please state the terms of the deal:**\n\n"
            "• What is the deal?\n"
            "• Who is the buyer/seller?\n"
            "• What is the agreed price and which crypto?\n"
            "• Include any other relevant information."
        )

        # Try to pin with flood wait handling
        try:
            await msg.pin()
        except Exception as e:
            print(f"[PIN ERROR] {e}")

        # Step 6: Create invite link
        invite = await client(ExportChatInviteRequest(peer=chat))

        # Step 7: Respond with invite link
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

        await asyncio.sleep(1800)  # 30 minutes
        await client(functions.messages.DeleteChatUserRequest(
            chat_id=chat.id,
            user_id='me'
        ))

    except Exception as e:
        print(f"[DELETE ERROR] {e}")

print("✅ Bot is running. Waiting for .mm or .del...")
client.start()
client.run_until_disconnected()