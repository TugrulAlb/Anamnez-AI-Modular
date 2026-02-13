# ── Build Stage ──────────────────────────────────────────────
FROM python:3.10-slim AS base

# Sistem bağımlılıkları (ffmpeg + Whisper derleme araçları)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Önce sadece requirements.txt kopyala (Docker cache optimizasyonu)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Port
EXPOSE 5001

# Giriş noktası
CMD ["python", "run.py"]
