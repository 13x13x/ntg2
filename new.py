from pyrogram import Client, filters
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import requests

# Command to broadcast a message (admin only)
async def broadcast(client, message, users_collection, OWNER_ID):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return

    text = " ".join(message.command[1:])
    all_users = users_collection.find({})
    for user in all_users:
        try:
            await client.send_message(user['user_id'], text)
        except Exception as e:
            print(f"Failed to send message to user {user['user_id']}: {e}")

    await message.reply("**Broadcast message sent**")

async def ban_user(client, message, users_collection, OWNER_ID):
    # Check if the user is the owner
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return 

    # Check if a user ID is provided
    if len(message.command) < 2:
        await message.reply("**Please provide a user ID to ban**")
        return

    # Parse the user ID from the command
    try:
        user_id = int(message.command[1])
    except ValueError:
        await message.reply("**Invalid user ID format. Please provide a valid integer ID.**")
        return

    # Check if the user exists in the database
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await message.reply(f"**User {user_id} does not exist in the database.**")
        return

    # Update the user's banned status in the database
    try:
        result = users_collection.update_one({"user_id": user_id}, {"$set": {"banned": True}})
        if result.modified_count > 0:
            await client.send_message(user_id, "**You are banned from the bot 🌚**")
            await message.reply(f"**User {user_id} has been banned**")
        else:
            await message.reply(f"**User {user_id} is already banned.**")
    except Exception as e:
        print(f"Error updating the database: {e}")
        await message.reply("**An error occurred while banning the user. Please try again later.**")

# Command to unban a user (admin only)
async def unban_user(client, message, users_collection, OWNER_ID):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return

    if len(message.command) < 2:
        await message.reply("**Please provide a user ID to unban**")
        return

    user_id = int(message.command[1])
    users_collection.update_one({"user_id": user_id}, {"$set": {"banned": False}})
    await client.send_message(user_id, "**You are unbanned from the bot. Happy to use! 🥳**")
    await message.reply(f"**User {user_id} has been unbanned**")

# Command to view user statistics (admin only)
async def user_stats(client, message, users_collection, OWNER_ID):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return

    total_users = users_collection.count_documents({})
    banned_users = users_collection.count_documents({"banned": True})
    await message.reply(f"**Total Users: {total_users}**\n**Banned Users: {banned_users}**")
