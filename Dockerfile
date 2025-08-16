FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app

#Install backend deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

#Copy the code
COPY backend /app/backend

EXPOSE 8000
USER appuser

#Production server: Gunicorn + Uvicorn Worker
CMD ["gunicorn", "backend.app:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "-w", "2", "--timeout", "60"]