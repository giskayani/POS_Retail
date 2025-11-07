# ============================
# Builder Stage
# ============================
FROM python:3.11.8-slim-bullseye AS builder

# Install system dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================
# Runtime Stage
# ============================
FROM python:3.11.8-slim-bullseye

# Install only what’s needed to run
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy only necessary source code
COPY . .

# Expose port (Cloud Run default: 8080)
EXPOSE 8080

# Gunicorn command (use eventlet for async if needed)
CMD ["gunicorn", "--worker-class", "eventlet", "--bind", "0.0.0.0:8080", "--workers", "1", "-t", "30    ", "app:app"]
