FROM python:3.11-slim

# Wingman runs as non-root for security
RUN useradd -m -u 1000 wingman && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy verification code
COPY --chown=wingman:wingman . .

USER wingman

# Health check to ensure independence
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:9090/health || exit 1

CMD ["python", "-u", "wingman_verifier.py"]
