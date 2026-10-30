# 🚀 How to Run the Music Recommendation System

## 📋 **Current Status (Already Running!)**

✅ **Backend API**: Running on Terminal 39 at `http://localhost:8001`  
✅ **Frontend UI**: Running on Terminal 56 at `http://localhost:8503`  
✅ **Streamlit App**: Running on Terminal 32 at `http://localhost:8502`

## 🔧 **Manual Setup Instructions**

### **Prerequisites:**
- Python 3.8+ installed
- All dependencies installed (see requirements.txt files)
- Database populated with songs and association rules

### **Method 1: Run Both Services Manually**

#### **1. Start the Backend API (FastAPI)**
```bash
# Open Terminal 1
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Backend will be available at:**
- 🌐 **API**: http://localhost:8001
- 📚 **API Docs**: http://localhost:8001/docs
- 🔍 **ReDoc**: http://localhost:8001/redoc

#### **2. Start the Frontend (Streamlit)**
```bash
# Open Terminal 2
python -m streamlit run frontend/app.py --server.port 8503
```

**Frontend will be available at:**
- 🎵 **Web App**: http://localhost:8503

### **Method 2: Quick Start Script**

Double-click `run.bat` or run:

```bash
python run_app.py
```

echo Both services are starting...
echo Backend API: http://localhost:8001
echo Frontend UI: http://localhost:8503
pause
```

## 🌐 **Service URLs**

### **Backend API (FastAPI)**
- **Base URL**: http://localhost:8001
- **Health Check**: http://localhost:8001/health
- **API Documentation**: http://localhost:8001/docs
- **Alternative Docs**: http://localhost:8001/redoc

### **Frontend (Streamlit)**
- **Web Application**: http://localhost:8503
- **Music Recommendations**: Interactive UI for song recommendations
- **Genre Filtering**: Browse by 43 different genres
```markdown
# 🚀 How to Run the Music Recommendation System

Concise, accurate instructions for starting and troubleshooting the project locally.

## Prerequisites
- Python 3.10+ (the project was developed with Python 3.11+)
- Install dependencies: `python -m pip install -r requirements.txt`
- DB: by default the app uses SQLite (`music_recommender.db` in project root). To use Postgres, set `DATABASE_URL` in your environment.

## Start both services (recommended)

Preferred: run the canonical launcher (keeps backend + frontend together and monitors both):

```powershell
python -m bin.run_app_launcher
# or use the backwards-compatible shim
python run_app.py
```

Default ports:
- Backend API: http://localhost:8001
- Frontend: http://localhost:8503

## Start services separately (useful for debugging)

Backend (FastAPI + Uvicorn):

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

Frontend (Streamlit):

```powershell
python -m streamlit run frontend/app.py --server.port 8503
```

## Useful endpoints
- Health: http://localhost:8001/health
- API docs: http://localhost:8001/docs
- Frontend: http://localhost:8503

## Troubleshooting
- If the launcher reports missing packages: install them with `python -m pip install -r requirements.txt`.
- If Streamlit exits immediately, run the Streamlit command in a terminal to capture logs and fix the reported error.
- If the DB is missing, create a SQLite db with `python scripts/setup_database.py --sqlite` or run `bin/setup_database.py`.
- If using Postgres, set `DATABASE_URL` and run migrations/setup for Postgres.

## Quick health check

```powershell
# Health check
curl http://localhost:8001/health

# Run unit/integration tests
python -m pytest -q
```

---

If you'd like, I can add a `start-all.ps1` to automate venv activation + launcher, or add per-service log files under `logs/` for easier debugging. Tell me which and I'll add it.
```
## 📊 **System Status Check**
