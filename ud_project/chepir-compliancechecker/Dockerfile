# Use an official Python 3.10.11 runtime as the base image
FROM python:3.10.11

# Set working directory in container
WORKDIR /chepir_compliance_checker_agent

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p logs data output references

# Expose port for FastAPI
EXPOSE 8050

# Command to run the FastAPI server
CMD ["python", "chepir_fastapi_v2.py"]