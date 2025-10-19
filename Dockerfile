FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    ffmpeg \
    libsm6 \
    libxext6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

COPY scripts/startdjango.sh /startdjango
COPY scripts/startceleryworker.sh /startceleryworker
RUN chmod +x /startdjango /startceleryworker \
 && sed -i 's/\r$//' /startdjango /startceleryworker

COPY . /app

EXPOSE 8000

CMD ["/startdjango"]