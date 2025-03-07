# Stage 1: Build Stage
FROM python:3.11.9-slim-bullseye AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libmariadbd-dev \
    ffmpeg \
    build-essential \
    python3-pymysql \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Upgrade pip and install dependencies into a separate folder
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/dependencies -r requirements.txt

# Stage 2: Runtime Stage
FROM python:3.11.9-slim-bullseye

# Install only necessary runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libmariadbd-dev \
    ffmpeg \
    build-essential \
    python3-pymysql \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the pre-installed dependencies from the builder stage
COPY --from=builder /dependencies /usr/local

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
