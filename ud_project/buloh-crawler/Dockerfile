# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to avoid writing .pyc files and buffer output
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application files into the container
COPY . /app/

RUN package-obfuscate ./

# Expose the necessary ports
EXPOSE 8000

# Set the command to run the appropriate script by default
CMD ["python", "main.py"]
