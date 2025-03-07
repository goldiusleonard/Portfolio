# Use official Python base image
FROM python:3.9

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /nile-videoprocess

# Install dependencies for the environment (if necessary)
RUN apt-get update -y && apt-get install -y \
    libgl1-mesa-glx \
    ffmpeg

# Copy all files into the container, including the environment and project files
COPY requirements.txt .

# install dependencies from requirements.txt (if needed, otherwise environment is used)
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install specific versions of PyTorch, torchvision, and torchaudio
RUN pip install torch==2.4.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Copy all files into the container, including the environment and project files
COPY . .

# Expose any necessary ports
EXPOSE 8000

# Set the command to activate the environment and run the FastAPI app
CMD ["python", "main.py"]