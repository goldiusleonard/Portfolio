#bin/bash
sudo docker build -t volga-audioprocess .
sudo docker run --runtime nvidia --gpus all --name volga-audioprocess --restart always \
    -d \
    -p 8007:8007 \
    volga-audioprocess:latest