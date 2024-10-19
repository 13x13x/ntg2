from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import asyncio
from asyncio import sleep
from pymongo.errors import ServerSelectionTimeoutError
from config import app, users_collection

# Start message with inline buttons for user settings
@app.on_message(filters.command("start"))
async def start(client, message):
    print("Start command received")
    user_id = message.from_user.id

    # Check if user exists in the database
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "amazon_tag": None, "footer": None})
        print(f"User {user_id} added to the database")

    welcome_text = "**ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴍᴀᴢᴏɴ ᴀғғɪʟɪᴀᴛᴇ ʟɪɴᴋ ᴄʀᴇᴀᴛᴏʀ ʙᴏᴛ!**\n**ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs**"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("㊂ ᴜsᴇʀ sᴇᴛᴛɪɴɢs", callback_data="user_settings")]
    ])

    try:
        await message.reply_text(welcome_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Error sending message: {e}")

# User Settings Menu
@app.on_callback_query(filters.regex("user_settings"))
async def user_settings(client, callback_query):
    user_id = callback_query.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    amazon_tag = user.get('amazon_tag', 'Not set')
    footer = user.get('footer', 'Not set')
    username = callback_query.from_user.username or "Unknown User"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("sᴇᴛ/ᴇᴅɪᴛ ᴛᴀɢ", callback_data="add_tag"),
            InlineKeyboardButton("ʀᴇᴍᴏᴠᴇ ᴛᴀɢ", callback_data="remove_tag")
        ],
        [
            InlineKeyboardButton("sᴇᴛ/ᴇᴅɪᴛ ғᴏᴏᴛᴇʀ", callback_data="add_footer"),
            InlineKeyboardButton("ʀᴇᴍᴏᴠᴇ ғᴏᴏᴛᴇʀ", callback_data="remove_footer")
        ],
        [
            InlineKeyboardButton("ʙᴏᴛ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ", url="https://t.me/Painfully") 
        ]
    ])

    await callback_query.message.edit_text(
        f"┌──── **㊂ ᴜsᴇʀ sᴇᴛᴛɪɴɢs** ───\n"
        f"├── **ɴᴀᴍᴇ :** `@{username}`\n"
        f"├── **ᴀᴍᴀᴢᴏɴ ᴛᴀɢ :** `{amazon_tag}`\n"
        f"├── **ғᴏᴏᴛᴇʀ :** `{footer}`\n"
        f"└───────────────────\n\n"
        f"**📝 Use the buttons below to manage your Amazon tag and footer.**",
        reply_markup=keyboard
    )

# Add/Edit Tag
@app.on_callback_query(filters.regex("add_tag"))
async def add_tag(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_tag": True}})
    await callback_query.message.reply("**Send your Amazon tag in the format `tag=csls0d6-21`. You have 60 seconds to reply.**")
    await sleep(60)
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data.get("awaiting_tag"):
        users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_tag": False}})
        await callback_query.message.reply("**Timeout! You didn't send the tag within 60 seconds.**")

# Add/Edit Footer
@app.on_callback_query(filters.regex("add_footer"))
async def add_footer(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_footer": True}})
    await callback_query.message.reply("**Send the footer text to save. You have 60 seconds to reply.**")
    await sleep(60)
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data.get("awaiting_footer"):
        users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_footer": False}})
        await callback_query.message.reply("**Timeout! You didn't send the footer within 60 seconds.**")

# Capture and save Amazon tag or footer
@app.on_message(filters.text & filters.private)
async def capture_tag_or_footer(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})
    if user:
        if user.get('awaiting_tag'):
            users_collection.update_one({"user_id": user_id}, {"$set": {"amazon_tag": message.text, "awaiting_tag": False}})
            await message.reply("**Your Amazon tag has been saved successfully!**")
        elif user.get('awaiting_footer'):
            users_collection.update_one({"user_id": user_id}, {"$set": {"footer": message.text, "awaiting_footer": False}})
            await message.reply("**Footer has been saved successfully!**")

# Remove Tag
@app.on_callback_query(filters.regex("remove_tag"))
async def remove_tag(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"amazon_tag": None}})
    await callback_query.answer("Your Amazon tag has been removed")

# Remove Footer
@app.on_callback_query(filters.regex("remove_footer"))
async def remove_footer(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"footer": None}})
    await callback_query.answer("Footer has been removed")

# /ntg command to replace the tag
@app.on_message(filters.command("ntg") & filters.private)
async def replace_tag(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await message.reply("**User not found in the database. Please start the bot again.**")
        return

    amazon_tag = user.get('amazon_tag')
    if not amazon_tag:
        await message.reply("**Please add your Amazon tag from the user settings.**")
        return

    try:
        if len(message.command) > 1:
            url = message.command[1]
            if "tag=" in url:
                updated_url = re.sub(r'tag=[^&]+', f'tag={amazon_tag}', url)
            else:
                updated_url = url + f"&tag={amazon_tag}"

            footer = user.get('footer', '')
            final_message = f"**Here is your modified Amazon link:**\n**{updated_url}**"
            if footer:
                final_message += f"\n\n{footer}"

            await message.reply(final_message)
        else:
            await message.reply("**Please provide a valid Amazon URL.**")
    except Exception as e:
        await message.reply(f"Error in /ntg command: {e}")

# Starting the bot
async def main():
    await app.start()
    print("Bot started..")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
