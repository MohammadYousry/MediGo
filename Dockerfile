# Use a lightweight Python 3.10 base image
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies needed for TensorFlow, image processing, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    && apt-get clean

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for the model
RUN mkdir -p /app/models

# Download the model from your now-public GCS URL
RUN wget https://storage.googleapis.com/medi-go-eb65e.firebasestorage.app/models/multitask_lab_reports_model.h5 \
    -O /app/models/multitask_lab_reports_model.h5

# Copy the rest of the app
COPY . .

# Set environment variable for the port
ENV PORT=8080

# Expose the port Uvicorn will run on
EXPOSE 8080

# Start FastAPI using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
