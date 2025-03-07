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


# Install the Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


EXPOSE 8002

CMD ["python3", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8002"]




