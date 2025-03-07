#bin/bash
sudo docker build -t nile-videoprocess .
sudo docker run --runtime nvidia --gpus all --name nile-videoprocess --restart always \
    -d \
    -p 8008:8000 \
    nile-videoprocess:latest