FROM python:3.11-slim

# Install system audio and build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose FastAPI port
EXPOSE 8000

CMD ["python", "main.py"]
