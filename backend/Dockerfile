# Foodberg Production Dockerfile
# Includes Litestream for database replication
#
# Build: docker build -t foodberg-api .
# Run: docker run -p 8000:8000 \
#        -e AWS_ACCESS_KEY_ID=xxx \
#        -e AWS_SECRET_ACCESS_KEY=xxx \
#        -e LITESTREAM_BUCKET=your-bucket \
#        foodberg-api

FROM python:3.11-slim

# Install Litestream
RUN apt-get update && apt-get install -y wget && \
    wget https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.deb && \
    dpkg -i litestream-v0.3.13-linux-amd64.deb && \
    rm litestream-v0.3.13-linux-amd64.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy Litestream config
COPY litestream.yml /etc/litestream.yml

# Create data directories
RUN mkdir -p /app/data/collected /app/data/backups /app/logs

# Environment
ENV ENV=production
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start script: restore database, then run Litestream with app
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
