# backend/auth/login.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

from db import users_collection
from models.user import AuthResponse
from utils.security import verify_password

# Load env vars from .env during local dev; in prod, the platform supplies them
load_dotenv()

router = APIRouter()

# -------------------- JWT / Auth config --------------------
# SECRET_KEY signs the JWT; keep it in an environment variable (never hardcode).
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
# Token lifetime: 7 days (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# For Swagger's "Authorize" button (OAuth2 password flow)
# tokenUrl should point to this router's login endpoint, including the /api prefix used in app.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# -------------------- Login endpoint --------------------
@router.post("/login", response_model=AuthResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Accepts x-www-form-urlencoded form with:
      - username: email address (OAuth2 spec uses 'username' field)
      - password: user password
    Returns AuthResponse with email, id, and JWT if credentials are valid.
    """
    # Look up the user by email
    user = await users_collection.find_one({"email": form_data.username})
    # Check user exists AND password matches (using your bcrypt-based helper)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create JWT payload with subject (user id) and expiry
    user_id = str(user["_id"])
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    # Encode and sign the JWT
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Respond with a consistent auth model (typed by AuthResponse)
    return {
        "email": user["email"],
        "id": user_id,
        "token": token
    }

# -------------------- Optional helper for protected routes --------------------
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency you can add to any protected endpoint:
      current_user: str = Depends(get_current_user)
    It decodes the bearer token and returns the user id ('sub').
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
