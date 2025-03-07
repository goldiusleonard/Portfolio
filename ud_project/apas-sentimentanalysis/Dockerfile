# Use the official Python 3.9 image
FROM python:3.9

# Set the working directory in the container
WORKDIR /apas_sentiment_analysis

# Copy the requirements.txt into the container at /apas_sentiment_analysis
COPY requirements.txt /apas_sentiment_analysis/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /apas_sentiment_analysis
# COPY . /apas_sentiment_analysis/

COPY . .

# Copy the .env file into the container
#COPY .env /apas_sentiment_analysis/.env

# Expose the port the app will run on
EXPOSE 8555

# Set the command to run the appropriate script by default
CMD ["python3", "fastapi_app.py"]