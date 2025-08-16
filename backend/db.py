# backend/db.py
import os
from dotenv import load_dotenv
import motor.motor_asyncio

# Load .env file in local development (ignored in production if not present)
load_dotenv()

# Get MongoDB URI and DB name from environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "smartpix")  # default to "smartpix" if not set

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set")

# Create async client and DB reference
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
images_collection = db["images"]
edits_collection = db["edits"]
