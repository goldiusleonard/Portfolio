# Use nvidia/cuda base image with the appropriate CUDA version
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kuala_Lumpur
ENV LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:/usr/local/cuda/lib64

# Install software-properties-common FIRST
RUN apt-get update && apt-get install -y software-properties-common\
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.10 python3.10-venv python3.10-distutils python3-pip \
    libgl1-mesa-glx \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
    gnupg \
    tar \
    cudnn9-cuda-12 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# Set the working directory
WORKDIR /whisper-server

# Copy requirements and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir ctranslate2==4.5.0 \
    && pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124

# Copy the project files into the container
COPY . .

# Expose necessary ports
EXPOSE 8000

# Set the command to run the FastAPI app
CMD ["python3", "main.py"]