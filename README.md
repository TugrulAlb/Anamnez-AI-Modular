# 🧠 Anamnez AI

**AI-Powered Clinical Anamnesis Assistant**  
A real-time voice-to-structured-report system for medical professionals, leveraging local speech-to-text (OpenAI Whisper) and large language models for intelligent clinical documentation.

---

## 📋 Overview

Anamnez AI is a full-stack clinical assistant application designed to streamline patient anamnesis collection. It captures patient interviews via voice, transcribes them locally using OpenAI Whisper STT, and generates structured medical reports through LLM-powered analysis — all while ensuring data privacy and offline capability.

**Key differentiators:**
- **100% Local STT**: No dependency on cloud APIs for voice transcription (HIPAA/GDPR-friendly).
- **Real-time processing**: WebSocket-based architecture for instant feedback.
- **Modular & scalable**: Clean separation of concerns using Flask Blueprints.
- **Production-ready**: Fully containerized with Docker Compose for one-command deployment.

---

## ✨ Key Features

- 🎤 **Real-time Speech-to-Text**: Browser-based audio capture → Local Whisper transcription (Turkish optimized)
- 🤖 **AI Report Generation**: LLM-powered (OpenRouter API) psychological analysis and structured summaries
- 👨‍⚕️ **Multi-Persona Psychologists**: 4 distinct AI counselor personalities (empathetic, professional, direct, warm)
- 🔒 **Session Management**: Flask-Login authentication with role-based access control
- 📊 **SQLite Persistence**: Patient answers and test results stored with SQLAlchemy ORM
- 🌐 **WebSocket Communication**: Flask-SocketIO for bidirectional real-time messaging
- 🐳 **Docker Ready**: One-command deployment with persistent Whisper model caching
- 🌙 **Dark Mode**: Full UI theme switcher with localStorage persistence

---

## 🛠️ Tech Stack

### Backend
- **Python 3.10+** (Type-hinted, modular design)
- **Flask 3.1** (Blueprints for route separation)
- **Flask-SocketIO 5.6** (Real-time WebSocket events)
- **Flask-SQLAlchemy 3.1** (ORM layer)
- **Flask-Login 0.6** (Session auth)
- **OpenAI Whisper** (Local STT — `small` model, ~461MB)

### Frontend
- **HTML5 + Tailwind CSS 3.x** (Responsive UI)
- **Socket.IO Client 4.7** (WebSocket connection)
- **MediaRecorder API** (Browser audio capture)
- **html2pdf.js** (Client-side PDF export)

### DevOps
- **Docker + Docker Compose** (Containerization)
- **FFmpeg** (Audio processing for Whisper)
- **Persistent Volumes** (Whisper model cache to prevent re-downloads)

### External Services
- **OpenRouter API** (LLM inference — GPT-3.5-turbo)

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (macOS/Windows) or **Docker Engine + Docker Compose** (Linux)
- **8GB+ RAM** recommended (Whisper model loading)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/anamnez-ai.git
   cd anamnez-ai
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   ```
   http://localhost:5001
   ```

### First-time Setup
On the first launch, Whisper will download the `small` model (~461MB) to `/root/.cache/whisper` inside the container. This is cached in a persistent volume, so subsequent restarts are instant.

---

## 📁 Project Structure

```
Anamnez-GPT/
├── run.py                      # Application entry point
├── config.py                   # Environment-based configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # Multi-container orchestration
├── .dockerignore               # Build context exclusions
├── .env.example                # Environment variable template
├── .gitignore                  # Version control exclusions
│
├── app/                        # Main application package
│   ├── __init__.py             # Flask factory (create_app)
│   ├── models.py               # SQLAlchemy models (User, Answer, TestResult)
│   ├── routes.py               # HTTP routes (Blueprint)
│   ├── socket_events.py        # SocketIO event handlers + Whisper integration
│   ├── services.py             # Business logic (LLM API calls)
│   ├── constants.py            # Static data (psychologist personas)
│   │
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── login.html
│   │   ├── select_style.html
│   │   ├── questions.html      # Real-time chat interface
│   │   └── result.html         # AI-generated report
│   │
│   └── static/                 # CSS/JS assets (currently inline in templates)
│
└── instance/                   # Runtime data (SQLite DB)
    └── anamnez_gpt.db
```

