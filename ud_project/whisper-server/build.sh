#bin/bash
sudo docker build -t whisper-server .
sudo docker run --runtime nvidia --gpus all --name whisper-server --restart always \
    -d \
    -p 8003:8000 \
    whisper-server:latest