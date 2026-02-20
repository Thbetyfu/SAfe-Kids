FROM python:3.11-slim

LABEL maintainer="SafeKid Flash <safekid@dev.local>"
LABEL description="SafeKid Flash — Parental Control & Kid Launcher"
LABEL version="0.7.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY safekid/  safekid/
COPY config/   config/

# Create non-root user for security
RUN useradd -r -s /bin/false safekid
USER safekid

# Expose port
EXPOSE 5556

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5556/api/status || exit 1

# Run server
CMD ["python", "safekid/kid_ui/launcher_server.py"]
