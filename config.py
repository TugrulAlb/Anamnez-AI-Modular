"""Uygulama yapılandırma ayarları."""

import os


class Config:
    """Temel yapılandırma."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "gizli-key-degistirin")

    # Veritabanı
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///anamnez_gpt.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenRouter API
    OPENROUTER_API_KEY = os.environ.get(
        "OPENROUTER_API_KEY",
        None,  # Üretimde mutlaka .env'de ayarlanmalı
    )
    OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

    # Whisper STT
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
    WHISPER_INITIAL_PROMPT = (
        "Bu bir profesyonel klinik görüşmedir. "
        "Lütfen standart İstanbul Türkçesi ile transkripsiyon yap. "
        "Argo, yerel ağız veya dini kalıplardan kaçın."
    )

    # SocketIO
    MAX_AUDIO_BUFFER = 16 * 1024 * 1024  # 16 MB


class DevelopmentConfig(Config):
    """Geliştirme ortamı."""

    DEBUG = True


class ProductionConfig(Config):
    """Üretim ortamı."""

    DEBUG = False
