FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Added 'curl' to the apt-get list for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copying scripts specifically
COPY scripts/startdjango.sh /startdjango
COPY scripts/startceleryworker.sh /startceleryworker

# The sed command is great—it double-fixes any Windows line-ending issues
RUN chmod +x /startdjango /startceleryworker \
 && sed -i 's/\r$//' /startdjango /startceleryworker

# Copy the whole project
COPY . /app

EXPOSE 8000

CMD ["/startdjango"]