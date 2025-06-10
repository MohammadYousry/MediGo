# Use a Python 3.8 slim image based on Debian Bookworm (newer than Bullseye)
# Bookworm is the current stable release for Debian and generally has more up-to-date packages.
FROM python:3.8-slim-bookworm

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for some Python packages (e.g., EasyOCR, TensorFlow)
# Combined into a single RUN command for better Docker layer caching and smaller image size.
# Removed libxrender-dev as it's typically not needed at runtime, only for development.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker layer caching.
# If requirements.txt doesn't change, this layer (and subsequent pip install) won't rebuild.
COPY requirements.txt .

# Install Python dependencies from requirements.txt
# This will now include 'python-multipart' as you've added it.
# Removed the separate 'pip install arabic-reshaper' as it should be in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Set environment variable for the port
ENV PORT=8080

# Expose the port (informative, but Cloud Run handles this internally)
EXPOSE 8080

# Command to run your FastAPI application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
