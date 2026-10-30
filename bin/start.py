#!/usr/bin/env python3
"""
Startup script for the Music Recommender System.
This script sets up the database, loads data, trains models, and starts the services.
"""

import subprocess
import sys
import os
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command, description, cwd=None):
    """Run a command and return success status."""
    logger.info(f"🔄 {description}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully")
            if result.stdout.strip():
                logger.info(f"Output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ {description} failed")
            if result.stderr.strip():
                logger.error(f"Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        logger.error(f"❌ {description} failed with exception: {e}")
        return False


def check_docker():
    """Check if Docker is available."""
    return run_command("docker --version", "Checking Docker availability")


def check_python_dependencies():
    """Check if Python dependencies are installed."""
    logger.info("🔄 Checking Python dependencies...")
    
    try:
        import fastapi
        import streamlit
        import pandas
        import sqlalchemy
        import mlxtend
        logger.info("✅ Python dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing Python dependency: {e}")
        logger.info("💡 Install dependencies with: pip install -r backend/requirements.txt")
        return False


def setup_environment():
    """Set up environment variables."""
    logger.info("🔄 Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        logger.info("Creating .env file from .env.example...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        logger.info("✅ .env file created")
    
    return True


def main():
    """Main startup function."""
    logger.info("🚀 Starting Music Recommender System setup...")
    
    # Check prerequisites
    if not check_python_dependencies():
        logger.error("❌ Setup failed: Missing dependencies")
        return False
    
    # Setup environment
    if not setup_environment():
        logger.error("❌ Setup failed: Environment setup failed")
        return False
    
    # Check if Docker is available for full setup
    docker_available = check_docker()
    
    if docker_available:
        logger.info("🐳 Docker detected. You can use Docker Compose for full setup:")
        logger.info("   docker-compose up --build")
        logger.info("")
        logger.info("🔧 Or continue with manual setup...")
    
    # Manual setup option
    logger.info("📋 Manual Setup Steps:")
    logger.info("1. Set up database (PostgreSQL required)")
    logger.info("2. Run: python scripts/setup_database.py")
    logger.info("3. Run: python scripts/train_models.py")
    logger.info("4. Start API: uvicorn backend.app.main:app --reload")
    logger.info("5. Start Frontend: streamlit run frontend/app.py")
    
    # Offer to run tests
    logger.info("")
    logger.info("🧪 To run tests: python -m pytest tests/")
    
    logger.info("🎉 Setup information provided!")
    logger.info("📖 See README.md for detailed instructions")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
