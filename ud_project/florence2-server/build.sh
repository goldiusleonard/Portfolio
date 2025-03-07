#bin/bash
sudo docker build -t florence2-server .
sudo docker run --runtime nvidia --gpus '"device=0,1,2,3"' --name florence2-server --restart always \
    -d \
    -p 8000:8000 \
    florence2-server