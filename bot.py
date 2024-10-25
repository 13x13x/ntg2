from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pyrogram import Client, filters
from pyrogram import errors
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import requests
import aiohttp
from bs4 import BeautifulSoup
import asyncio
from asyncio import sleep
import os
import uuid
import nest_asyncio
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from new import broadcast, ban_user, unban_user, user_stats

from pyrogram.errors import PeerIdInvalid  # Import the specific error

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# MongoDB URI and Owner ID
MONGO_URI = "mongodb+srv://shopngodeals:ultraamz@cluster0.wn2wr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
OWNER_ID = 5549620776
LOG_CHANNEL = -1001998686767

# Telegram API credentials
api_id = 24972774
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'
bot_token = '6246208865:AAEbf4RNlcCPwCWoYt4qnYmh79tsUGcctA4'

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client['lanjaa_db']
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

#premium

# Handler for the /why command
@app.on_message(filters.command("why") & filters.private)
async def why_command(client, message):
    response_text = (
        "**🙏🏻 Subscription Required For Bot Access**\n\n"
        "**Dear User,**\n\n"
        "**We regret to inform you that you currently do not have access to the features of our bot** "
        "**To enjoy full functionality, we kindly invite you to purchase a subscription from the owner**\n\n"
        "**We offer a flexible Monthly Subscription Plan designed to cater to your needs**\n\n"
        "**If you have any questions or require further assistance, please feel free to reach out to our support admin at @amzdevbot**\n\n"
        "**We appreciate your understanding and support**\n\n"
        "**Best Regards,**\n"
        "**Team: @Ultraamzinfo**\n"
    )

    # Send the text message with the image
    await message.reply_photo(photo="https://envs.sh/pHm.jpg", caption=response_text)

# Command to handle /info and save user details to info.txt
@app.on_message(filters.command("info") & filters.user(OWNER_ID))  # OWNER_ID is your admin user ID
async def me(client, message):
    # Fetch all users from the database
    users = users_collection.find()

    # Create or open the info.txt file in write mode
    with open("info.txt", "w") as f:
        count = 1
        for user in users:
            # Get the user_id from the database
            user_id = user.get("user_id", "None")

            # If the username is not in the database, attempt to fetch it from Telegram
            if user.get("username"):
                username = user["username"]
            else:
                try:
                    # Try to fetch the username from Telegram
                    fetched_user = await client.get_users(user_id)
                    username = fetched_user.username or "None"
                except PeerIdInvalid:
                    # If the user cannot be found, default to "None"
                    username = "None"

            # Get other details from the database
            amazon_tag = user.get("amazon_tag", "None")
            footer = user.get("footer", "None")
            channel = user.get("channel", "None")

            # Write the user details in the required format
            f.write(f"{count}. {username} {user_id} {amazon_tag} {footer} {channel}\n")
            count += 1

    # Send the file to the bot
    await client.send_document(
        message.chat.id,
        document="info.txt",
        caption="**Here are the details of all users**"
    )

    # Optionally remove the file after sending it
    os.remove("info.txt")

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id

    # Check if user exists in the database
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        users_collection.insert_one({"user_id": user_id, "amazon_tag": None, "footer": None, "channel": None, "banned": True})
        print(f"User {user_id} added and banned automatically")  # Debugging line": user_id, "amazon_tag": None, "footer": None})
        print(f"User {user_id} Added in the database")  # Debugging line

        # Notify the log channel about the new user
        try:
            if message.from_user.username:
                username = message.from_user.username
            else:
                username = "Nonee"
            notification_text = f"**#NewUser from Ultraamz 😘**\n**UserID:** `{user_id}`\n**Username: @{username}**"
            await client.send_message(LOG_CHANNEL, notification_text)
        except Exception as e:
            print(f"Error sending notification to log channel: {e}")

    else:
        print(f"User {user_id} already exists in the database")  # Debugging line

    # Welcome text without formatting
    welcome_text = "**🛒 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴍᴀᴢᴏɴ ᴀғғɪʟɪᴀᴛᴇ ʟɪɴᴋ ᴄʀᴇᴀᴛᴏʀ ʙᴏᴛ! ᴡɪᴛʜ ᴘʀᴏᴅᴜᴄᴛ ᴅᴀᴛᴀɪʟs**\n\n**↓↓ ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ↓↓**"

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

