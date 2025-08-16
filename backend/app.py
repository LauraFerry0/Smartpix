# backend/app.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import routers (auth & API endpoints)
from auth import signup, login
from api import editor, dashboard

# --------------------------------------------------------
# Create the FastAPI application instance
# --------------------------------------------------------
app = FastAPI()

# --------------------------------------------------------
# CORS configuration
# --------------------------------------------------------
# Read allowed origins from environment variable ALLOWED_ORIGINS.
# - Value should be a comma-separated list of URLs, e.g.:
#   "http://localhost:5173,https://username.github.io,https://username.github.io/repo"
# - In local dev: set ALLOWED_ORIGINS=http://localhost:5173
# - In production: set ALLOWED_ORIGINS to your GitHub Pages (or custom domain) URLs
_env_origins = os.getenv("ALLOWED_ORIGINS")
allowed_origins = [o.strip() for o in _env_origins.split(",")] if _env_origins else []

# Attach the CORS middleware so browsers can call the API from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------
# Static file serving
# --------------------------------------------------------
# Mount the local "static" folder at /static.
# Used by the editor/dashboard code to serve uploaded/processed images.
# NOTE: In AWS App Runner, this storage is ephemeral — consider moving to S3
#       if you need persistence across restarts or multiple instances.
app.mount("/static", StaticFiles(directory="static"), name="static")

# --------------------------------------------------------
# API routers
# --------------------------------------------------------
# Mount each router under the /api prefix.
# Each router defines its own paths (e.g., /signup, /login, /editor, /dashboard).
app.include_router(signup.router, prefix="/api")
app.include_router(login.router, prefix="/api")
app.include_router(editor.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# --------------------------------------------------------
# Optional: Health check endpoint
# --------------------------------------------------------
# AWS App Runner and other platforms often use this for liveness checks.
@app.get("/healthz")
def health():
    return {"status": "ok"}
