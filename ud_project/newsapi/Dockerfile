# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to avoid writing .pyc files and buffer output
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . /app/

RUN package-obfuscate ./

# Expose the necessary ports
EXPOSE 8000

# Set the command to run the appropriate script by default
CMD ["python", "main.py"]
