# Lightweight Web Interface Container (Cloud-Only Architecture)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SIMULATION_MODE=cloud

# Install system dependencies including Node.js and pnpm
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pnpm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Build frontend
RUN echo "=== DIAGNOSTIC: Building frontend in Dockerfile ===" && \
    echo "Node.js version: $(node --version)" && \
    echo "NPM version: $(npm --version)" && \
    echo "PNPM version: $(pnpm --version)" && \
    echo "Frontend directory contents: $(ls -la frontend/)" && \
    cd frontend && \
    echo "Installing frontend dependencies with pnpm..." && \
    pnpm install && \
    echo "Building frontend..." && \
    pnpm run build && \
    echo "Frontend build completed" && \
    echo "Frontend dist contents: $(ls -la dist/)" && \
    cd .. && \
    echo "=== DIAGNOSTIC: Frontend build complete ==="

# Create data directory for local storage (minimal)
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start the application
CMD ["python", "backend/f_backend.py"]
