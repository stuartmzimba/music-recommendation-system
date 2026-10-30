#!/usr/bin/env python3
"""
Test the API recommendations to see if Apriori is working through the API.
"""

import requests
import json

def test_api_recommendations():
    """Test the recommendation API."""
    print("🧪 Testing API Recommendations")
    print("=" * 40)
    
    # Test the same song from the UI
    url = "http://localhost:8001/api/v1/recommendations"
    
    payload = {
        "basket": ["Abantwana bakho"],
        "genres": ["Amapiano"],
        "top_k": 5
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🔍 Testing: {payload['basket'][0]}")
        print(f"🎭 Genre: {payload['genres'][0]}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API Response received")
            print(f"📈 Number of recommendations: {len(data.get('recommendations', []))}")
            
            recommendations = data.get('recommendations', [])
            
            if recommendations:
                print(f"\n🎵 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    track = rec.get('track_name', 'Unknown')
                    artist = rec.get('artist', 'Unknown')
                    method = rec.get('reason', 'Unknown method')
                    score = rec.get('score', 0)
                    
                    print(f"  {i}. {track} by {artist}")
                    print(f"     Method: {method} | Score: {score:.3f}")
                
                # Check what methods were used
                methods = [rec.get('reason', 'Unknown') for rec in recommendations]
                method_counts = {}
                for method in methods:
                    method_counts[method] = method_counts.get(method, 0) + 1
                
                print(f"\n📊 Methods Used:")
                for method, count in method_counts.items():
                    percentage = (count / len(recommendations)) * 100
                    print(f"  {method}: {count} recommendations ({percentage:.1f}%)")
                    
                # Check if Apriori is working
                apriori_recs = [rec for rec in recommendations if 'apriori' in rec.get('reason', '').lower() or 'association' in rec.get('reason', '').lower()]
                
                if apriori_recs:
                    print(f"\n✅ Apriori recommendations found: {len(apriori_recs)}")
                else:
                    print(f"\n⚠️ No Apriori recommendations found")
                    print(f"   This might be expected if the frontend is using content-based as fallback")
            else:
                print(f"❌ No recommendations returned")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {url}")
        print(f"   Make sure the backend is running on port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_direct_database():
    """Test direct database access to verify Apriori rules."""
    import sqlite3
    
    print(f"\n🔍 Testing Direct Database Access")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Find the song
    cursor.execute("""
        SELECT id, track_name, artist 
        FROM songs 
        WHERE track_name LIKE '%Abantwana%'
        LIMIT 1
    """)
    
    song = cursor.fetchone()
    if song:
        song_id, track, artist = song
        print(f"🎵 Found: {track} by {artist} (ID: {song_id})")
        
        # Check association rules
        cursor.execute("""
            SELECT COUNT(*) FROM association_rules 
            WHERE antecedent_song_id = ?
        """, (song_id,))
        
        rule_count = cursor.fetchone()[0]
        print(f"📊 Association rules: {rule_count}")
        
        if rule_count > 0:
            cursor.execute("""
                SELECT s.track_name, s.artist, ar.confidence
                FROM association_rules ar
                JOIN songs s ON ar.consequent_song_id = s.id
                WHERE ar.antecedent_song_id = ?
                ORDER BY ar.confidence DESC
                LIMIT 3
            """, (song_id,))
            
            rules = cursor.fetchall()
            print(f"🎯 Top database recommendations:")
            for track, artist, conf in rules:
                print(f"  → {track} by {artist} (conf: {conf:.2f})")
        else:
            print(f"⚠️ No association rules in database")
    else:
        print(f"❌ Song not found in database")
    
    conn.close()

def main():
    print("🧪 Testing Recommendation System")
    print("=" * 50)
    
    # Test API
    test_api_recommendations()
    
    # Test database directly
    test_direct_database()
    
    print(f"\n🎉 Testing Complete!")
    print(f"\n💡 If API shows content-based but database has Apriori rules:")
    print(f"   The recommendation service might need to be restarted to pick up new rules")

if __name__ == "__main__":
    main()
