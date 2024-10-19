from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import requests
from bs4 import BeautifulSoup
import asyncio
from asyncio import sleep
import os
import uuid
import nest_asyncio
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# MongoDB URI and Owner ID
MONGO_URI = "mongodb+srv://Puka12:puka12@cluster0.4xmyiyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

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

@app.on_message(filters.command("amz") & filters.private)
async def replace_tag(client, message):
    user_id = message.from_user.id
    print(f"/amz command received from {user_id}")  # Debugging line

    user = users_collection.find_one({"user_id": user_id})

    if not user:
        await message.reply("**User not found in the database. Please start the bot again.**")
        return

    amazon_tag = user.get('amazon_tag')
    if not amazon_tag:
        await message.reply("**Please add your Amazon tag from the user settings using the 'set/edit tag' button.**")
        return

    try:
        if len(message.command) > 1:
            url = message.command[1]
            print(f"Processing URL: {url} for user {user_id} with tag {amazon_tag}")

            # Replace existing tag or add new one
            if "tag=" in url:
                updated_url = re.sub(r'tag=[^&]+', f'tag={amazon_tag}', url)  # Replace the existing tag
            else:
                updated_url = url + f"&tag={amazon_tag}"  # Append the tag if not present

            # Automatically call the /run command with the updated URL
            new_command = f"/run {updated_url}"
            sent_message = await app.send_message(chat_id=message.chat.id, text=new_command)

            # Wait for 3 seconds, then delete the message
            await asyncio.sleep(3)
            await app.delete_messages(chat_id=message.chat.id, message_ids=sent_message.id)

        else:
            await message.reply("**Please provide a valid Amazon URL.**")
    except Exception as e:
        print(f"Error in /amz command: {e}")  # Debugging
        await message.reply(f"Error in /amz command: {e}")

# Scraper function to fetch Amazon product data
def scrape_amazon_product(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5'
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return f"Failed to retrieve page, status code: {response.status_code}", None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Product name
    product_name = soup.find('span', {'id': 'productTitle'})
    if product_name:
        product_name = product_name.get_text(strip=True)
    else:
        return "Product name not found", None

    # Price
    price = soup.find('span', {'class': 'a-price-whole'})
    if price:
        price = price.get_text(strip=True).rstrip('.')
    else:
        price = 'not found'

    # MRP (if available)
    mrp_tag = soup.find('span', {'class': 'a-price a-text-price'})
    mrp = None
    if mrp_tag:
        mrp_span = mrp_tag.find('span', {'class': 'a-offscreen'})
        if mrp_span:
            mrp = mrp_span.get_text(strip=True)
        else:
            mrp = 'MRP not found'
    else:
        mrp = 'not found'

    # Calculate discount
    try:
        price_value = float(price.replace(',', ''))
        mrp_value = float(mrp.replace('₹', '').replace(',', ''))
        discount = mrp_value - price_value
        discount_percentage = (discount / mrp_value) * 100
        discount_text = f'₹{discount:.2f} ({discount_percentage:.2f}%)'
    except (ValueError, TypeError):
        discount_text = 'Unable to calculate discount'

    # Product Image
    image_tag = soup.find('div', {'id': 'imgTagWrapperId'})
    if image_tag and image_tag.img:
        product_image_url = image_tag.img['src'].replace('_UX75_', '_UX500_').replace('_SX38_', '_SL1000_')
    else:
        product_image_url = None

    # Final product details response
    product_details = f"🤯 **{product_name}**\n\n💥 **Discount: {discount_text} 🔥**\n❌ **Regular Price:** ~~{mrp}/-~~\n✅ **Deal Price: ₹{price}/-**\n\n[🛒 **𝗕𝗨𝗬 𝗡𝗢𝗪**]({url})"
    
    return product_details, product_image_url

# Command to scrape Amazon product
@app.on_message(filters.command("run") & filters.private)
async def scrape(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("**Please provide a valid Amazon URL.**")
            return

        url = message.command[1]
        product_details, product_image_url = scrape_amazon_product(url)

        # Fetch user info from the database using user_id
        user_id = message.from_user.id  # Get the user ID from the message
        user = users_collection.find_one({"user_id": user_id})

        if not user:
            await message.reply("**User not found in the database. Please start the bot again.**")
            return

        footer = user.get('footer', '')  # Get the footer, if available
        if footer:
            product_details += f"\n\n**{footer}**"  # Append the footer to product details

        if product_image_url:
            await message.reply_photo(photo=product_image_url, caption=product_details)
        else:
            await message.reply(product_details)

    except Exception as e:
        await message.reply(f"An error occurred while scraping: {e}")
        
# Start message with inline buttons for user settings
@app.on_message(filters.command("start"))
async def start(client, message):
    print("Start command received")  # Debugging line
    user_id = message.from_user.id

    # Check if user exists in the database
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "amazon_tag": None, "footer": None})
        print(f"User {user_id} added to the database")  # Debugging line

    # Simple welcome text without formatting
    welcome_text = "**ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴍᴀᴢᴏɴ ᴀғғɪʟɪᴀᴛᴇ ʟɪɴᴋ ᴄʀᴇᴀᴛᴏʀ ʙᴏᴛ! ᴡɪᴛʜ ᴘʀᴏᴅᴜᴄᴛ ᴅᴀᴛᴀɪʟs**\n\n**ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs**"

    # Create the inline keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("㊂ ᴜsᴇʀ sᴇᴛᴛɪɴɢs", callback_data="user_settings")
        ]
    ])

    try:
        # Send message without parse_mode
        await message.reply_text(welcome_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Error sending message: {e}")

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
    await callback_query.message.reply("**ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ɪɴ ᴛʜᴇ ғᴏʀᴍᴀᴛ:**\n\n**ᴇxᴀᴍᴘʟᴇ :** `tag=csls0d6-21`\n\n(**ʏᴏᴜ ʜᴀᴠᴇ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴛᴏ ʀᴇᴘʟʏ**)")

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
    print("Bot started..")
    # Keep the bot running
    while True:
        await asyncio.sleep(1)

nest_asyncio.apply()
asyncio.run(main())
