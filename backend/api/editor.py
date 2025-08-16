# backend/api/editor.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from bson import ObjectId
from datetime import datetime
import shutil, os
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os

from db import images_collection, edits_collection
from utils.image_ai import process_image

# Load environment variables (for local dev; in production, the platform sets envs)
load_dotenv()

router = APIRouter()

# -------------------- Auth / JWT config --------------------
# SECRET_KEY is used to verify JWTs created at login.
# Make sure SECRET_KEY is set in your environment (not hardcoded).
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# This defines how Swagger's "Authorize" flow gets a token.
# Note: tokenUrl affects docs UX only; decode logic below enforces auth at runtime.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Extract current user ID ("sub") from the bearer token.
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        # Any error (expired/invalid/signature) → unauthorized
        raise HTTPException(status_code=401, detail="Invalid token")

# -------------------- Local file storage paths --------------------
# Files are saved under ./static. In containerized cloud (App Runner/ECS),
# this storage is ephemeral (lost on restart/scale). For production durability,
# consider swapping these with S3 (store keys in Mongo).
STATIC_DIR = "static"
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
EDIT_DIR = os.path.join(STATIC_DIR, "processed")

# Ensure folders exist at startup (safe if they already exist)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EDIT_DIR, exist_ok=True)

# -------------------- Upload an image --------------------
@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),  # uploaded image file (multipart/form-data)
    user_id: str = Form(...)       # owner's user_id (stringified ObjectId)
):
    # Validate user_id shape (must be a valid ObjectId)
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Save the raw upload to disk (static/uploads/<original_filename>)
    filename = file.filename
    upload_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")

    # Insert metadata for the uploaded image into MongoDB
    try:
        image_doc = {
            "user_id": user_object_id,
            "original_url": f"/static/uploads/{filename}",  # relative URL used by the frontend
            "filename": filename,
            "uploaded_at": datetime.utcnow(),
            "tags": []  # present to match expected schema (extend if you add tagging later)
        }

        result = await images_collection.insert_one(image_doc)

        # Return the new image id and a URL the frontend can request
        return {
            "image_id": str(result.inserted_id),
            "url": image_doc["original_url"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)}")


# -------------------- Edit an image --------------------
@router.post("/edit")
async def edit_image(
    image_id: str = Form(...),   # Mongo _id of the original image (stringified ObjectId)
    edit_type: str = Form(...),  # e.g., "blur", "sharpen" (handled by process_image)
    intensity: int = Form(...),  # edit strength (forwarded to process_image)
    user_id: str = Form(...)     # owner user_id (stringified ObjectId)
):
    # Validate IDs
    try:
        user_object_id = ObjectId(user_id)
        image_object_id = ObjectId(image_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    # Ensure the source image exists
    image_doc = await images_collection.find_one({"_id": image_object_id})
    if not image_doc:
        raise HTTPException(status_code=404, detail="Image not found")

    # Resolve input (uploaded) and output (processed) paths
    input_path = os.path.join(UPLOAD_DIR, image_doc['filename'])
    output_filename = f"{ObjectId()}.jpg"  # unique filename for the edited result
    output_path = os.path.join(EDIT_DIR, output_filename)

    # Perform the edit (your implementation in utils.image_ai.process_image)
    process_image(input_path, output_path, edit_type, intensity)

    # Save edit metadata (linking edited file to the original image)
    edit_doc = {
        "image_id": image_object_id,
        "edited_url": f"/static/processed/{output_filename}",  # relative URL to the processed image
        "prompt": f"{edit_type} with intensity {intensity}",   # simple descriptor for audit/UX
        "edited_at": datetime.utcnow(),
        "user_id": user_object_id,
        "edit_type": edit_type,
        "intensity": intensity
    }

    await edits_collection.insert_one(edit_doc)
    return {"edited_url": edit_doc["edited_url"]}
