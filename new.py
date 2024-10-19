from pyrogram import Client, filters
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import requests

async def broadcast(client, message, users_collection, OWNER_ID):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return

    if len(message.command) < 2:
        await message.reply("**Please provide a message to broadcast**")
        return

    all_users = users_collection.find({})
    count_sent = 0

    # Determine the type of content to broadcast
    if message.reply_to_message:
        # Broadcasting a reply (can be a text message, photo, document, etc.)
        reply_message = message.reply_to_message

        for user in all_users:
            try:
                # Send based on the type of reply message
                if reply_message.text:
                    await client.send_message(user['user_id'], reply_message.text)
                elif reply_message.photo:
                    await client.send_photo(user['user_id'], reply_message.photo.file_id)
                elif reply_message.document:
                    await client.send_document(user['user_id'], reply_message.document.file_id)
                # Add other types as needed (like videos, audios, etc.)
                count_sent += 1
            except Exception as e:
                print(f"Failed to send message to user {user['user_id']}: {e}")

    else:
        # Broadcasting a regular text message
        text = " ".join(message.command[1:])
        for user in all_users:
            try:
                await client.send_message(user['user_id'], text)
                count_sent += 1
            except Exception as e:
                print(f"Failed to send message to user {user['user_id']}: {e}")

    await message.reply(f"**Broadcast message sent to {count_sent} users**")

async def ban_user(client, message, users_collection, OWNER_ID):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return 

    if len(message.command) < 2:
        await message.reply("**Please provide a user ID to ban**")
        return

    try:
        user_id = int(message.command[1])
    except ValueError:
        await message.reply("**Invalid user ID format. Please provide a valid integer ID**")
        return

    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await message.reply(f"**User {user_id} does not exist in the database**")
        return

    try:
        result = users_collection.update_one({"user_id": user_id}, {"$set": {"banned": True}})
        if result.modified_count > 0:
            await client.send_message(user_id, "**You are banned from the bot 🌚**")
            await message.reply(f"**User {user_id} has been banned**")
        else:
            await message.reply(f"**User {user_id} is already banned**")
    except Exception as e:
        print(f"Error updating the database: {e}")
        await message.reply("**An error occurred while banning the user. Please try again later**")

async def unban_user(client, message, users_collection, OWNER_ID):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return

    if len(message.command) < 2:
        await message.reply("**Please provide a user ID to unban**")
        return

    try:
        user_id = int(message.command[1])
    except ValueError:
        await message.reply("**Invalid user ID format. Please provide a valid integer ID**")
        return

    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await message.reply(f"**User {user_id} does not exist in the database**")
        return

    try:
        result = users_collection.update_one({"user_id": user_id}, {"$set": {"banned": False}})
        if result.modified_count > 0:
            await client.send_message(user_id, "**You are unbanned from the bot. Happy to use! 🥳**")
            await message.reply(f"**User {user_id} has been unbanned**")
        else:
            await message.reply(f"**User {user_id} was not banned**")
    except Exception as e:
        print(f"Error updating the database: {e}")
        await message.reply("**An error occurred while unbanning the user, Please try again later**")

# Command to view user statistics (admin only)
async def user_stats(client, message, users_collection, OWNER_ID):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return

    total_users = users_collection.count_documents({})
    banned_users = users_collection.count_documents({"banned": True})
    await message.reply(f"**Total Users: {total_users}**\n**Banned Users: {banned_users}**")
