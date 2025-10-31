FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (optional, kept minimal for SQLite)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY scooters/ ./scooters/

EXPOSE 8000

# Run migrations and start the development server
CMD ["sh", "-c", "python scooters/manage.py migrate && python scooters/manage.py runserver 0.0.0.0:8000"]


