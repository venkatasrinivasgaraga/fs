from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated
)
import asyncio

# Global control for broadcast stop signals
broadcast_control = {}

# How often to update progress (every X users)
PROGRESS_EVERY = 10


@Client.on_message(filters.command('users'))
async def user_count(client, message):
    if not message.from_user.id in client.admins:
        return await client.send_message(message.from_user.id, "❌ You are not authorized to use this command.")
    
    total_users = await client.mongodb.full_userbase()
    await message.reply(f"**👥 {len(total_users)} users are currently using this bot!**")


@Client.on_message(filters.private & filters.command('broadcast'))
async def send_text(client, message):
    admin_ids = client.admins
    user_id = message.from_user.id

    if user_id in admin_ids and message.reply_to_message:
        query = await client.mongodb.full_userbase()
        broadcast_msg = message.reply_to_message
        broadcast_id = f"broadcast_{message.id}"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⛔ Stop Broadcast", callback_data=f"stop_broadcast_{broadcast_id}")
        ]])

        pls_wait = await message.reply(
            "📢 Broadcasting message... Please wait.",
            reply_markup=keyboard
        )

        broadcast_control[broadcast_id] = True

        total = successful = blocked = deleted = unsuccessful = 0

        for index, chat_id in enumerate(query, start=1):
            if not broadcast_control.get(broadcast_id, False):
                await pls_wait.edit("🚫 Broadcast Stopped.")
                break

            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await client.mongodb.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await client.mongodb.del_user(chat_id)
                deleted += 1
            except Exception as e:
                print(f"Error sending to {chat_id}: {e}")
                unsuccessful += 1
            total += 1

            if index % PROGRESS_EVERY == 0:
                await pls_wait.edit(
                    f"📤 Broadcasting...\n\n"
                    f"👥 Total: {total}\n"
                    f"✅ Sent: {successful} | 🚫 Blocked: {blocked}\n"
                    f"🗑️ Deleted: {deleted} | ⚠️ Failed: {unsuccessful}"
                )

        if broadcast_control.get(broadcast_id, False):
            status = f"""<b>✅ Broadcast Completed</b>

👥 Total Users: <code>{total}</code>
✅ Sent: <code>{successful}</code>
🚫 Blocked: <code>{blocked}</code>
🗑️ Deleted: <code>{deleted}</code>
⚠️ Failed: <code>{unsuccessful}</code>"""
            await pls_wait.edit(status)

        broadcast_control.pop(broadcast_id, None)

    else:
        msg = await message.reply("⚠️ Use this command as a reply to a message.")
        await asyncio.sleep(5)
        await msg.delete()


@Client.on_message(filters.private & filters.command('pbroadcast'))
async def pin_bdcst_text(client, message):
    admin_ids = client.admins
    user_id = message.from_user.id

    if user_id in admin_ids and message.reply_to_message:
        query = await client.mongodb.full_userbase()
        broadcast_msg = message.reply_to_message
        broadcast_id = f"pbroadcast_{message.id}"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⛔ Stop Pin Broadcast", callback_data=f"stop_broadcast_{broadcast_id}")
        ]])

        pls_wait = await message.reply(
            "📌 Broadcasting & Pinning message... Please wait.",
            reply_markup=keyboard
        )

        broadcast_control[broadcast_id] = True

        total = successful = blocked = deleted = unsuccessful = 0

        for index, chat_id in enumerate(query, start=1):
            if not broadcast_control.get(broadcast_id, False):
                await pls_wait.edit("🚫 Pin Broadcast Stopped.")
                break

            try:
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except UserIsBlocked:
                await client.mongodb.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await client.mongodb.del_user(chat_id)
                deleted += 1
            except Exception as e:
                print(f"Error pinning in {chat_id}: {e}")
                unsuccessful += 1
            total += 1

            if index % PROGRESS_EVERY == 0:
                await pls_wait.edit(
                    f"📌 Pin Broadcasting...\n\n"
                    f"👥 Total: {total}\n"
                    f"✅ Sent & Pinned: {successful} | 🚫 Blocked: {blocked}\n"
                    f"🗑️ Deleted: {deleted} | ⚠️ Failed: {unsuccessful}"
                )

        if broadcast_control.get(broadcast_id, False):
            status = f"""<b>📌 Pin Broadcast Completed</b>

👥 Total Users: <code>{total}</code>
✅ Sent & Pinned: <code>{successful}</code>
🚫 Blocked: <code>{blocked}</code>
🗑️ Deleted: <code>{deleted}</code>
⚠️ Failed: <code>{unsuccessful}</code>"""
            await pls_wait.edit(status)

        broadcast_control.pop(broadcast_id, None)

    else:
        msg = await message.reply("⚠️ Use this command as a reply to a message.")
        await asyncio.sleep(5)
        await msg.delete()


@Client.on_callback_query(filters.regex(r"stop_broadcast_(.+)"))
async def stop_broadcast(client, callback_query):
    broadcast_id = callback_query.data.split("stop_broadcast_")[-1]
    if broadcast_id in broadcast_control:
        broadcast_control[broadcast_id] = False
        await callback_query.answer("🛑 Broadcast will stop shortly...", show_alert=True)
    else:
        await callback_query.answer("❌ Broadcast already stopped or not found.", show_alert=True)
