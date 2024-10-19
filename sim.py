from pyrogram import Client, filters
import requests
from bs4 import BeautifulSoup
import re
import nest_asyncio
import asyncio
from pymongo.errors import ServerSelectionTimeoutError
from bot import app, users_collection

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
