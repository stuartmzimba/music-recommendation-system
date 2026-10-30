#!/usr/bin/env python3
"""
Canonical launcher for the Music Recommender System.
This file is the relocated content from the repository root `run_app.py` to `bin/`.
"""

import argparse
import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MusicRecommenderLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
        # Configuration
        self.backend_host = "0.0.0.0"
        self.backend_port = 8001
        self.frontend_port = 8503
        # Paths
        self.project_root = Path(__file__).parent.parent
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"

        # runtime options
        self.install_missing = False
        # If True, skip interactive prompt when installing missing packages
        self.auto_confirm = False

    def _install_missing_packages(self, packages):
        """Install missing pip packages using the current Python interpreter."""
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + packages
            print(f"🔧 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error installing packages: {e}")
            return False
        
    def check_dependencies(self):
        """Check if required dependencies are available."""
        print("🔍 Checking Dependencies...")
        
        # Check Python packages
        # Map package names (pip) to their import names when they differ
        required_packages = {
            'uvicorn': 'uvicorn',
            'fastapi': 'fastapi',
            'streamlit': 'streamlit',
            'sqlalchemy': 'sqlalchemy',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'scikit-learn': 'sklearn',
        }
        missing_packages = []
        for pkg_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                print(f"  ✅ {pkg_name}")
            except ImportError:
                missing_packages.append(pkg_name)
                print(f"  ❌ {pkg_name} - Missing (import '{import_name}')")
        
        if missing_packages:
            print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            if self.install_missing:
                # Ask for confirmation unless auto_confirm is set
                proceed = self.auto_confirm
                if not proceed:
                    try:
                        resp = input("\nDo you want to install missing packages now? [y/N]: ").strip().lower()
                        proceed = resp in ("y", "yes")
                    except Exception:
                        proceed = False

                if not proceed:
                    print("ℹ️ Installation cancelled by user.")
                    return False

                print("\n🔧 Installing missing packages...")
                installed = self._install_missing_packages(missing_packages)
                if installed:
                    print("✅ Missing packages installed. Re-checking imports...")
                    # re-check imports
                    return self.check_dependencies()
                else:
                    print("❌ Failed to install missing packages automatically")
                    return False
            return False
        
        # Check if database exists
        db_path = self.project_root / "music_recommender.db"
        if not db_path.exists():
            print(f"❌ Database not found: {db_path}")
            print("Please ensure the database file exists.")
            return False
        else:
            print(f"✅ Database found: {db_path}")
        
        # Check if backend and frontend directories exist
        if not self.backend_path.exists():
            print(f"❌ Backend directory not found: {self.backend_path}")
            return False
        else:
            print(f"✅ Backend directory: {self.backend_path}")
            
        if not self.frontend_path.exists():
            print(f"❌ Frontend directory not found: {self.frontend_path}")
            return False
        else:
            print(f"✅ Frontend directory: {self.frontend_path}")
        
        return True
    
    def start_backend(self):
        """Start the FastAPI backend server."""
        print(f"\n🚀 Starting Backend Server...")
        print(f"   Host: {self.backend_host}")
        print(f"   Port: {self.backend_port}")
        print(f"   Path: {self.backend_path}")
        
        try:
            backend_cmd = [
                sys.executable, "-m", "uvicorn", 
                "backend.app.main:app",
                "--host", self.backend_host,
                "--port", str(self.backend_port),
                "--reload"
            ]
            
            self.backend_process = subprocess.Popen(
                backend_cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print(f"✅ Backend started (PID: {self.backend_process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the Streamlit frontend server."""
        print(f"\n🎨 Starting Frontend Server...")
        print(f"   Port: {self.frontend_port}")
        print(f"   Path: {self.frontend_path}")
        
        try:
            frontend_cmd = [
                sys.executable, "-m", "streamlit", "run", 
                "app.py",
                "--server.port", str(self.frontend_port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            self.frontend_process = subprocess.Popen(
                frontend_cmd,
                cwd=self.frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print(f"✅ Frontend started (PID: {self.frontend_process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
    
    def monitor_process(self, process, name):
        """Monitor a process and print its output."""
        try:
            for line in iter(process.stdout.readline, ''):
                if line and self.running:
                    line = line.strip()
                    if any(keyword in line.lower() for keyword in [
                        'error', 'warning', 'started', 'running', 'listening',
                        'uvicorn running', 'streamlit running', 'application startup'
                    ]):
                        print(f"[{name}] {line}")
        except Exception as e:
            if self.running:
                print(f"❌ Error monitoring {name}: {e}")
    
    def wait_for_services(self):
        """Wait for services to start up."""
        print(f"\n⏳ Waiting for services to start...")
        
        import urllib.request
        import json
        
        backend_url = f"http://localhost:{self.backend_port}"
        for i in range(30):
            try:
                with urllib.request.urlopen(f"{backend_url}/", timeout=2) as response:
                    if response.status == 200:
                        print(f"✅ Backend ready at {backend_url}")
                        break
            except:
                time.sleep(1)
        else:
            print(f"⚠️ Backend may not be ready yet")
        
        frontend_url = f"http://localhost:{self.frontend_port}"
        for i in range(30):
            try:
                with urllib.request.urlopen(frontend_url, timeout=2) as response:
                    if response.status == 200:
                        print(f"✅ Frontend ready at {frontend_url}")
                        break
            except:
                time.sleep(1)
        else:
            print(f"⚠️ Frontend may not be ready yet")
    
    def print_status(self):
        """Print the current status and URLs."""
        print(f"\n🎉 Music Recommendation System is Running!")
        print("=" * 50)
        print(f"🍎 Apple Music Web App:     http://localhost:{self.backend_port}/app/")
        print(f"📊 Streamlit Dashboard:    http://localhost:{self.frontend_port}")
        print(f"🔌 Backend (API):          http://localhost:{self.backend_port}")
        print(f"📚 API Documentation:     http://localhost:{self.backend_port}/docs")
        print("=" * 50)
        print(f"💡 Usage:")
        print(f"  1. Open http://localhost:{self.backend_port}/app/ for Apple Music UI")
        print(f"  2. Or open http://localhost:{self.frontend_port} for Streamlit Dashboard")
        print(f"  2. Search for songs or select a genre")
        print(f"  3. Get personalized recommendations!")
        print("=" * 50)
        print(f"⏹️  Press Ctrl+C to stop both services")
    
    def cleanup(self):
        """Clean up processes."""
        print(f"\n🛑 Shutting down services...")
        self.running = False
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print(f"✅ Backend stopped")
            except:
                self.backend_process.kill()
                print(f"🔨 Backend force-killed")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print(f"✅ Frontend stopped")
            except:
                self.frontend_process.kill()
                print(f"🔨 Frontend force-killed")
        
        print(f"👋 Music Recommendation System stopped")
    
    def run(self):
        """Main run method."""
        print("🎵 Music Recommendation System Launcher")
        print("=" * 45)
        
        # Check dependencies
        if not self.check_dependencies():
            print(f"\n❌ Dependency check failed. Please install missing packages.")
            return False
        
        def signal_handler(signum, frame):
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            if not self.start_backend():
                return False
            
            if not self.start_frontend():
                self.cleanup()
                return False
            
            backend_monitor = threading.Thread(
                target=self.monitor_process, 
                args=(self.backend_process, "Backend"),
                daemon=True
            )
            frontend_monitor = threading.Thread(
                target=self.monitor_process, 
                args=(self.frontend_process, "Frontend"),
                daemon=True
            )
            
            backend_monitor.start()
            frontend_monitor.start()
            
            self.wait_for_services()
            self.print_status()
            
            while self.running:
                time.sleep(1)
                if self.backend_process.poll() is not None:
                    print(f"❌ Backend process died")
                    break
                if self.frontend_process.poll() is not None:
                    print(f"❌ Frontend process died")
                    break
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            self.cleanup()
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Run the Music Recommender System (backend + frontend)")
    parser.add_argument('--install-missing', action='store_true', help='Attempt to install missing pip packages automatically')
    parser.add_argument('--yes', '-y', action='store_true', help='Automatically answer yes to prompts (use with --install-missing)')
    args = parser.parse_args()

    launcher = MusicRecommenderLauncher()
    launcher.install_missing = bool(args.install_missing)
    launcher.auto_confirm = bool(args.yes)

    success = launcher.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
