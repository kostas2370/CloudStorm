# ---------------------------
# Stage 1: Build stage
# ---------------------------
FROM python:3.11 AS builder

ENV PYTHONBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    ffmpeg libsm6 libxext6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install Python dependencies into a virtual environment
RUN python -m venv /venv \
 && /venv/bin/pip install --upgrade pip \
 && /venv/bin/pip install -r requirements.txt --ignore-installed

# ---------------------------
# Stage 2: Final image
# ---------------------------
FROM python:3.11-slim AS final

ENV PYTHONBUFFERED=1

# Install runtime-only dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /venv /venv

# Copy startup scripts and ensure they are executable + LF
COPY scripts/startdjango.sh /startdjango
COPY scripts/startceleryworker.sh /startceleryworker
RUN chmod +x /startdjango /startceleryworker \
 && sed -i 's/\r$//' /startdjango /startceleryworker

# Copy the rest of the app
COPY . /app

# Update PATH to use the venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 8000

# Default command to start Django
CMD ["/startdjango"]