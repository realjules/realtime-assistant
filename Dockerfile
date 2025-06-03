# Dockerfile for Sasabot project
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create app directory
WORKDIR /app

# Install system dependencies needed for your project
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your project files
COPY . .

# Create data directory for JSON files and set permissions
RUN mkdir -p data data/backups && \
    chmod 755 data data/backups

# Create non-root user for security
RUN groupadd -r sasabot && useradd -r -g sasabot sasabot && \
    chown -R sasabot:sasabot /app

# Switch to non-root user
USER sasabot

# Expose port for Chainlit
EXPOSE 8000

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start Chainlit application
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]