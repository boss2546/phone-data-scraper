# Standalone Dockerfile for VesselFinder Live Maritime Radar Microservice
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy microservice source code and assets
COPY config/ ./config/
COPY src/ ./src/
COPY run.py .
COPY vesselfinder_studio.html .

# Create data directory with initial structure
RUN mkdir -p data/json data/exports data/images

# Copy existing cached data if present for instant warm boot
COPY data/ ./data/

# Expose port for API and Web Studio
EXPOSE 8000

# Healthcheck to verify the microservice is responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Launch FastAPI Microservice with Uvicorn
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]

