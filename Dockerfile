FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY uc_intg_spotify/ ./uc_intg_spotify/
COPY driver.json .

# Create config directory
RUN mkdir -p /app/config

# Set environment variables
ENV UC_CONFIG_HOME=/app/config
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the integration port
EXPOSE 9090

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash integration
RUN chown -R integration:integration /app
USER integration

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:9090/ || exit 1

# Run the integration
CMD ["python", "-m", "uc_intg_spotify.driver"]