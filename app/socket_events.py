"""SocketIO olay işleyicileri ve Whisper STT entegrasyonu."""

import os
import tempfile

import whisper
from flask import session
from flask_login import current_user
from flask_socketio import emit

from app import db, socketio
from app.constants import PSIKOLOG_TARZLARI
from app.models import Answer
from app.services import get_ai_response_with_style, check_if_ready_for_diagnosis


# ── Whisper Lazy Loading ────────────────────────────────────

_whisper_model = None


def _get_whisper_model():
    """Whisper modelini lazy olarak yükle (ilk ses kaydında)."""
    global _whisper_model
    if _whisper_model is None:
        from flask import current_app

        model_name = current_app.config["WHISPER_MODEL"]
        print(f"🎤 Whisper '{model_name}' modeli yükleniyor (ilk kullanım)...")
        _whisper_model = whisper.load_model(model_name)
        print(f"✅ Whisper '{model_name}' modeli hazır!")
    return _whisper_model


# ── Ses → Metin ─────────────────────────────────────────────

@socketio.on("audio_message")
def handle_audio(data):
    """Ses kaydını al, Whisper ile metne çevir."""
    from flask import current_app

    print("🎤 Ses kaydı alındı, işleniyor...")
    emit("transcription_status", {"status": "processing"})

    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        model = _get_whisper_model()
        result = model.transcribe(
            tmp_path,
            language="tr",
            temperature=0,
            initial_prompt=current_app.config["WHISPER_INITIAL_PROMPT"],
        )
        text = result["text"].strip()

        os.unlink(tmp_path)
        print(f"📝 Transkripsiyon: {text[:60]}...")

        if not text:
            emit("transcription_status", {"status": "empty"})
            return

        emit("transcription_result", {"text": text})

    except Exception as e:
        print(f"❌ Whisper hatası: {e}")
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        emit("transcription_status", {"status": "error", "message": str(e)})


# ── Kullanıcı Mesajı ────────────────────────────────────────

@socketio.on("user_message")
def handle_message(data):
    """Kullanıcı mesajını işle ve AI yanıtı gönder."""
    user_msg = data["message"]
    tarz = session.get("psikolog_tarz", "profesyonel")
    psikolog = PSIKOLOG_TARZLARI[tarz]

    # Mesajı geçmişe ekle
    session["history"].append({"mesaj": user_msg, "tip": "kullanici"})
    session.modified = True

    # Son psikolog sorusunu bul
    son_soru = ""
    for item in reversed(session["history"]):
        if item.get("tip") == "psikolog" and item.get("soru"):
            son_soru = item["mesaj"]
            break

    # Veritabanına kaydet
    try:
        answer = Answer(
            user_id=current_user.id,
            question_text=son_soru,
            answer_text=user_msg,
        )
        db.session.add(answer)
        db.session.commit()
        print(f"💾 Cevap kaydedildi: {user_msg[:30]}...")
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")

    mesaj_sayisi = sum(
        1 for item in session["history"] if item.get("tip") == "kullanici"
    )
    print(f"🧠 Toplam kullanıcı mesajı: {mesaj_sayisi}")

    # AI yanıtı al
    extended = mesaj_sayisi >= 10
    ai_response = get_ai_response_with_style(
        session["history"], psikolog, extended_mode=extended
    )

    session["history"].append(
        {"mesaj": ai_response, "tip": "psikolog", "soru": True}
    )
    session.modified = True

    emit("ai_response", {"message": ai_response, "psikolog": psikolog["isim"]})

    # READY kontrolü (5+ mesajda)
    if mesaj_sayisi >= 5 and not session.get("ready_sent", False):
        if mesaj_sayisi >= 10:
            print("🟢 10 mesaj — Otomatik READY durumu")
            session["ready_sent"] = True
            session.modified = True
            emit("ready_for_diagnosis", {"ready": True})
        else:
            ready_status = check_if_ready_for_diagnosis(session["history"])
            if ready_status:
                print("✅ LLM READY döndü — Analiz için hazır")
                session["ready_sent"] = True
                session.modified = True
                emit("ready_for_diagnosis", {"ready": True})
            else:
                print("⏳ LLM NOT_READY döndü — Sohbet devam ediyor")
