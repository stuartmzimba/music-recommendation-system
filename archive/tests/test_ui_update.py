#!/usr/bin/env python3
"""
Test if the UI is getting updated Apriori recommendations from the API.
"""

import sqlite3
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode

def test_api_directly():
    """Test the API directly to see what recommendations are returned."""
    print("🧪 Testing API Recommendations")
    print("=" * 40)
    
    # Test data
    url = "http://localhost:8001/api/v1/recommendations"
    data = {
        "basket": ["Abantwana bakho"],
        "genres": ["Amapiano"],
        "top_k": 5
    }
    
    try:
        # Create request
        req = Request(url)
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
        
        print(f"🔍 Testing song: {data['basket'][0]}")
        print(f"🎭 Genre: {data['genres'][0]}")
        
        # Make request
        with urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ API Response received")
            recommendations = result.get('recommendations', [])
            print(f"📈 Number of recommendations: {len(recommendations)}")
            
            if recommendations:
                print(f"\n🎵 API Recommendations:")
                method_counts = {}
                
                for i, rec in enumerate(recommendations, 1):
                    track = rec.get('track_name', 'Unknown')
                    artist = rec.get('artist', 'Unknown')
                    reason = rec.get('reason', 'Unknown')
                    score = rec.get('score', 0)
                    
                    print(f"  {i}. {track} by {artist}")
                    print(f"     Method: {reason} | Score: {score:.3f}")
                    
                    # Count methods
                    method_counts[reason] = method_counts.get(reason, 0) + 1
                
                print(f"\n📊 Methods Used by API:")
                for method, count in method_counts.items():
                    percentage = (count / len(recommendations)) * 100
                    print(f"  {method}: {count} ({percentage:.1f}%)")
                
                # Check for Apriori
                apriori_methods = ['Apriori Association', 'Association Rule', 'apriori']
                has_apriori = any(any(ap.lower() in reason.lower() for ap in apriori_methods) 
                                for reason in method_counts.keys())
                
                if has_apriori:
                    print(f"\n✅ Apriori recommendations found in API!")
                else:
                    print(f"\n⚠️ No Apriori recommendations in API response")
                    print(f"   Available methods: {list(method_counts.keys())}")
                
                return method_counts
            else:
                print(f"❌ No recommendations returned from API")
                return {}
                
    except Exception as e:
        print(f"❌ API Error: {e}")
        return {}

def check_database_rules():
    """Verify the database has the association rules."""
    print(f"\n🔍 Checking Database Association Rules")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Check total rules
    cursor.execute("SELECT COUNT(*) FROM association_rules")
    total_rules = cursor.fetchone()[0]
    print(f"📊 Total association rules: {total_rules:,}")
    
    # Check for Abantwana Bakho specifically
    cursor.execute("""
        SELECT id, track_name, artist 
        FROM songs 
        WHERE track_name LIKE '%Abantwana%'
        LIMIT 1
    """)
    
    song = cursor.fetchone()
    if song:
        song_id, track, artist = song
        print(f"🎵 Found: {track} by {artist}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM association_rules 
            WHERE antecedent_song_id = ?
        """, (song_id,))
        
        rule_count = cursor.fetchone()[0]
        print(f"📈 Rules for this song: {rule_count}")
        
        if rule_count > 0:
            cursor.execute("""
                SELECT s.track_name, s.artist, ar.confidence, ar.lift
                FROM association_rules ar
                JOIN songs s ON ar.consequent_song_id = s.id
                WHERE ar.antecedent_song_id = ?
                ORDER BY ar.confidence DESC
                LIMIT 3
            """, (song_id,))
            
            rules = cursor.fetchall()
            print(f"🎯 Top database rules:")
            for track, artist, conf, lift in rules:
                print(f"  → {track} by {artist} (conf: {conf:.2f}, lift: {lift:.2f})")
        
        conn.close()
        return rule_count > 0
    else:
        print(f"❌ Song not found in database")
        conn.close()
        return False

def check_frontend_code():
    """Check if the frontend is properly handling different recommendation methods."""
    print(f"\n🔍 Checking Frontend Code")
    print("=" * 40)
    
    try:
        with open('frontend/app.py', 'r', encoding='utf-8') as f:
            frontend_code = f.read()
        
        # Check for method handling
        if 'reason' in frontend_code or 'method' in frontend_code:
            print("✅ Frontend appears to handle recommendation methods")
        else:
            print("⚠️ Frontend might not be handling recommendation methods")
        
        # Check for chart/visualization
        if 'chart' in frontend_code.lower() or 'plotly' in frontend_code.lower():
            print("✅ Frontend has chart/visualization code")
        else:
            print("⚠️ Frontend might not have chart visualization")
        
        # Look for specific method handling
        lines = frontend_code.split('\n')
        method_lines = [line.strip() for line in lines if 'reason' in line.lower() or 'method' in line.lower()]
        
        if method_lines:
            print(f"📝 Found method-related code lines:")
            for line in method_lines[:3]:  # Show first 3
                if line and not line.startswith('#'):
                    print(f"  {line}")
        
    except FileNotFoundError:
        print("❌ Frontend file not found")
    except Exception as e:
        print(f"❌ Error reading frontend: {e}")

def main():
    print("🔍 Checking UI Update Status")
    print("=" * 50)
    
    # Test API
    api_methods = test_api_directly()
    
    # Check database
    has_db_rules = check_database_rules()
    
    # Check frontend
    check_frontend_code()
    
    print(f"\n🎉 UI Update Status Summary:")
    print("=" * 35)
    
    if has_db_rules:
        print("✅ Database: Association rules present")
    else:
        print("❌ Database: No association rules")
    
    if api_methods:
        if any('apriori' in method.lower() or 'association' in method.lower() for method in api_methods.keys()):
            print("✅ API: Returning Apriori recommendations")
        else:
            print("⚠️ API: Not returning Apriori recommendations")
            print(f"   Methods returned: {list(api_methods.keys())}")
    else:
        print("❌ API: Not responding or no recommendations")
    
    print(f"\n💡 Next Steps:")
    if has_db_rules and not api_methods:
        print("  • API might need debugging - check backend logs")
    elif has_db_rules and api_methods:
        print("  • Refresh your browser at http://localhost:8503")
        print("  • Try the recommendation again")
    else:
        print("  • Database rules might need regeneration")

if __name__ == "__main__":
    main()
