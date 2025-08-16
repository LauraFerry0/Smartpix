
Smartpix
========

Smartpix is an AI-powered image editing and management platform.
It allows users to sign up, log in, upload images, and apply AI-based enhancements.

Built with FastAPI, MongoDB Atlas, and OpenAI’s Image API.
Frontend: React (GitHub Pages)
Backend: Dockerized FastAPI

----------------------
Features
----------------------
- Authentication (Signup & Login with JWT tokens)
- Security (Password hashing with bcrypt)
- Image Editing (Enhance, restore, retouch, style transfer, background removal)
- Database (MongoDB Atlas)
- Deployment (Dockerized backend, static frontend)
- CORS-friendly (Configurable origins for local testing and production)

----------------------
Project Structure
----------------------
Smartpix/
  backend/              FastAPI backend
    api/                API routes (editor, dashboard)
    auth/               Authentication (signup, login)
    models/             Pydantic models
    utils/              Security & AI helpers
    static/             Static assets
    app.py              FastAPI entrypoint
    db.py               MongoDB connection
    .env.example        Example environment variables
  Dockerfile            Backend container definition
  .dockerignore         Docker ignore rules

----------------------
Setup & Installation
----------------------
1. Clone the repository:
   git clone https://github.com/LauraFerry0/Smartpix.git
   cd Smartpix/backend

2. Create an environment file:
   Copy .env.example to .env and fill in your secrets.

3. Install dependencies:
   python -m venv .venv
   source .venv/bin/activate   (Linux/Mac)
   .venv\Scripts\activate    (Windows PowerShell)
   pip install -r requirements.txt

4. Run locally:
   uvicorn app:app --reload

Docs available at http://localhost:8000/docs

----------------------
Docker Deployment
----------------------
Build and run the backend:
   docker build -t smartpix-backend .
   docker run -p 8000:8000 --env-file backend/.env smartpix-backend

----------------------
Frontend
----------------------
Frontend is served separately (e.g., GitHub Pages).
Ensure ALLOWED_ORIGINS in .env includes your deployed frontend URL.

----------------------
License
----------------------
MIT License
Educational project
