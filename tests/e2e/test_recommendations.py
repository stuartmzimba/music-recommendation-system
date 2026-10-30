#!/usr/bin/env python3
"""Test the recommendation system to ensure genres and popularity are working correctly."""

import requests
import json

def test_api_endpoint(endpoint, data=None):
    """Test an API endpoint."""
    base_url = "http://localhost:8001"
    url = f"{base_url}{endpoint}"
    
    try:
        if data:
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def main():
    """Test the recommendation system."""
    print("🧪 Testing Music Recommendation System...")
    
    # Test 1: Get available genres
    print("\n1. Testing available genres...")
    genres = test_api_endpoint("/api/v1/genres")
    if genres:
        print(f"✅ Found {len(genres.get('genres', []))} genres")
        print(f"   Sample genres: {genres.get('genres', [])[:5]}")

    # Test 2: Get popular songs
    print("\n2. Testing popular songs...")
    popular = test_api_endpoint("/api/v1/popular?limit=5")
    if popular:
        print(f"✅ Found {len(popular)} popular songs")
        for i, song in enumerate(popular[:3], 1):
            print(f"   {i}. {song['track_name']} by {song['artist']} ({song['genre']}) - Score: {song['popularity_score']}")

    # Test 3: Get popular songs by genre
    print("\n3. Testing popular songs by genre (Amapiano)...")
    amapiano_popular = test_api_endpoint("/api/v1/popular?limit=5&genre=Amapiano")
    if amapiano_popular:
        print(f"✅ Found {len(amapiano_popular)} Amapiano songs")
        for i, song in enumerate(amapiano_popular[:3], 1):
            print(f"   {i}. {song['track_name']} by {song['artist']} - Score: {song['popularity_score']}")

    # Test 4: Get recommendations with genre filter
    print("\n4. Testing recommendations with genre filter...")
    rec_data = {
        "basket": ["Jerusalema", "Water"],
        "genres": ["Amapiano", "Afrobeats"],
        "top_k": 5
    }
    recommendations = test_api_endpoint("/api/v1/recommend", rec_data)
    if recommendations:
        print(f"✅ Found {len(recommendations)} recommendations")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec['track_name']} by {rec['artist']} ({rec['genre']}) - Score: {rec['score']:.2f} [{rec['reason']}]")

    # Test 5: Get recommendations without genre filter
    print("\n5. Testing recommendations without genre filter...")
    rec_data_no_genre = {
        "basket": ["Jerusalema"],
        "top_k": 5
    }
    recommendations_no_genre = test_api_endpoint("/api/v1/recommend", rec_data_no_genre)
    if recommendations_no_genre:
        print(f"✅ Found {len(recommendations_no_genre)} recommendations")
        for i, rec in enumerate(recommendations_no_genre[:3], 1):
            print(f"   {i}. {rec['track_name']} by {rec['artist']} ({rec['genre']}) - Score: {rec['score']:.2f} [{rec['reason']}]")
    
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    main()
