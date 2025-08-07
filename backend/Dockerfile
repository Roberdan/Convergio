# 🐍 Convergio Backend - Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY src/ /app/src/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

LABEL org.opencontainers.image.title="Convergio Backend"
LABEL org.opencontainers.image.description="AI-powered business orchestration platform backend"
LABEL org.opencontainers.image.source="https://github.com/Roberdan/Convergio"
LABEL org.opencontainers.image.licenses="CC-BY-NC-SA-4.0"
LABEL org.opencontainers.image.authors="Roberto D'Angelo <roberdan@fightthestroke.org>"

# 🔧 Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 📦 Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 👤 Create non-root user
RUN groupadd -r convergio && useradd -r -g convergio convergio

# 📁 Set working directory
WORKDIR /app

# 📦 Copy requirements first (for better caching)
COPY requirements.txt .

# 🔧 Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 📁 Copy application code
COPY . .

# 👤 Change ownership to non-root user
RUN chown -R convergio:convergio /app

# 🔄 Switch to non-root user
USER convergio

# 🔍 Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# 🚀 Expose port
EXPOSE 9000

# 🎯 Default command
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1"]