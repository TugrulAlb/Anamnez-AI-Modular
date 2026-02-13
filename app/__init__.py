"""Flask uygulama fabrikası (Application Factory Pattern)."""

from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()


def create_app(config_class="config.Config"):
    """Flask uygulamasını oluştur ve yapılandır."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Eklentiler ──────────────────────────────────────────
    db.init_app(app)

    login_manager.login_view = "main.login"
    login_manager.login_message = "Lütfen giriş yapın."
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    socketio.init_app(
        app,
        cors_allowed_origins="*",
        max_http_buffer_size=app.config["MAX_AUDIO_BUFFER"],
    )

    # ── Kullanıcı yükleyiciler ──────────────────────────────
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for("main.login"))

    # ── Blueprint kayıt ─────────────────────────────────────
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    # ── SocketIO olay kayıt ─────────────────────────────────
    from app import socket_events  # noqa: F401

    # ── CLI komutları ────────────────────────────────────────
    @app.cli.command("create-db")
    def create_db_cmd():
        db.create_all()
        print("✅ Veritabanı oluşturuldu.")

    # ── Otomatik kullanıcı seed ──────────────────────────────
    with app.app_context():
        from app.models import User
        from werkzeug.security import generate_password_hash

        db.create_all()  # Tabloları oluştur (yoksa)

        # 'test' kullanıcısı yoksa oluştur
        test_user = User.query.filter_by(username="test").first()
        if not test_user:
            test_user = User(
                username="test",
                password_hash=generate_password_hash("test123", method="pbkdf2:sha256"),
                role="user",
            )
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test kullanıcısı oluşturuldu (username: test, password: test123)")
        else:
            print("ℹ️  Test kullanıcısı zaten mevcut")

    return app
