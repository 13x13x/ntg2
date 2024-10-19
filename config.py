import os
import uuid
from pyrogram import Client
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# MongoDB URI
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
    print("Connected to MongoDB")
except ServerSelectionTimeoutError as e:
    print(f"Could not connect to MongoDB: {e}")
