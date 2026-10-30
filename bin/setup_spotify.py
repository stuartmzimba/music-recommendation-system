#!/usr/bin/env python3
"""
Setup script for Spotify integration
"""

import os
import sys
from pathlib import Path

def setup_spotify_credentials():
    """Setup Spotify API credentials."""
    print("🎵 SPOTIFY SETUP")
    print("=" * 50)

    print("To get Spotify data, you need API credentials:")
    print("1. Go to https://developer.spotify.com/dashboard")
    print("2. Log in with your Spotify account")
    print("3. Click 'Create App'")
    print("4. Fill in app details:")
    print("   - App Name: Music Recommender System")
    print("   - App Description: Hybrid music recommendation system")
    print("   - Redirect URI: http://127.0.0.1:8080/callback")
    print("   - Check 'Web API'")
    print("5. Copy your Client ID and Client Secret")
    print()
    print("⚠️  IMPORTANT: Use http://127.0.0.1:8080/callback as redirect URI")
    print("   (NOT localhost - Spotify requires explicit IP for loopback)")
    print()
    
    # Check if credentials already exist
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "SPOTIFY_CLIENT_ID" in content:
                print("✅ Spotify credentials already configured in .env file")
                return True
    
    # Get credentials from user
    client_id = input("Enter your Spotify Client ID: ").strip()
    client_secret = input("Enter your Spotify Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both Client ID and Client Secret are required!")
        return False
    
    # Save to .env file
    env_content = f"""
# Spotify API Credentials
SPOTIFY_CLIENT_ID={client_id}
SPOTIFY_CLIENT_SECRET={client_secret}
"""
    
    with open(env_file, 'a') as f:
        f.write(env_content)
    
    print(f"✅ Credentials saved to {env_file}")
    return True

def install_spotify_dependencies():
    """Install required packages for Spotify integration."""
    print("\n📦 Installing Spotify dependencies...")
    
    try:
        import subprocess
        
        # Install spotipy
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spotipy", "requests"])
        print("✅ Spotify dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def main():
    """Main setup function."""
    print("Setting up Spotify integration for your music recommender...")
    
    # Install dependencies
    if not install_spotify_dependencies():
        return 1
    
    # Setup credentials
    if not setup_spotify_credentials():
        return 1
    
    print("\n🎉 Spotify setup complete!")
    print("\n📝 Next steps:")
    print("1. Run: python spotify_easy_fetcher.py")
    print("2. Or run: python spotify_data_fetcher.py")
    print("3. Then run: python reload_data.py")
    print("4. Restart your app to see new music!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
