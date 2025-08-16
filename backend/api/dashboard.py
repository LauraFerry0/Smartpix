# router module (e.g., backend/dashboard.py)
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from bson import ObjectId
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os

from db import images_collection, edits_collection

router = APIRouter()

# ----- File paths (local container storage) -----
# These paths are used to read/write files on the container filesystem.
# NOTE: In AWS (App Runner/ECS), this storage is ephemeral and disappears on restart/scale.
# For production, consider moving to S3 and saving only keys/URLs in Mongo.
STATIC_DIR = "static"
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
EDIT_DIR = os.path.join(STATIC_DIR, "processed")

# ----- Auth config (JWT) -----
# Load env variables from .env in local dev; in production, envs come from the platform.
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# The tokenUrl here is used by Swagger's "Authorize" button only.
# It does not affect validation logic—just the docs OAuth flow.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Base URL used to build fully-qualified links returned in JSON responses below.
# In local dev this points to your Uvicorn server; for prod you can:
#   - leave BASE_URL and return relative paths (frontends prepend their origin), OR
#   - set it via env (e.g., API_BASE_URL) and compose absolute URLs.
BASE_URL = "http://localhost:8000"  # Change in production


# ----- Helper: extract current user id from JWT -----
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # we expect "sub" to contain the user's ObjectId string
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        # Any decode/expiry/signature error → unauthorized
        raise HTTPException(status_code=401, detail="Invalid token")


# ----- Fetch all images for a given user (public endpoint taking user_id path param) -----
@router.get("/user-images/{user_id}")
async def get_user_images_by_id(user_id: str):
    # Validate and convert the provided user_id to ObjectId
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Query images owned by that user
    images_cursor = images_collection.find({"user_id": user_object_id})
    images = []

    # For each image, try to find a corresponding edit document
    async for image in images_cursor:
        edit = await edits_collection.find_one({"image_id": image["_id"]})

        # Build response fields; original/edited URLs are assembled against BASE_URL
        images.append({
            "id": str(image["_id"]),
            "name": image.get("filename", "Unnamed"),
            "originalImageUrl": f"http://localhost:8000{image.get('original_url')}",
            "editedImageUrl": f"http://localhost:8000{edit.get('edited_url')}" if edit else None,
            # Use uploaded_at if present; otherwise fallback to edited_at if we have an edit doc
            "createdAt": image.get("uploaded_at") or (edit.get("edited_at") if edit else None),
            "editType": edit.get("edit_type") if edit else None
        })

    return images


# ----- Delete an image (auth required) -----
@router.delete("/images/{image_id}")
async def delete_image(image_id: str, current_user: str = Depends(get_current_user)):
    # Validate IDs
    try:
        image_object_id = ObjectId(image_id)
        user_object_id = ObjectId(current_user)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Ensure the image exists and belongs to the caller
    image = await images_collection.find_one({"_id": image_object_id, "user_id": user_object_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete DB docs (image + any associated edits)
    await images_collection.delete_one({"_id": image_object_id})
    await edits_collection.delete_many({"image_id": image_object_id})

    # Best-effort delete of the original file; ignore if already missing
    try:
        os.remove(os.path.join(UPLOAD_DIR, image["filename"]))
    except FileNotFoundError:
        pass

    return {"status": "deleted"}


# ----- Download the edited image file (auth required) -----
@router.get("/images/{image_id}/download")
async def download_edited_image(image_id: str, current_user: str = Depends(get_current_user)):
    # Validate IDs
    try:
        image_object_id = ObjectId(image_id)
        user_object_id = ObjectId(current_user)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Find an edit that belongs to this user/image
    edit = await edits_collection.find_one({"image_id": image_object_id, "user_id": user_object_id})
    if not edit:
        raise HTTPException(status_code=404, detail="Edited image not found")

    # Map stored URL/path to a real file on disk; serve via FileResponse
    filename = edit["edited_url"].split("/")[-1]
    filepath = os.path.join(EDIT_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(filepath, media_type="image/jpeg", filename=filename)


# ----- Download the original uploaded image (auth required) -----
@router.get("/images/{image_id}/original")
async def download_original_image(image_id: str, current_user: str = Depends(get_current_user)):
    # Validate IDs
    try:
        image_object_id = ObjectId(image_id)
        user_object_id = ObjectId(current_user)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Ensure image exists and belongs to the caller
    image = await images_collection.find_one({"_id": image_object_id, "user_id": user_object_id})
    if not image:
        raise HTTPException(status_code=404, detail="Original image not found")

    # Map stored filename to disk path; serve file
    filename = image["filename"]
    filepath = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(filepath, media_type="image/png", filename=filename)
