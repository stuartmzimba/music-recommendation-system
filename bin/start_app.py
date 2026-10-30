#!/usr/bin/env python3
"""
Simple startup script for the Music Recommender System
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import streamlit
        import pandas
        import sqlalchemy
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_database():
    """Set up database if it doesn't exist"""
    db_file = Path("music_recommender.db")
    if not db_file.exists():
        print("🔧 Setting up database...")
        result = subprocess.run([sys.executable, "setup_database.py"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Database setup failed")
            print(result.stderr)
            return False
        print("✅ Database setup completed")
    else:
        print("✅ Database already exists")
    return True

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting backend API...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "backend.app.main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", "8001"
    ])
    return backend_process

def start_frontend():
    """Start the Streamlit frontend"""
    print("🎨 Starting frontend...")
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/app.py", 
        "--server.port", "8503",
        "--server.address", "0.0.0.0"
    ])
    return frontend_process

def main():
    """Main startup function"""
    print("🎵 MUSIC RECOMMENDER SYSTEM STARTUP")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Setup database
    if not setup_database():
        return False
    
    print("\nChoose startup option:")
    print("1. Full stack (API + Frontend)")
    print("2. API only")
    print("3. Frontend only")
    print("4. Demo only")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    processes = []
    
    try:
        if choice == "1":
            # Start both backend and frontend
            backend_proc = start_backend()
            processes.append(backend_proc)
            
            # Wait a bit for backend to start
            time.sleep(3)
            
            frontend_proc = start_frontend()
            processes.append(frontend_proc)
            
            # Wait a bit more for frontend to start
            time.sleep(3)
            
            print("\n✅ Both services started!")
            print("📱 Frontend: http://localhost:8501")
            print("🔧 API: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
            
            # Open browser
            try:
                webbrowser.open("http://localhost:8501")
            except:
                pass
            
            print("\nPress Ctrl+C to stop all services")
            
            # Wait for processes
            for proc in processes:
                proc.wait()
                
        elif choice == "2":
            # API only
            backend_proc = start_backend()
            processes.append(backend_proc)
            
            time.sleep(3)
            print("\n✅ API started!")
            print("🔧 API: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
            
            backend_proc.wait()
            
        elif choice == "3":
            # Frontend only
            frontend_proc = start_frontend()
            processes.append(frontend_proc)
            
            time.sleep(3)
            print("\n✅ Frontend started!")
            print("📱 Frontend: http://localhost:8501")
            
            frontend_proc.wait()
            
        elif choice == "4":
            # Demo only
            print("🎬 Running demo...")
            result = subprocess.run([sys.executable, "demo.py"])
            return result.returncode == 0
            
        else:
            print("❌ Invalid choice")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for proc in processes:
            proc.terminate()
        print("✅ All services stopped")
        return True
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
