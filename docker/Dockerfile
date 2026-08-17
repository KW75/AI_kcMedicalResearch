# docker/Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching).
# requirements-base.txt only: excludes dev tools (pytest), Windows-only
# packages (pywin32), and the optional OCR stack (easyocr pulls ~2GB of
# PyTorch, and OCR also needs Tesseract/Poppler system binaries that are
# not installed in this image).
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt

# Copy the rest of the application
COPY . .

# Create directories for mounted volumes
RUN mkdir -p /app/input /app/output /app/data /app/reports

# Expose ports
EXPOSE 8501 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CLI_THEME=dark

# Ensure SOURCE_CODE is in Python path
ENV PYTHONPATH=/app:/app/SOURCE_CODE

# Default command (can be overridden)
# Now points to SOURCE_CODE/main.py
CMD ["python", "SOURCE_CODE/main.py"]