"""
Tests for the Music Recommender API.
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "music-recommender-api"


def test_recommend_endpoint():
    """Test the recommendation endpoint."""
    request_data = {
        "basket": ["Master KG", "Amapiano"],
        "genres": ["amapiano"],
        "top_k": 5
    }
    
    response = client.post("/api/v1/recommend", json=request_data)
    
    # The endpoint should return 200 even if no recommendations are found
    assert response.status_code == 200
    
    # Response should be a list
    data = response.json()
    assert isinstance(data, list)


def test_popular_songs_endpoint():
    """Test the popular songs endpoint."""
    response = client.get("/api/v1/popular?limit=10")
    
    assert response.status_code == 200
    
    # Response should be a list
    data = response.json()
    assert isinstance(data, list)


def test_genres_endpoint():
    """Test the genres endpoint."""
    response = client.get("/api/v1/genres")
    
    assert response.status_code == 200
    
    # Response should have genres key
    data = response.json()
    assert "genres" in data
    assert isinstance(data["genres"], list)


def test_artists_endpoint():
    """Test the artists endpoint."""
    response = client.get("/api/v1/artists?limit=20")
    
    assert response.status_code == 200
    
    # Response should have artists key
    data = response.json()
    assert "artists" in data
    assert isinstance(data["artists"], list)


def test_invalid_recommendation_request():
    """Test recommendation endpoint with invalid data."""
    # Empty basket should still work (fallback to popular)
    request_data = {
        "basket": [],
        "top_k": 5
    }
    
    response = client.post("/api/v1/recommend", json=request_data)
    assert response.status_code == 200
    
    # Invalid top_k should return validation error
    request_data = {
        "basket": ["Master KG"],
        "top_k": 0  # Invalid: should be >= 1
    }
    
    response = client.post("/api/v1/recommend", json=request_data)
    assert response.status_code == 422  # Validation error


def test_search_endpoint():
    """Test the song search endpoint."""
    response = client.get("/api/v1/search?query=Jerusalema&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "track_name" in data[0]


def test_stats_endpoint():
    """Test the system stats endpoint."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "songs_count" in data
    assert data["songs_count"] > 0
    assert "rules_count" in data
    assert "genres_count" in data


def test_frontend_web_app():
    """Test that the Apple Music web app is mounted and served at /app/."""
    response = client.get("/app/")
    assert response.status_code == 200
    assert "MusicAI" in response.text or "Music Recommender" in response.text
    assert "Apple Music Clean" in response.text

    # Test static assets are served
    css_res = client.get("/app/style.css")
    assert css_res.status_code == 200
    assert "--apple-red" in css_res.text

    js_res = client.get("/app/app.js")
    assert js_res.status_code == 200
    assert "fetchRecommendations" in js_res.text



if __name__ == "__main__":
    pytest.main([__file__])
