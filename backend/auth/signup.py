# backend/auth/signup.py
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from jose import jwt

from db import users_collection
from models.user import AuthRequest, AuthResponse
from utils.security import hash_password

# Load env vars (for local dev); in production, AWS provides env directly
load_dotenv()

router = APIRouter()

# -------------------- JWT Config --------------------
SECRET_KEY = os.getenv("SECRET_KEY")     # never hardcode; set as env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week lifetime

# -------------------- Signup endpoint --------------------
@router.post("/signup", response_model=AuthResponse)
async def signup(data: AuthRequest):
    """
    Register a new user.
    - Validates email uniqueness
    - Hashes the password (bcrypt via utils.security)
    - Stores user in MongoDB
    - Returns JWT + user info
    """

    # Check if email is already registered
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password before storing (bcrypt, defined in utils.security)
    hashed = hash_password(data.password)

    # Construct user document for Mongo
    user = {
        "email": data.email,
        "username": data.email.split("@")[0],  # simple username fallback
        "password_hash": hashed,
        "created_at": datetime.utcnow()
    }

    # Insert user document
    result = await users_collection.insert_one(user)
    user_id = str(result.inserted_id)

    # Generate JWT token for immediate login after signup
    token_payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

    # Return data that matches AuthResponse model
    return {
        "email": data.email,
        "id": user_id,
        "token": token
    }
