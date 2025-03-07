# Use an official Python 3.10.11 runtime as the base image
FROM python:3.10.11

# Set working directory in container
WORKDIR /karun_summary_agent

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Expose port for FastAPI
EXPOSE 8000

# Command to run the FastAPI server
CMD ["python", "karun_fastapi.py"]