#ntg

@app.on_message(filters.command("amz") & filters.private)
async def replace_tag(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    # Check if user is banned
    if user and user.get('banned', False):
        await message.reply("**Important Notice: The bot is currently unable to execute commands as expected**\n\n**Please check /why for full information**")
        return

    # Ensure user exists and has an Amazon tag
    if not user:
        await message.reply("**✨ Please /start Bot**")
        return
    
    amazon_tag = user.get('amazon_tag')
    if not amazon_tag:
        await message.reply("**Please Add Your Amazon Tag in User Settings Using This /start**")
        return

    if len(message.command) > 1:
        url = message.command[1]

        # Handle amzn.to and amzn.in short URLs
        if url.startswith("https://amzn.to/") or url.startswith("https://amzn.in/"):
            try:
                response = requests.get(url, allow_redirects=False)
                location = response.headers.get('location')
                if location:
                    url = location
                else:
                    await message.reply("**Error: Unable to extract product code from shortened URL.**")
                    return
            except Exception as e:
                await message.reply(f"**Error resolving shortened URL: {e}**")
                return

        # Validate product URL format
        if not re.search(r'/dp/([A-Z0-9]{10})', url):
            await message.reply("**Invalid URL: Please provide a valid Amazon product URL.**")
            return

        # Modify the URL with the Amazon tag
        url_parts = list(urlparse(url))
        query_params = parse_qs(url_parts[4])

        # Update or add the tag parameter
        query_params['tag'] = [amazon_tag]

        # Remove duplicate ref parameters
        query_params = {key: value for key, value in query_params.items() if key != 'ref'}

        # Rebuild the query string
        url_parts[4] = urlencode(query_params, doseq=True)
        updated_url = urlunparse(url_parts)

        try:
            # Call the scrape_amazon_product function to fetch product details
            product_details, product_image_url = scrape_amazon_product(updated_url)

            footer = user.get('footer', '')
            if footer:
                product_details += f"\n\n**{footer}**"

            if product_image_url:
                # Send the product details to the user
                await message.reply_photo(photo=product_image_url, caption=product_details)

                # Forward the product details to the user's specified channel
                channel = user.get('channel', '')
                if channel:
                    try:
                        # Forward the message to the channel
                        await client.send_photo(chat_id=channel, photo=product_image_url, caption=product_details)
                    except Exception as e:
                        await message.reply(f"**Error forwarding to channel: {e}**")
            else:
                await message.reply("**No channel specified for forwarding. Skipping auto-forwarding.**")

        except Exception as e:
            await message.reply(f"**Error fetching product details: {e}**")
    else:
        await message.reply("**🚶🏻.. Please Send Valid Amazon URL**")
        
#new

import threading
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

# Initialize a single session for all HTTP requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
    'Accept-Language': 'en-US, en;q=0.5'
})

# Precompile regex patterns
image_url_pattern = re.compile(r'_(UX|SX|SL)[0-9]+_')
non_numeric_pattern = re.compile(r'[^\d.]')

# Load the Roboto font once
try:
    font_path = "fonts/Roboto-Bold.ttf"  # Ensure this path is correct
    font_size = 25
    font = ImageFont.truetype(font_path, font_size)
except IOError:
    print("Error: Font file not found. Please check the font path.")
    font = ImageFont.load_default()

# Lock for thread-safe operations (if needed)
lock = threading.Lock()

