#!/usr/bin/env python3
"""
Simple launcher for Music Recommendation System
Runs both frontend and backend with minimal setup.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_database():
    """Check if database exists."""
    db_path = Path("music_recommender.db")
    if db_path.exists():
        print(f"✅ Database found")
        return True
    else:
        print(f"❌ Database not found: {db_path}")
        print("   Please ensure music_recommender.db is in the current directory")
        return False

def start_backend():
    """Start the backend server."""
    print("\n🚀 Starting Backend Server...")
    
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "backend.app.main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        print(f"✅ Backend starting... (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the frontend server."""
    print("\n🎨 Starting Frontend Server...")
    
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "frontend/app.py",
            "--server.port", "8503",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        print(f"✅ Frontend starting... (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def wait_and_open_browser():
    """Wait for services and open browser."""
    print("\n⏳ Waiting for services to start...")
    
    # Wait a bit for services to start
    time.sleep(5)
    
    # Try to open browser
    try:
        frontend_url = "http://localhost:8503"
        print(f"🌐 Opening browser: {frontend_url}")
        webbrowser.open(frontend_url)
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")

def print_info():
    """Print application information."""
    print("\n🎉 Music Recommendation System")
    print("=" * 40)
    print("🌐 Frontend:  http://localhost:8503")
    print("🔌 Backend:   http://localhost:8001")
    print("📚 API Docs:  http://localhost:8001/docs")
    print("=" * 40)
    print("🎵 Features:")
    print("  • AI-powered music recommendations")
    print("  • 8,681 songs across 43 genres")
    print("  • 294 authentic Amapiano tracks")
    print("  • Apriori + Content-based filtering")
    print("=" * 40)
    print("⏹️  Press Ctrl+C to stop")

def main():
    """Main function."""
    print("🎵 Music Recommendation System Launcher")
    print("=" * 45)
    
    # Check requirements
    if not check_python_version():
        return False
    
    if not check_database():
        return False
    
    # Start services
    backend = start_backend()
    if not backend:
        return False
    
    frontend = start_frontend()
    if not frontend:
        backend.terminate()
        return False
    
    # Wait and open browser
    wait_and_open_browser()
    
    # Print info
    print_info()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
            
            # Check if processes are still alive
            if backend.poll() is not None:
                print("\n❌ Backend stopped")
                break
            if frontend.poll() is not None:
                print("\n❌ Frontend stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        
    finally:
        # Cleanup
        try:
            backend.terminate()
            frontend.terminate()
            print("✅ Services stopped")
        except:
            pass
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
