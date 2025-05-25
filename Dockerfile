# ---------------------------
# Stage 1: Build stage
# ---------------------------
FROM python:3.11 AS builder

ENV PYTHONBUFFERED 1

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

ENV PYTHONBUFFERED 1

# Install runtime-only dependencies (if needed)
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /venv /venv
COPY scripts/startdjango.sh /startdjango
COPY scripts/startceleryworker.sh /startceleryworker
COPY . /app

ENV PATH="/venv/bin:$PATH"

EXPOSE 8000

CMD ["/startdjango"]