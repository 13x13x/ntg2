from pyrogram import Client, filters
from pyrogram import errors
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import aiohttp  # Use aiohttp
from bs4 import BeautifulSoup
import asyncio
from asyncio import sleep
import os
import uuid
import nest_asyncio
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from new import broadcast, ban_user, unban_user, user_stats

# MongoDB URI and Owner ID
MONGO_URI = "mongodb+srv://Puka12:puka12@cluster0.4xmyiyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
OWNER_ID = 6290483448

# Telegram API credentials
api_id = 24972774
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'
bot_token = '6401043461:AAH5GrnSCgbCldGRdLy-SDvhcK4JzgozI3Y'

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client['lanja_db']
    users_collection = db['users']
    print("Connected to MongoDB")  # Debugging line
except ServerSelectionTimeoutError as e:
    print(f"Could not connect to MongoDB: {e}")

# Session setup for the bot
session_name = f"web_scraper_bot_{api_id}_{uuid.uuid4()}"
os.makedirs("./sessions", exist_ok=True)

app = Client(
    session_name,
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
    workdir="./sessions"
)

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id

    # Check if user exists in the database
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        users_collection.insert_one({"user_id": user_id, "amazon_tag": None, "footer": None})
        print(f"User {user_id} Added in the database")  # Debugging line
    else:
        print(f"User {user_id} already exists in the database")  # Debugging line

    if user and user.get('banned', False):  # Check if the user is banned
        await message.reply("**You Are Banned 🚫 From Using This Bot**")
        return

    # Welcome text without formatting
    welcome_text = "**ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴍᴀᴢᴏɴ ᴀғғɪʟɪᴀᴛᴇ ʟɪɴᴋ ᴄʀᴇᴀᴛᴏʀ ʙᴏᴛ! ᴡɪᴛʜ ᴘʀᴏᴅᴜᴄᴛ ᴅᴀᴛᴀɪʟs**\n\n**ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs**"

    # Create the inline keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("㊂ ᴜsᴇʀ sᴇᴛᴛɪɴɢs", callback_data="user_settings")
        ]
    ])

    # Define the image URL or path (can be a URL or a local file path)
    welcome_image_url = "https://envs.sh/pS2.jpg"  # Replace with your image URL

    try:
        # Send welcome image with caption (optional)
        await message.reply_photo(photo=welcome_image_url, caption=welcome_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.on_message(filters.command("amz") & filters.private)
async def amz_command(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    if user.get('banned', False):
        await message.reply("**You Are Banned 🚫 From Using This Bot**")
        return

    if not user:
        await message.reply("**User Not Found In The Database. Please /start The Bot Again**")
        return

    amazon_tag = user.get('amazon_tag')
    if not amazon_tag:
        await message.reply("**Please Add Your Amazon Tag From The User Settings Using The /start 'Set,Edit Tag' Buttons**")
        return

    if len(message.command) > 1:
        url = message.command[1]
        updated_url = url + f"&tag={amazon_tag}" if "tag=" not in url else re.sub(r'tag=[^&]+', f'tag={amazon_tag}', url)
        
        try:
            product_details, product_image_url = await scrape_amazon_product(updated_url, user)

            if product_details:
                if product_image_url:
                    await client.send_photo(chat_id=message.chat.id, photo=product_image_url, caption=product_details, parse_mode='html')
                else:
                    await message.reply(product_details, parse_mode='html')
            else:
                await message.reply("**Failed to retrieve product details.**")
        except Exception as e:
            await message.reply(f"**Error in /amz command: {str(e)}**")
    else:
        await message.reply("**Please Provide A Valid Amazon URL**")


async def scrape_amazon_product(url, user):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept-Language': 'en-US, en;q=0.5'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                return f"Failed to retrieve page, status code: {response.status}", None

            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')

            product_name = soup.find('span', {'id': 'productTitle'})
            if product_name:
                product_name = re.escape(product_name.get_text(strip=True))
            else:
                return "**Product Name Not Found, Try Again**", None

            price = soup.find('span', {'class': 'a-price-whole'})
            price = price.get_text(strip=True).rstrip('.') if price else 'not found'

            mrp_tag = soup.find('span', {'class': 'a-price a-text-price'})
            mrp = mrp_tag.find('span', {'class': 'a-offscreen'}).get_text(strip=True) if mrp_tag else 'not found'

            discount_text = 'Unable to Calculate Discount'
            try:
                price_value = float(price.replace(',', ''))
                mrp_value = float(mrp.replace('₹', '').replace(',', ''))
                discount = mrp_value - price_value
                discount_percentage = (discount / mrp_value) * 100
                discount_text = f'₹{discount:.2f} ({discount_percentage:.2f}%)'
            except (ValueError, TypeError):
                pass

            image_tag = soup.find('div', {'id': 'imgTagWrapperId'})
            product_image_url = image_tag.img['src'].replace('_UX75_', '_UX500_') if image_tag and image_tag.img else None

            product_details = (f"🤯 <b>{product_name}</b>\n\n"
                               f"💥 <b>Discount: {discount_text} 🔥</b>\n"
                               f"❌ <b>Regular Price:</b> <s>{mrp}/-</s>\n"
                               f"✅ <b>Deal Price: ₹{price}/-</b>\n\n"
                               f"<a href='{url}'>🛒 𝗕𝗨𝗬 𝗡𝗢𝗪</a>")

            footer = user.get('footer', '')
            if footer:
                product_details += f"\n\n<b>{footer}</b>"

            return product_details, product_image_url

@app.on_message(filters.command("bcast") & filters.user(OWNER_ID))
async def handle_broadcast(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return
    
    lel = await message.reply_text("`⚡️ Processing...`")
    await broadcast(client, message, users_collection, lel)

@app.on_message(filters.command("ban") & filters.private)
async def handle_ban(client, message):
    await ban_user(client, message, users_collection, OWNER_ID)

@app.on_message(filters.command("unban") & filters.private)
async def handle_unban(client, message):
    await unban_user(client, message, users_collection, OWNER_ID)

# User Settings Menu with updated Add/Edit buttons
@app.on_callback_query(filters.regex("user_settings"))
async def user_settings(client, callback_query):
    user_id = callback_query.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    amazon_tag = user.get('amazon_tag', 'Not set')
    footer = user.get('footer', 'Not set')
    username = callback_query.from_user.username or "Unknown User"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ ʀᴇғʀᴇsʜ ᴍᴇɴᴜ", callback_data="user_settings")
        ],
        [
            InlineKeyboardButton("sᴇᴛ/ᴇᴅɪᴛ ᴛᴀɢ", callback_data="add_tag"),
            InlineKeyboardButton("ʀᴇᴍᴏᴠᴇ ᴛᴀɢ", callback_data="remove_tag")
        ],
        [
            InlineKeyboardButton("sᴇᴛ/ᴇᴅɪᴛ ғᴏᴏᴛᴇʀ", callback_data="add_footer"),
            InlineKeyboardButton("ʀᴇᴍᴏᴠᴇ ғᴏᴏᴛᴇʀ", callback_data="remove_footer")
        ],
        [
            InlineKeyboardButton("ʙᴏᴛ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ", url="https://t.me/Painfully")  # Replace with your channel link
        ]
    ])

    # Update the message to provide more explanation
    await callback_query.message.edit_text(
        f"┌──── **㊂ ᴜsᴇʀ sᴇᴛᴛɪɴɢs** ───\n"
        f"│\n"
        f"├── **ɴᴀᴍᴇ :** `@{username}`\n"
        f"├── **ᴀᴍᴀᴢᴏɴ ᴛᴀɢ :** `{amazon_tag}`\n"
        f"├── **ғᴏᴏᴛᴇʀ :** `{footer}`\n"
        f"│\n"
        f"└───────────────────\n\n"
        f"**📝 ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ sᴇᴛ, ᴇᴅɪᴛ, ᴏʀ ʀᴇᴍᴏᴠᴇ ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ, ғᴏᴏᴛᴇʀ..**",
        reply_markup=keyboard
    )

