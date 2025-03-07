# Use an official Python 3.11 runtime as the base image
FROM python:3.11.5-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    python3-pip \
    pkg-config \
    libmariadbd-dev && \
    rm -rf /var/lib/apt/lists/*  # Clean up apt cache to reduce image size

# Set the working directory inside the container
WORKDIR /ADA

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port for FastAPI app
EXPOSE 8001

# Install supervisord to manage multiple processes
RUN pip install supervisor

# Create a supervisord configuration file
COPY supervisord.conf /etc/supervisord.conf

# Define the command to run the supervisord, which will manage FastAPI and Celery worker
CMD ["supervisord", "-c", "/etc/supervisord.conf"]

# CMD ["python3", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]

# build: docker build -t yankechil-fastapi-celery-app .
# run: docker run -d --name yankechil-app -p 8001:8001 yankechil-fastapi-celery-app:latest
# stop: docker stop yankechil-app
# docker rm yankechil-app