# Use an official Python 3.9.18 runtime as the base image
FROM python:3.9.18-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get update && apt-get install -y  libmariadbd-dev 

# Set the working directory inside the container
WORKDIR /ADA

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip3.9 install --no-cache-dir --upgrade pip
RUN pip3.9 install --no-cache-dir -r requirements.txt

COPY . .

RUN package-obfuscate ./

EXPOSE 8000

CMD ["python3", "main.py"]
