from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from PIL import Image, ImageDraw, ImageFont
from pymongo import MongoClient
import os

async def get_userinfo_img(user_id, profile_path=None):
    # Create a background image
    bg = Image.new("RGB", (1280, 720), (30, 30, 30))

    # Draw a gradient background
    draw_bg = ImageDraw.Draw(bg)
    for i in range(720):
        color = (30 + i // 3, 30 + i // 3, 30 + i // 3)  # Lighten the color as we go down
        draw_bg.line([(0, i), (1280, i)], fill=color)

    # Create a circular profile picture placeholder
    profile_size = 400
    circular_img = Image.new("RGBA", (profile_size, profile_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(circular_img)
    draw.ellipse([(0, 0), (profile_size, profile_size)], fill=(255, 255, 255), outline=(0, 0, 0), width=10)  # White circle with black stroke

    # Paste the circular image on the background (centered)
    bg.paste(circular_img, ((bg.width - profile_size) // 2, 50), circular_img)

    # Draw user ID on the image, positioned at the bottom
    img_draw = ImageDraw.Draw(bg)
    font_size = 80  # Font size for user ID
    user_id_text = str(user_id).upper()

    # Calculate text width and height for centering
    text_width, text_height = img_draw.textsize(user_id_text, font=ImageFont.load_default())
    text_x = (bg.width - text_width) / 2  # Center horizontally
    text_y = bg.height - text_height - 50  # Position 50 pixels from the bottom

    # Add a shadow effect for readability
    shadow_offset = 3
    img_draw.text((text_x + shadow_offset, text_y + shadow_offset), text=user_id_text, font=ImageFont.load_default(), fill=(0, 0, 0, 128))
    img_draw.text((text_x, text_y), text=user_id_text, font=ImageFont.load_default(), fill=(255, 255, 255))

    # Save the image
    path = f"./userinfo_img_{user_id}.png"
    bg.save(path)
    return path


async def start_command(client, message):
    user_id = message.from_user.id

    # Check if user exists in the database
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        users_collection.insert_one({"user_id": user_id, "amazon_tag": None, "footer": None})
        print(f"User {user_id} added to the database")  # Debugging line
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

    # Generate user's image
    profile_path = None  # Set this to the user's profile image path if available
    user_image_path = await get_userinfo_img(user_id, profile_path)

    try:
        # Send welcome image with caption (optional)
        await message.reply_photo(photo=user_image_path, caption=welcome_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Error sending message: {e}")
