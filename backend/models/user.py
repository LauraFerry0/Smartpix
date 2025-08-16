# backend/models/user.py
from pydantic import BaseModel, EmailStr

# -------------------- Request schema --------------------
class AuthRequest(BaseModel):
    """
    Incoming request body for signup or login.
    - email: must be a valid email address (validated by Pydantic's EmailStr).
    - password: raw password string (will be hashed on signup; verified on login).
    """
    email: EmailStr
    password: str


# -------------------- Response schema --------------------
class AuthResponse(BaseModel):
    """
    Outgoing response returned after successful signup or login.
    Contains:
    - email: the user's email address
    - id: the MongoDB document _id (as a string)
    - token: the signed JWT for authentication
    """
    email: str
    id: str
    token: str