def create_thumbnail_with_text(product_image_url):
    try:
        # Fetch the product image using the shared session
        response = session.get(product_image_url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        product_img = Image.open(BytesIO(response.content)).convert('RGB')  # Ensure image is in RGB

        # Resize the product image to fit within the canvas
        max_size = (900, 900)  # Slight increase in size
        product_img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Create a white background canvas (1280x720)
        canvas_size = (1280, 720)
        white_bg = Image.new('RGB', canvas_size, 'white')

        # Center the product image on the canvas
        img_w, img_h = product_img.size
        bg_w, bg_h = white_bg.size
        offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
        white_bg.paste(product_img, offset)

        # Draw text on the image
        draw = ImageDraw.Draw(white_bg)

        # Define the text and position
        text = "BOT: @Ultraamzbot"
        text_color = (0, 0, 0)  # Black color
        text_position = (10, bg_h - font_size - 18)  # Bottom left corner with some padding

        # Add the text to the image
        draw.text(text_position, text, fill=text_color, font=font)

        # Save the image to a BytesIO object
        buffer = BytesIO()
        white_bg.save(buffer, format="JPEG", optimize=True, quality=85)  # Optimize image size
        buffer.seek(0)

        return buffer
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None

def scrape_amazon_product(url):
    try:
        # Fetch the product page using the shared session
        response = session.get(url, timeout=10)
        response.raise_for_status()

        # Parse the HTML content with BeautifulSoup using the faster 'lxml' parser
        soup = BeautifulSoup(response.content, 'lxml')

        # Product name
        product_name_tag = soup.find('span', {'id': 'productTitle'})
        if product_name_tag:
            product_name = product_name_tag.get_text(strip=True)
        else:
            return "**Product Details Not Found, Try Again**", None

        # Price (deal price)
        price_tag = soup.find('span', {'class': 'a-price-whole'})
        if price_tag:
            price = price_tag.get_text(strip=True).replace(',', '').rstrip('.')
        else:
            price = 'not found'

        # MRP (find the highest valid MRP)
        mrp_tag = soup.find('span', {'class': 'a-price a-text-price'})
        mrp = 'not found'
        if mrp_tag:
            mrp_values = mrp_tag.find_all('span', {'class': 'a-offscreen'})
            valid_mrps = []
            for val in mrp_values:
                text_value = val.get_text(strip=True)
                if "per" not in text_value.lower():  # Ignore values like "₹2.69 per millilitre"
                    try:
                        mrp_cleaned = float(non_numeric_pattern.sub('', text_value))
                        valid_mrps.append(mrp_cleaned)
                    except ValueError:
                        continue

            # Select the highest MRP that is greater than the price
            if valid_mrps:
                highest_valid_mrp = max(valid_mrps)
                if price != 'not found' and highest_valid_mrp > float(price):
                    mrp = f"₹{highest_valid_mrp:.2f}"
                else:
                    mrp = 'not applicable'

        # Calculate discount
        discount_text = ""
        if mrp not in ['not applicable', 'not found']:
            try:
                price_value = float(price.replace(',', ''))
                mrp_value = float(mrp.replace('₹', '').replace(',', '')) if mrp != 'not found' else 0
                if mrp_value > price_value:
                    discount = mrp_value - price_value
                    discount_percentage = (discount / mrp_value) * 100 if mrp_value else 0
                    discount_text = f"😱 **Discount: ₹{discount:.2f} ({discount_percentage:.2f}%) 🔥**\n\n"
            except (ValueError, TypeError):
                discount_text = ""

        # Product Image (scrape in HD quality)
        image_tag = soup.find('div', {'id': 'imgTagWrapperId'})
        product_thumbnail = None
        if image_tag and image_tag.img:
            product_image_url = image_tag.img.get('data-a-dynamic-image')
            if product_image_url:
                # Extract the first image URL from the JSON-like string
                match = re.search(r'"(https://[^"]+)"', product_image_url)
                if match:
                    product_image_url = match.group(1)
                    # Transform the image URL to get the highest quality version available
                    product_image_url = image_url_pattern.sub('_UL1500_', product_image_url)

                    # Create white background thumbnail
                    product_thumbnail = create_thumbnail_with_text(product_image_url)
        # Final product details response
        product_details = f"🤯 **{product_name}**\n\n"
        product_details += discount_text  # Add discount only if available
        if mrp != 'not applicable':
            product_details += f"❌ **Regular Price:** **~~{mrp}/-~~**\n\n"
        product_details += f"✅ **Deal Price: ₹{price}/-**\n\n**[🛒 𝗕𝗨𝗬 𝗡𝗢𝗪]({url})**"

        return product_details, product_thumbnail

    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return f"**Failed To Retrieve Page: {e}**", None
    except Exception as e:
        print(f"Error scraping product: {e}")
        return "**An unexpected error occurred. Please try again later.**", None
        

def scrape_multiple_products(urls):
    product_details_list = []
    product_thumbnails = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(scrape_amazon_product, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                details, thumbnail = future.result()
                product_details_list.append(details)
                product_thumbnails.append(thumbnail)
            except Exception as e:
                print(f"Error processing {url}: {e}")
                product_details_list.append(f"**Failed to process {url}**")
                product_thumbnails.append(None)

    return product_details_list, product_thumbnails

# Command to scrape Amazon product
@app.on_message(filters.command("amzpd") & filters.private)
async def scrape(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("**🚶🏻.. Please Send a Vaild Amazon URL**")
            return

        url = message.command[1]
        product_details, product_image_url = scrape_amazon_product(url)

        # Fetch user info from the database using user_id
        user_id = message.from_user.id  # Get the user ID from the message
        user = users_collection.find_one({"user_id": user_id})

        if user.get('banned', False):  # Check if the user is banned
            await message.reply("**Important Notice: The bot is currently unable to execute commands as expected**\n\n**Please check /why for full information**")
            return

        if not user:
            await message.reply("**✨ Please /start Bot**")
            return

        footer = user.get('footer', '')  # Get the footer, if available
        if footer:
            product_details += f"\n\n**{footer}**"  # Append the footer to product details

        if product_image_url:
            await message.reply_photo(photo=product_image_url, caption=product_details)
        else:
            await message.reply(product_details)

    except Exception as e:
        await message.reply(f"**An error occurred while scraping: {e}**")
            
 
@app.on_message(filters.command("bcast") & filters.user(OWNER_ID))
async def handle_broadcast(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("**You are not authorized to use this command**")
        return
    
    lel = await message.reply_text("**⚡️ Processing...**")
    await broadcast(client, message, users_collection, lel)

@app.on_message(filters.command("fban") & filters.private)
async def handle_fban(client, message):
    await ban_user(client, message, users_collection, OWNER_ID)

@app.on_message(filters.command("funban") & filters.private)
async def handle_funban(client, message):
    await unban_user(client, message, users_collection, OWNER_ID)

@app.on_message(filters.command("fusers") & filters.private)
async def handle_fusers(client, message):
    await user_stats(client, message, users_collection, OWNER_ID)
    

# User Settings Menu with updated Add/Edit buttons
@app.on_callback_query(filters.regex("user_settings"))
async def user_settings(client, callback_query):
    user_id = callback_query.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    amazon_tag = user.get('amazon_tag', 'Not set')
    channel = user.get('channel', 'Not set')
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
            InlineKeyboardButton("ᴇɴᴀʙʟᴇ ғᴏʀᴡᴀʀᴅ", callback_data="add_channel"),
            InlineKeyboardButton("ᴅɪsᴀʙʟᴇ ғᴏʀᴡᴀʀᴅ", callback_data="remove_channel")
        ],
        [
            InlineKeyboardButton("ʙᴏᴛ ᴜᴘᴅᴀᴛᴇs", url="https://t.me/Ultraamzinfo")  # Replace with your channel link
        ]
    ])

# Update the message to include auto forwarding details
    await callback_query.edit_message_text(
        f"┌──── **㊂ ᴜsᴇʀ sᴇᴛᴛɪɴɢs** ───\n"
        f"│\n"
        f"├─ **ɴᴀᴍᴇ :** `@{username}`\n"
        f"├─ **ᴀᴍᴀᴢᴏɴ ᴛᴀɢ :** `{amazon_tag}`\n"
        f"├─ **ғᴏᴏᴛᴇʀ :** `{footer}`\n"
        f"├─ **ᴀᴜᴛᴏ ғᴏʀᴡᴀʀᴅɪɴɢ ᴛᴏ ᴄʜᴀɴɴᴇʟ :** `{channel}`\n"
        f"│\n"
        f"└───────────────────\n\n"
        f"**📝 ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ sᴇᴛ, ᴇᴅɪᴛ, ᴏʀ ʀᴇᴍᴏᴠᴇ ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ, ғᴏᴏᴛᴇʀ, ᴀɴᴅ ᴀᴜᴛᴏ ғᴏʀᴡᴀʀᴅɪɴɢ..**",
        reply_markup=keyboard
    )

# vaild 

def is_valid_amazon_tag(tag):
    # Define the regex pattern for a valid Amazon tag
    # This example assumes the tag can include letters, numbers, and hyphens.
    pattern = r'^[a-zA-Z0-9-]+$'
    return re.match(pattern, tag) is not None

# Handle Add Tag (Prompt user to send the Amazon tag)
@app.on_callback_query(filters.regex("add_tag"))
async def add_tag(client, callback_query):
    user_id = callback_query.from_user.id
    # Set awaiting_tag to True for this user
    users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_tag": True}})
    await callback_query.message.reply("**🙂 ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ɪɴ ᴛʜᴇ ғᴏʀᴍᴀᴛ:**\n\n**ᴇxᴀᴍᴘʟᴇ :** `csls0d6-21`\n\n(**ʏᴏᴜ ʜᴀᴠᴇ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴛᴏ ʀᴇᴘʟʏ**)")

    await sleep(60)

    # Check if the user has sent the footer within the time limit
    user_data = users_collection.find_one({"user_id": user_id})

    if user_data and user_data.get("awaiting_tag"):
        users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_tag": False}})
        await callback_query.message.reply("**🚶🏻.. ᴛɪᴍᴇᴏᴜᴛ!** **ʏᴏᴜ ᴅɪᴅ ɴᴏᴛ sᴇɴᴅ ᴛʜᴇ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ᴛᴇxᴛ ᴡɪᴛʜɪɴ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ**")


@app.on_callback_query(filters.regex("add_footer"))
async def add_footer(client, callback_query):
    user_id = callback_query.from_user.id

    # Set awaiting_footer to True for this user
    users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_footer": True}})

    # Send initial message to prompt the user to send the footer text
    await callback_query.message.reply("**🙂 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ғᴏᴏᴛᴇʀ ᴛᴇxᴛ ᴛᴏ sᴀᴠᴇ!**\n\n**ᴇxᴀᴍᴘʟᴇ :** `Share & Join @Yourchannel`\n\n(**ʏᴏᴜ ʜᴀᴠᴇ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴛᴏ ʀᴇᴘʟʏ**)")

    # Wait for 60 seconds
    await sleep(60)

    # Check if the user has sent the footer within the time limit
    user_data = users_collection.find_one({"user_id": user_id})

    if user_data and user_data.get("awaiting_footer"):
        users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_footer": False}})
        await callback_query.message.reply("**🚶🏻.. ᴛɪᴍᴇᴏᴜᴛ!** **ʏᴏᴜ ᴅɪᴅ ɴᴏᴛ sᴇɴᴅ ᴛʜᴇ ғᴏᴏᴛᴇʀ ᴛᴇxᴛ ᴡɪᴛʜɪɴ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ**")

#Autoforward

@app.on_callback_query(filters.regex("add_channel"))
async def add_channel(client, callback_query):
    user_id = callback_query.from_user.id

    # Set awaiting_footer to True for this user
    users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_channel": True}})

    # Send initial message to prompt the user to send the footer text
    await callback_query.message.reply("**🙂 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ ᴛᴏ sᴀᴠᴇ!**\n\n**ɪᴍᴘᴏʀᴛᴀɴᴛ sᴛᴇᴘs:**\n\n**ᴘʀᴏᴠɪᴅᴇ ᴏɴʟʏ ᴛʜᴇ ᴘᴜʙʟɪᴄ ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ**\n\n**ᴇxᴀᴍᴘʟᴇ:** `@PIFDealss`\n\n**ɴᴏᴛᴇ: ɪғ ᴛʜᴇ ʙᴏᴛ ɪs ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ, ᴛʜᴇ ᴀᴜᴛᴏ ғᴏʀᴡᴀʀᴅɪɴɢ ғᴇᴀᴛᴜʀᴇ ᴡɪʟʟ ɴᴏᴛ ᴡᴏʀᴋ**\n\n**(ʏᴏᴜ ʜᴀᴠᴇ 60 sᴇᴄᴏɴᴅs ᴛᴏ ʀᴇᴘʟʏ)**")

    # Wait for 60 seconds
    await sleep(60)

    # Check if the user has sent the footer within the time limit
    user_data = users_collection.find_one({"user_id": user_id})

    if user_data and user_data.get("awaiting_channel"):
        users_collection.update_one({"user_id": user_id}, {"$set": {"awaiting_channel": False}})
        await callback_query.message.reply("**🚶🏻.. ᴛɪᴍᴇᴏᴜᴛ!** **ʏᴏᴜ ᴅɪᴅ ɴᴏᴛ sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ ᴡɪᴛʜɪɴ 𝟼𝟶 sᴇᴄᴏɴᴅs ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ**")

# Consolidated capture handler for tag and footer
@app.on_message(filters.text & filters.private)
async def capture_tag_or_footer(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    if user:
        # Check if awaiting a tag
        if user.get('awaiting_tag'):
            if is_valid_amazon_tag(message.text):
                # Save the Amazon tag and reset awaiting_tag to False
                users_collection.update_one({"user_id": user_id}, {"$set": {"amazon_tag": message.text, "awaiting_tag": False}})
                await message.reply("**😘 ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ʜᴀs ʙᴇᴇɴ sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**")
            else:
                await message.reply("**🥴 ɪɴᴠᴀʟɪᴅ ᴛᴀɢ ғᴏʀᴍᴀᴛ**")
            return

        # Check if awaiting a footer
        if user.get('awaiting_footer'):
            # Save the footer and reset awaiting_footer to False
            users_collection.update_one({"user_id": user_id}, {"$set": {"footer": message.text, "awaiting_footer": False}})
            await message.reply("**😘 ғᴏᴏᴛᴇʀ ʜᴀs ʙᴇᴇɴ sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**")
            return

        # Check if awaiting a channel 
        if user.get('awaiting_channel'):
            # Save the footer and reset awaiting_footer to False
            users_collection.update_one({"user_id": user_id}, {"$set": {"channel": message.text, "awaiting_channel": False}})
            await message.reply("**😘 ᴄʜᴀɴɴᴇʟ ʜᴀs ʙᴇᴇɴ sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**")
            return
            

# Handle Remove Tag
@app.on_callback_query(filters.regex("remove_tag"))
async def remove_tag(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"amazon_tag": None}})
    await callback_query.answer("🙃 ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ᴛᴀɢ ʜᴀs ʙᴇᴇɴ rᴇᴍᴏᴠᴇᴅ")

# Handle Remove auto forward 
@app.on_callback_query(filters.regex("remove_channel"))
async def remove_channel(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"channel": None}})
    await callback_query.answer("🙃 ᴀᴜᴛᴏ ғᴏʀᴡᴀʀᴅɪɴɢ ʜᴀs ʙᴇᴇɴ sᴛᴏᴘᴘᴇᴅ")

# Handle Remove Footer
@app.on_callback_query(filters.regex("remove_footer"))
async def remove_footer(client, callback_query):
    user_id = callback_query.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"footer": None}})
    await callback_query.answer("🙃 ғᴏᴏᴛᴇʀ ʜᴀs ʙᴇᴇɴ rᴇᴍᴏᴠᴇᴅ")


# Starting the bot
async def main():
    await app.start()
    print("Bot started Bro..")
    # Keep the bot running
    while True:
        await asyncio.sleep(1)

nest_asyncio.apply()
asyncio.run(main())
