"""SQLAlchemy veritabanı modelleri."""

from datetime import datetime

from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    """Kullanıcı modeli."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(50), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Answer(db.Model):
    """Cevap modeli — her soru-cevap çifti için bir kayıt."""

    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    question_text = db.Column(db.Text, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TestResult(db.Model):
    """Test sonucu modeli — görüşme sonu analiz raporu."""

    __tablename__ = "test_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    result_summary = db.Column(db.Text, nullable=True)
    dsm_diagnosis = db.Column(db.Text, nullable=True)
    psychologist_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