---

## 🧪 Usage

### 1. Login
**Default Test Credentials** (Auto-seeded on first launch):
```
Username: test
Password: test123
```

> **Note**: To make the system ready-to-use out of the box, an automatic database seeding mechanism has been implemented within the application factory. When deployed in a new environment, the default test account is automatically created without manual database intervention. This ensures zero-friction onboarding for demonstrations and testing.

<details>
<summary>Manual user creation (optional)</summary>

You can also create additional users via Flask shell:
```bash
docker compose exec anamnez-ai flask shell
>>> from app.models import User, db
>>> from werkzeug.security import generate_password_hash
>>> user = User(username='doctor', password_hash=generate_password_hash('password'), role='user')
>>> db.session.add(user)
>>> db.session.commit()
```
</details>

### 2. Select AI Psychologist
Choose from 4 personas:
- **İrem** (Warm & Friendly)
- **Tuğrul** (Professional & Experienced)
- **Yasemin** (Empathetic & Emotional)
- **Ali** (Realistic & Direct)

### 3. Conduct Interview
- **Type**: Use text input for written responses
- **Voice**: Click 🎤 to record audio (Whisper transcribes locally)
- AI adapts questioning based on conversation depth (5-10 messages)

### 4. View Report
After sufficient data collection, a structured psychological observation is generated and can be exported as PDF.

---

## 🏗️ Architecture Highlights

### Modular Monolith Pattern
The application follows a **Blueprint-based modular design**, separating concerns into:
- **Routes** (`app/routes.py`) → HTTP endpoints
- **SocketIO Events** (`app/socket_events.py`) → Real-time communication
- **Services** (`app/services.py`) → External API integrations
- **Models** (`app/models.py`) → Data layer

This enables **independent testing, gradual microservice extraction**, and **team-based feature development**.

### Lazy Loading Optimization
Whisper model (461MB) is loaded **only on the first audio transcription request**, not at startup — reducing cold start time from ~30s to <3s.

### Environment Configuration
The `config.py` module supports multiple environments:
- `DevelopmentConfig` (debug=True, verbose logging)
- `ProductionConfig` (debug=False, gunicorn-ready)

---

## 🔐 Security Considerations

- **Environment Variables**: API keys stored in `.env` (excluded from Git)
- **Password Hashing**: PBKDF2-SHA256 via Werkzeug
- **CSRF Protection**: Built-in Flask-WTF integration (future enhancement)
- **Local STT**: No patient data sent to third-party transcription services

---

## 🐳 Docker Details

### Dockerfile
- Base: `python:3.10-slim`
- System deps: `ffmpeg`, `build-essential`, `git`
- Layer caching: `requirements.txt` copied first for faster rebuilds
- Non-root user: Future TODO for security hardening

### docker-compose.yml
- **Port mapping**: `5001:5001`
- **Volumes**:
  - `whisper-cache:/root/.cache/whisper` (persistent model storage)
  - `./instance:/app/instance` (SQLite database)
- **Environment**: `.env` file auto-loaded

---

## 📊 Performance Notes

- **First audio transcription**: ~6-10s (model loading + inference)
- **Subsequent transcriptions**: ~1-2s (model cached in memory)
- **Whisper model size**: 461MB (small), 244MB (base), 1.5GB (medium)
- **LLM response time**: 2-5s (depends on OpenRouter load)

---

## 🛣️ Roadmap

- [ ] PostgreSQL migration for production
- [ ] Redis session store for horizontal scaling
- [ ] Celery task queue for async LLM processing
- [ ] DICOM integration for medical imaging
- [ ] Multi-language Whisper support (currently Turkish-optimized)
- [ ] Gunicorn + Nginx production deployment guide

---

## 🤝 Contributing

This is a portfolio project demonstrating:
- Clean architecture principles
- Production-grade Docker setup
- Real-time WebSocket handling
- Local AI model integration

Feel free to fork and adapt for your use case.

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Tuğrul**  
*Full-Stack Developer | AI Engineering Enthusiast*

Built with Flask, Whisper, and a passion for healthcare tech.

---

**⚠️ Disclaimer**: This application is for **educational and research purposes only**. It is **not** a replacement for professional medical diagnosis. Always consult qualified healthcare providers for clinical decisions.