# Handle Add Tag (Prompt user to send the Amazon tag)
@app.on_callback_query(filters.regex("add_tag"))
async def add_tag(client, callback_query):
    user_id = callback_query.from_user.id
    # Set awaiting_tag to True for this user
    users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_tag": True}})
    await callback_query.message.reply("**ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ɪɴ ᴛʜᴇ ғᴏʀᴍᴀᴛ:**\n\n**ᴇxᴀᴍᴘʟᴇ :** `csls0d6-21`\n\n(**ʏᴏᴜ ʜᴀᴠᴇ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴛᴏ ʀᴇᴘʟʏ**)")

    await sleep(60)

    # Check if the user has sent the footer within the time limit
    user_data = users_collection.find_one({"user_id": user_id})

    if user_data and user_data.get("awaiting_tag"):
        users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_tag": False}})
        await callback_query.message.reply("**ᴛɪᴍᴇᴏᴜᴛ!** **ʏᴏᴜ ᴅɪᴅ ɴᴏᴛ sᴇɴᴅ ᴛʜᴇ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ᴛᴇxᴛ ᴡɪᴛʜɪɴ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ**")


@app.on_callback_query(filters.regex("add_footer"))
async def add_footer(client, callback_query):
    user_id = callback_query.from_user.id

    # Set awaiting_footer to True for this user
    users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_footer": True}})

    # Send initial message to prompt the user to send the footer text
    await callback_query.message.reply("**ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ғᴏᴏᴛᴇʀ ᴛᴇxᴛ ᴛᴏ sᴀᴠᴇ!**\n\n**ᴇxᴀᴍᴘʟᴇ :** `share & join @channel`\n\n(**ʏᴏᴜ ʜᴀᴠᴇ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴛᴏ ʀᴇᴘʟʏ**)")

    # Wait for 60 seconds
    await sleep(60)

    # Check if the user has sent the footer within the time limit
    user_data = users_collection.find_one({"user_id": user_id})

    if user_data and user_data.get("awaiting_footer"):
        users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_footer": False}})
        await callback_query.message.reply("**ᴛɪᴍᴇᴏᴜᴛ!** **ʏᴏᴜ ᴅɪᴅ ɴᴏᴛ sᴇɴᴅ ᴛʜᴇ ғᴏᴏᴛᴇʀ ᴛᴇxᴛ ᴡɪᴛʜɪɴ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ**")

