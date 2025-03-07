ARG PYTHON_VERSION=3.12.8
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container.
WORKDIR /ba_stored_procedure_api

# Copy the source code into the container.
COPY . /ba_stored_procedure_api

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the application listens on.
EXPOSE 8016

# Run the application.
CMD ["uvicorn", "radar_stored_procedure_api:stored_app", "--host", "0.0.0.0", "--port", "8016"]
