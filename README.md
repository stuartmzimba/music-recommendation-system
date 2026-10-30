# 🎵 MusicAI Pro — Hybrid Music Recommendation System

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-38B2AC?logo=tailwindcss)](https://tailwindcss.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.0-FF6384?logo=chartdotjs)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passing-brightgreen?logo=pytest)](https://pytest.org/)
[![Latency](https://img.shields.io/badge/Inference%20Latency-%3C15ms-success)](https://fastapi.tiangolo.com/)

A production-grade, full-stack hybrid music recommendation platform tailored for South African streaming trends (Amapiano, Afrobeats, House, Hip-Hop, Pop) and global catalog discovery.

Features an **Apple Music Clean** desktop web application, **Native HTML5 30-Second AAC Audio Streaming**, and a **Multi-Armed Hybrid Recommendation Backend** mining 1.2M+ user listening interactions.

---

## 🌟 Key Highlights

- **Hybrid Recommendation Pipeline**:
  - **Arm 1 (Co-Listening Association)**: FP-Growth association rules mined across 1.2M user streaming transactions, scored by Support, Confidence, and Lift.
  - **Arm 2 (Acoustic Feature Vectors)**: TF-IDF metadata tokens combined with normalized acoustic vectors (Danceability, Energy, Valence, Tempo, Popularity) computed via Cosine Similarity.
  - **Arm 3 (Regional Trending Fallback)**: Streaming hit index guarantees zero cold-start failures or blank recommendation states.
- **Sub-15ms Inference**: Pre-computed vectorized feature matrices and singleton caching slash inference latency from ~4,000ms to `<15ms`.
- **Apple Music Clean UI**:
  - Translucent frosted glass layout (`backdrop-filter: blur(24px)`) matching macOS / iOS standards.
  - Authentic high-resolution `600x600` album cover art resolution.
  - Dual view modes: **Editorial Card Grid** & **Tracklist Table View**.
- **Real Audio Streaming Engine**:
  - Streams 30-second master recording AAC `.m4a` preview audio via standard HTML5 `<audio>` tag.
  - Clickable audio scrubber, volume slider, mute toggle, and real-time animated equalizer waves.
  - Web Audio API synthesizer fallback for guaranteed sound on all catalog items.
- **Dual-Track Acoustic Radar Visualizer**: 5-axis dimensional fingerprinting with side-by-side song comparisons.
- **Export & Share Mix**: Instant export to `.M3U` playlist files (compatible with Apple Music, VLC, iTunes) and clipboard tracklist formatting.
- **Comprehensive Test Suite**: 18 automated unit and end-to-end tests covering data pipelines, ML models, and API endpoints.

---

## 🏗️ System Architecture

```
User Basket Seeds & Genre Preferences
                  │
                  ▼
   ┌──────────────────────────────┐
   │ RecommendationService Router │
   └──────────────┬───────────────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
┌─────────────┐ ┌──────────┐ ┌────────────┐
│  FP-Growth  │ │ Content  │ │ Regional   │
│ Association │ │ Vectors  │ │ Popularity │
│ Rules (1.2M)│ │ (TF-IDF) │ │ Trending   │
└──────┬──────┘ └────┬─────┘ └─────┬──────┘
       │             │             │
       └──────────┬──┴─────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ Rank Blending & De-duplication│
   └──────────────┬───────────────┘
                  │
                  ▼
       Top-K Recommendation List (<15ms)
                  │
                  ▼
       Apple Music Clean Web App
```

---

## 📁 Project Structure

```
├── backend/                   # FastAPI Backend
│   └── app/
│       ├── api/              # API endpoints (/recommend, /popular, /search, /stats)
│       ├── core/             # Configuration & database session management
│       ├── models/           # SQLAlchemy ORM & Pydantic validation schemas
│       ├── services/         # Hybrid recommendation business logic
│       └── main.py           # FastAPI entry point & static app mount
├── frontend_web/              # Apple Music Clean Web Application
│   ├── index.html            # Studio desktop layout, sidebar, player & radar
│   ├── style.css             # Apple Music frosted glass & animated equalizer
│   └── app.js                # State management, audio engine & Chart.js bindings
├── frontend/                  # Legacy Streamlit interface (optional)
│   └── app.py
├── ml/                        # Machine Learning Pipeline
│   ├── apriori/              # FP-Growth / Apriori association rule trainer
│   ├── content_based/        # TF-IDF & acoustic cosine similarity recommender
│   └── data_pipeline/        # ETL & data loading routines
├── models/                    # Pre-computed model serialization artifacts
│   └── content_based_model.joblib
├── tests/                     # Automated Pytest suite
│   ├── test_api.py           # API routes & static mount tests
│   ├── test_integration.py   # Full pipeline end-to-end tests
│   └── test_apriori_rules.py # Association rule mining verification
├── run.bat                    # 1-click Windows launcher
├── run_app.py                 # Canonical python launcher shim
├── requirements.txt           # Python package dependencies
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/music-recommendation-system.git
cd music-recommendation-system

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.venv\Scripts\activate          # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database (Optional if seed DB is present)

```bash
python setup_database.py
```

### 4. Run the Application

```bash
# 1-Click Launch (Windows):
run.bat

# Or run via Python:
python run_app.py

# Or run FastAPI directly:
uvicorn backend.app.main:app --port 8000 --reload
```

Open your browser at:
👉 **[http://localhost:8000/app/](http://localhost:8000/app/)**

---

## 🔌 API Endpoints Reference

The FastAPI backend exposes an interactive OpenAPI documentation at `http://localhost:8000/docs`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/recommend` | Generate hybrid recommendations based on basket seeds & genres |
| `GET` | `/api/v1/popular` | Retrieve top-streamed songs by genre or regional rank |
| `GET` | `/api/v1/search` | Live catalog search across 8,681+ tracks with acoustic vectors |
| `GET` | `/api/v1/genres` | List all 43 catalog music genres |
| `GET` | `/api/v1/stats` | Database telemetry (song count, rules, interaction logs) |
| `GET` | `/health` | Health check probe |

---

## 🧪 Testing

Run the automated test suite with `pytest`:

```bash
pytest -v
```

All 18 unit, integration, and API tests should pass cleanly in `<8s`.

---

## 📄 License

MIT License. Feel free to use and adapt this project for portfolio, educational, or commercial purposes.
