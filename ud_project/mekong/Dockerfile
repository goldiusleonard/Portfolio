# Use an official Python 3.11 runtime as the base image
FROM python:3.11.5-bookworm
# Install system dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get update && apt-get install -y python3.11 python3-pip pkg-config
RUN apt-get update && apt-get install -y  libmariadbd-dev 

# Set the working directory inside the container
WORKDIR /ADA

# Copy the requirements file into the container
COPY requirements.txt .

# I am adding this line


# Install the Python dependencies
RUN pip3.11 install --no-cache-dir --upgrade pip
RUN pip3.11 install --no-cache-dir -r requirements.txt

COPY . .

RUN package-obfuscate ./

EXPOSE 8000

# CMD ["python3", "-m", "uvicorn", "Agent_Mekong:app", "--host", "0.0.0.0"]
# CMD ["/Users/avinashkakumanu/Documents/Agent_Mekong/Dockerfile", "Agent_Mekong.py"]
#CMD ["python3","Agent_Mekong.py"]
CMD ["python3", "-m", "uvicorn", "Mekong_Agent:app", "--host", "0.0.0.0"]

