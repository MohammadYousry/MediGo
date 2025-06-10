# Use a lightweight Python 3.10 base image
FROM python:3.10-slim-bullseye

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (for TensorFlow, Pillow, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    && apt-get clean

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create model directory
RUN mkdir -p /app/models

# Download the ML model from GCS (replace URL if your file is private)
RUN wget https://storage.googleapis.com/medi-go-eb65e.firebasestorage.app/models/multitask_lab_reports_model.h5 -O /app/models/multitask_lab_reports_model.h5

# Copy the rest of the app
COPY . .

# Set environment variable (optional)
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
