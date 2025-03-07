# Use an official Python 3.11 runtime as the base image
FROM python:3.10.14-bookworm
# Install system dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get update && apt-get install -y python3.11 python3-pip pkg-config
RUN apt-get update && apt-get install -y  libmariadbd-dev 
RUN apt-get update && apt-get install -y python3-pymysql

# Set the working directory inside the container
WORKDIR /

# Copy the requirements file into the container
COPY requirements.txt .


# Install the Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

#CMD ["python3", "-m", "uvicorn", "uvicorn main:app --host 0.0.0.0 --port 8000", "--host", "0.0.0.0"]

#CMD "/usr/local/bin/python3.9" "-m" "gunicorn" "Camel-Agent:app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]