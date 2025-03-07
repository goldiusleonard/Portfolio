# Use an official Python 3.11 runtime as the base image
FROM python:3.13.1

# Set the working directory in the container
WORKDIR /amu-category

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory into the container
COPY . .

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["python3", "main_api.py"]
