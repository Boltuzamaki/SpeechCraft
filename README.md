<div align="center">

<img src="frontend/app/static/img/video-placeholder.svg" width="80" alt="SpeechCraft Logo"/>

# 🎙️ SpeechCraft

### Open-Source AI-Powered Speech Transcription Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**SpeechCraft** is a free, open-source platform that transcribes audio and video files into editable, timestamped text — then lets you embed styled subtitles back into your videos.
No SaaS fees. No data leaving your infrastructure. Fully self-hosted.

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Configuration](#-configuration) · [Roadmap](#-roadmap) · [Contributing](#-contributing)

---

</div>

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎵 **Multi-format Upload** | MP3, WAV, OGG, M4A, FLAC, AAC, WebM, MP4, AVI, MOV, MKV |
| 🎙️ **Live Recording** | Record directly in the browser and transcribe instantly |
| 🤖 **AI Transcription** | Powered by [OpenAI Whisper](https://github.com/openai/whisper) — runs entirely on your hardware |
| ⚡ **Async Processing** | Celery + Redis task queue; uploads return immediately while transcription runs in background |
| ✏️ **Interactive Editor** | Click any segment to edit text, jump to that timestamp in the media player |
| 🎬 **Subtitle Embedding** | Burn styled SRT subtitles into video via FFmpeg (font, size, color, outline) |
| 🔐 **Authentication** | Email/password + Google OAuth 2.0 |
| ☁️ **Flexible Storage** | AWS S3 with automatic local-disk fallback |
| 📊 **Service Health Panel** | Live status of Frontend, Backend API, and Celery Worker in the sidebar |
| 🐳 **One-command Deploy** | Full stack via Docker Compose |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│          Flask Frontend  (port 5000)                        │
│   Auth · Workspace · Media Player · Transcript Editor       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP
           ┌───────────▼────────────┐
           │   FastAPI Backend      │  (port 8000)
           │   POST /stt            │
           └───────────┬────────────┘
                       │ enqueue task
           ┌───────────▼────────────┐      ┌──────────────────┐
           │       Redis            │◄─────►  Celery Worker   │
           │  (broker + results)    │      │  OpenAI Whisper  │
           └────────────────────────┘      └────────┬─────────┘
                                                    │ POST /callback
                                          ┌─────────▼─────────┐
                                          │  Flask /callback   │
                                          │  Save segments     │
                                          └───────────────────┘
```

**Services:**

| Service | Tech | Port | Role |
|---------|------|------|------|
| `frontend` | Flask + Gunicorn | `5000` | Web UI, auth, file management |
| `backend` | FastAPI + Uvicorn | `8000` | STT API, task scheduling |
| `celery` | Celery Worker | — | Runs Whisper transcription |
| `redis` | Redis Alpine | `6379` | Message broker + task results |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) v2+
- Git

### 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SpeechCraft.git
cd SpeechCraft
```

### 2 — Configure environment

Copy and edit the environment file:

```bash
cp .env.example .env
```

Minimum required variables (edit `.env`):

```env
# Flask session secret — change this to a random string
SESSION_SECRET=your-secret-key-here

# Optional: Google OAuth (leave blank to disable Google login)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

# Optional: AWS S3 (leave blank to use local disk storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=

# Optional: PostgreSQL (leave blank to use SQLite)
DATABASE_URL=
```

### 3 — Build and run

```bash
docker compose up --build
```

> First run downloads the Whisper model (~140 MB for `base`). Subsequent starts are fast.

### 4 — Open in your browser

| URL | Description |
|-----|-------------|
| http://localhost:5000 | Web application |
| http://localhost:5000/workspace | Transcription workspace |
| http://localhost:8000/docs | FastAPI interactive API docs |

### 5 — Create an account

Navigate to `http://localhost:5000`, click **Sign Up**, and register with your email.

---

## 🗂️ Project Structure

```
SpeechCraft/
├── backend/                    # FastAPI microservice
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/stt/         # POST /stt endpoint
│   │   │   ├── tasks.py        # Celery STT task
│   │   │   └── worker.py       # Celery configuration
│   │   ├── src/
│   │   │   └── stt_main/
│   │   │       ├── base.py     # Abstract STT interface
│   │   │       ├── factory.py  # STT provider factory
│   │   │       └── whisperSTT/ # OpenAI Whisper implementation
│   │   └── utils/
│   │       └── callbackhandler.py
│   ├── main.py                 # FastAPI app + health endpoints
│   └── Dockerfile
│
├── frontend/                   # Flask web UI
│   ├── app/
│   │   ├── auth/               # Email + Google OAuth blueprints
│   │   ├── main/               # Routes, FFmpeg subtitle utils
│   │   ├── static/
│   │   │   ├── css/style.css
│   │   │   └── js/
│   │   │       ├── app.js              # Global utilities
│   │   │       ├── media-player.js     # In-browser media player
│   │   │       ├── media-processor.js  # Client-side audio extraction
│   │   │       ├── transcript-editor.js
│   │   │       ├── recorder.js         # Live audio recorder (AudioRecorder class)
│   │   │       └── waveform-visualizer.js  # Canvas frequency visualizer
│   │   ├── templates/          # Jinja2 HTML templates
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── storage.py          # S3 / local storage manager
│   │   └── utils.py            # File processing, FFmpeg, API calls
│   ├── main.py
│   └── Dockerfile
│
├── docker-compose.yaml         # Full-stack orchestration
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables

#### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_SECRET` | `change-me-in-production` | Flask session signing key |
| `FLASK_CONFIG` | `development` | `development` / `production` / `testing` |
| `DATABASE_URL` | SQLite | PostgreSQL connection string for production |
| `BACKEND_URL` | `http://localhost:8000` | Internal URL of the FastAPI backend |
| `CALLBACK_URL` | `http://frontend:5000` | URL Celery posts results back to |
| `GOOGLE_OAUTH_CLIENT_ID` | — | Google OAuth app client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | — | Google OAuth app secret |
| `AWS_ACCESS_KEY_ID` | — | S3 credentials |
| `AWS_SECRET_ACCESS_KEY` | — | S3 credentials |
| `AWS_REGION` | `us-east-1` | S3 bucket region |
| `S3_BUCKET_NAME` | — | S3 bucket name |

#### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Redis result backend |

### Whisper Model Size

Edit `backend/app/src/stt_main/whisperSTT/whisperstt.py` to change the model:

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | ~1 GB | ⚡⚡⚡⚡ | ★★☆☆ |
| `base` | ~1 GB | ⚡⚡⚡ | ★★★☆ *(default)* |
| `small` | ~2 GB | ⚡⚡ | ★★★★ |
| `medium` | ~5 GB | ⚡ | ★★★★ |
| `large` | ~10 GB | 🐢 | ★★★★★ |

> CPU is supported. GPU (CUDA) is used automatically when available.

---

## 🔄 Workflow

```
1. Sign up / log in
2. Upload a media file  ──or──  Record audio live in browser
3. SpeechCraft extracts audio (FFmpeg) and sends to backend
4. Celery worker transcribes via Whisper (async)
5. Results are saved as timestamped segments
6. Edit any segment in the interactive timeline editor
7. Export transcript  ──or──  Embed styled subtitles into video
```

---

## 🛠️ Development Setup

Running services individually without Docker:

```bash
# 1. Start Redis
docker run -d -p 6379:6379 redis:alpine

# 2. Backend
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000

# 3. Celery worker (separate terminal)
cd backend
uv run celery -A app.api.worker.celery worker --loglevel=info

# 4. Frontend
cd frontend
uv sync
uv run python main.py
```

### Running Tests

```bash
cd frontend
FLASK_CONFIG=testing uv run pytest
```

---

## 🗺️ Roadmap

### ✅ Done
- [x] Multi-format audio & video upload
- [x] Async transcription with Celery + Redis
- [x] Interactive transcript editor with timeline
- [x] Subtitle embedding via FFmpeg
- [x] Email + Google OAuth authentication
- [x] AWS S3 + local storage
- [x] Live browser audio recording
- [x] Service health dashboard
- [x] Docker Compose full-stack deployment

### 🔜 Coming Soon

- [ ] **🌍 Real-time Subtitle Translation** — Translate transcribed subtitles into any language using an LLM or translation API (DeepL / Google Translate). Select target language per segment or for the entire transcript, then re-embed translated subtitles into video.
- [ ] **🗣️ Speaker Diarization** — Identify and label multiple speakers in the transcript
- [ ] **📤 Export Formats** — SRT, VTT, TXT, DOCX, JSON export options
- [ ] **🔑 API Keys** — Public REST API with key-based auth for programmatic access
- [ ] **👥 Team Workspaces** — Share projects and collaborate on transcripts
- [ ] **📺 YouTube / URL Import** — Paste a video URL to transcribe directly
- [ ] **🔔 Webhook Notifications** — Get notified on job completion
- [ ] **🌐 Multi-language UI** — Interface localization

---

## 🤝 Contributing

Contributions are what make open source great. All PRs are welcome!

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Commit your changes: `git commit -m "feat: add amazing feature"`
4. Push to the branch: `git push origin feat/amazing-feature`
5. Open a Pull Request

Please open an issue first for large changes so we can discuss the approach.

---

## 🐛 Reporting Issues

Found a bug or have a feature request?
→ [Open an issue](https://github.com/YOUR_USERNAME/SpeechCraft/issues)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
Free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) — the STT engine that powers transcription
- [FastAPI](https://fastapi.tiangolo.com) — modern Python web framework
- [Flask](https://flask.palletsprojects.com) — lightweight WSGI web application framework
- [Celery](https://docs.celeryq.dev) — distributed task queue
- [FFmpeg](https://ffmpeg.org) — audio/video processing

---

<div align="center">

Made with ❤️ · Open Source Forever

⭐ **Star this repo if SpeechCraft is useful to you!** ⭐

</div>
