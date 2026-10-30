#!/usr/bin/env python3
"""
Setup script for the Music Recommender System.
This script installs dependencies and sets up the environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Music Recommender System...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required")
        return False
    
    print(f"✅ Python {sys.version} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("💡 Try: pip install --upgrade pip")
        print("💡 Or create a virtual environment: python -m venv venv && venv\\Scripts\\activate")
        return False
    
    # Set up environment file
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("🔄 Creating .env file...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ .env file created")
    
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. For Docker setup: docker-compose up --build")
    print("2. For manual setup:")
    print("   - Set up PostgreSQL database")
    print("   - Run: python scripts/setup_database.py")
    print("   - Run: python scripts/train_models.py")
    print("   - Start API: uvicorn backend.app.main:app --reload")
    print("   - Start Frontend: streamlit run frontend/app.py")
    print("3. For demo: python demo.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
