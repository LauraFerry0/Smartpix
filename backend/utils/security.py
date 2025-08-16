# backend/utils/security.py
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    - Returns a salted hash string that should be stored in the database.
    - Bcrypt automatically generates a new random salt each time, so the same
      password will not produce the same hash twice.
    """
    return bcrypt.hash(password)


def verify_password(plain_password: str, hashed: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.
    - Returns True if the password matches the hash, False otherwise.
    - Use this during login to check the provided password against the stored hash.
    """
    return bcrypt.verify(plain_password, hashed)
