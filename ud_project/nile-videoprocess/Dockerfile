# Use official Python base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /nile-videoprocess

# Copy all files into the container, including the environment and project files
COPY requirements.txt .

# Install dependencies for the environment (if necessary)
RUN apt-get update -y && apt-get install -y \
    libgl1-mesa-glx \
    ffmpeg && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Copy all files into the container, including the environment and project files
COPY . .

RUN package-obfuscate ./

# Expose any necessary ports
EXPOSE 8000

# Set the command to activate the environment and run the FastAPI app
CMD ["python", "main.py"]