# Consolidated capture handler for tag and footer
@app.on_message(filters.text & filters.private)
async def capture_tag_or_footer(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    if user:
        # Check if awaiting a tag
        if user.get('awaiting_tag'):
            # Save the Amazon tag and reset awaiting_tag to False
            users_collection.update_one({"user_id": user_id}, {"$set": {"amazon_tag": message.text, "awaiting_tag": False}})
            await message.reply("**ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ʜᴀs ʙᴇᴇɴ sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**")
         # Sleep for 10 seconds
        # Check if awaiting a footer
        elif user.get('awaiting_footer'):
            # Save the footer and reset awaiting_footer to False
            users_collection.update_one({"user_id": user_id}, {"$set": {"footer": message.text, "awaiting_footer": False}})
            await message.reply("**ғᴏᴏᴛᴇʀ ʜᴀs ʙᴇᴇɴ sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**")


# Handle Remove Tag
@app.on_callback_query(filters.regex("remove_tag"))
async def remove_tag(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"amazon_tag": None}})
    await callback_query.answer("ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ʜᴀs ʙᴇᴇɴ rᴇᴍᴏᴠᴇᴅ")


# Handle Remove Footer
@app.on_callback_query(filters.regex("remove_footer"))
async def remove_footer(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"footer": None}})
    await callback_query.answer("ғᴏᴏᴛᴇʀ ʜᴀs ʙᴇᴇɴ rᴇᴍᴏᴠᴇᴅ")


# Starting the bot
async def main():
    await app.start()
    print("Bot started Bro..")
    # Keep the bot running
    while True:
        await asyncio.sleep(1)

nest_asyncio.apply()
asyncio.run(main())
