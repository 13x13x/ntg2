from pyrogram import Client, filters
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import requests
import asyncio
from pyrogram import errors
from MongoClient import users_collection, remove_user  # Import your database and remove_user function

async def broadcast(client, message, users_collection, OWNER_ID):
    all_users = users_collection
    lel = await message.reply("`⚡️ Processing...`")
    success = 0
    failed = 0
    deactivated = 0
    blocked = 0

    # Check if the user is authorized
    if message.from_user.id != OWNER_ID:
        await lel.edit("**You are not authorized to use this command**")
        return

    if len(message.command) < 2:
        await lel.edit("**Please provide a message to broadcast**")
        return

    # Determine the type of content to broadcast
    if message.reply_to_message:
        reply_message = message.reply_to_message
        for user in all_users.find():
            try:
                userid = user['user_id']
                await reply_message.copy(userid)
                success += 1
            except FloodWait as ex:
                await asyncio.sleep(ex.value)
                await reply_message.copy(userid)
                success += 1
            except errors.InputUserDeactivated:
                deactivated += 1
                remove_user(userid)  # Ensure you have this function defined
            except errors.UserIsBlocked:
                blocked += 1
            except Exception as e:
                print(f"Failed to send message to user {userid}: {e}")
                failed += 1
    else:
        text = " ".join(message.command[1:])
        for user in all_users.find():
            try:
                userid = user['user_id']
                await client.send_message(userid, text)
                success += 1
            except FloodWait as ex:
                await asyncio.sleep(ex.value)
                await client.send_message(userid, text)
                success += 1
            except errors.InputUserDeactivated:
                deactivated += 1
                remove_user(userid)  # Ensure you have this function defined
            except errors.UserIsBlocked:
                blocked += 1
            except Exception as e:
                print(f"Failed to send message to user {userid}: {e}")
                failed += 1

    await lel.edit(f"✅ Successfully sent to `{success}` users.\n❌ Failed to send to `{failed}` users.\n👾 Found `{blocked}` blocked users.\n👻 Found `{deactivated}` deactivated users.")

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
