"""HTTP route tanımları (Blueprint)."""

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
)
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash

from app import db
from app.models import User, Answer, TestResult
from app.constants import PSIKOLOG_TARZLARI
from app.services import (
    get_first_greeting,
    get_ai_response_with_style,
    get_summary_response,
)

main_bp = Blueprint("main", __name__)


# ── Kimlik Doğrulama ────────────────────────────────────────

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("main.index"))
        flash("Hatalı kullanıcı adı veya şifre", category="error")
    return render_template("login.html")


@main_bp.route("/logout")
@login_required
def logout():
    session.pop("psikolog_tarz", None)
    session.pop("history", None)
    logout_user()
    return redirect(url_for("main.login"))


# ── Ana Sayfa & Tarz Seçimi ─────────────────────────────────

@main_bp.route("/")
@login_required
def index():
    if "psikolog_tarz" not in session:
        return redirect(url_for("main.select_style"))
    return redirect(url_for("main.question"))


@main_bp.route("/select-style", methods=["GET", "POST"])
@login_required
def select_style():
    if request.method == "POST":
        tarz = request.form.get("tarz")
        if tarz in PSIKOLOG_TARZLARI:
            session["psikolog_tarz"] = tarz
            session["history"] = []

            psikolog = PSIKOLOG_TARZLARI[tarz]
            karsilama = get_first_greeting(psikolog)
            session["history"].append(
                {"mesaj": karsilama, "tip": "psikolog", "soru": True}
            )
            return redirect(url_for("main.question"))

    return render_template("select_style.html", tarzlar=PSIKOLOG_TARZLARI)


@main_bp.route("/close-chat")
@login_required
def close_chat():
    session.pop("history", None)
    session.pop("psikolog_tarz", None)
    return redirect(url_for("main.select_style"))


# ── Görüşme ─────────────────────────────────────────────────

@main_bp.route("/question", methods=["GET", "POST"])
@login_required
def question():
    if "psikolog_tarz" not in session:
        return redirect(url_for("main.select_style"))

    tarz = session["psikolog_tarz"]
    psikolog = PSIKOLOG_TARZLARI[tarz]

    if request.method == "POST":
        cevap = request.form.get("cevap")
        session["history"].append({"mesaj": cevap, "tip": "kullanici"})
        session.modified = True

        # Son psikolog sorusunu bul
        son_soru = ""
        for item in reversed(session["history"]):
            if item.get("tip") == "psikolog" and item.get("soru"):
                son_soru = item["mesaj"]
                break

        answer = Answer(
            user_id=current_user.id,
            question_text=son_soru,
            answer_text=cevap,
        )
        db.session.add(answer)
        db.session.commit()

        soru_sayisi = sum(
            1 for item in session["history"] if item.get("tip") == "kullanici"
        )
        if soru_sayisi >= 5:
            return redirect(url_for("main.result"))

        yeni_mesaj = get_ai_response_with_style(session["history"], psikolog)
        session["history"].append(
            {"mesaj": yeni_mesaj, "tip": "psikolog", "soru": True}
        )
        session.modified = True

    # Son psikolog mesajını bul
    son_psikolog_mesaji = ""
    for item in reversed(session["history"]):
        if item.get("tip") == "psikolog":
            son_psikolog_mesaji = item["mesaj"]
            break

    return render_template(
        "questions.html",
        mesaj=son_psikolog_mesaji,
        psikolog=psikolog,
        history=session["history"],
    )


# ── Sonuç ────────────────────────────────────────────────────

@main_bp.route("/result")
@login_required
def result():

    history = session.get("history", [])
    tarz = session.get("psikolog_tarz", "profesyonel")
    psikolog = PSIKOLOG_TARZLARI.get(tarz, PSIKOLOG_TARZLARI["profesyonel"])

    # Soru-cevap çiftleri
    cevaplar = []
    current_soru = ""
    for item in history:
        if item.get("tip") == "psikolog" and item.get("soru"):
            current_soru = item["mesaj"]
        elif item.get("tip") == "kullanici" and current_soru:
            cevaplar.append({"soru": current_soru, "cevap": item["mesaj"]})
            current_soru = ""

    analiz = get_summary_response(cevaplar)

    test_result = TestResult(
        user_id=current_user.id,
        result_summary=analiz,
        dsm_diagnosis="(otomatik tanı eklenecek)",
        psychologist_note="",
    )
    db.session.add(test_result)
    db.session.commit()

    return render_template("result.html", cevaplar=cevaplar, analiz=analiz)
