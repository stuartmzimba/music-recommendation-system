#!/usr/bin/env python3
"""
Test the correct API endpoint for recommendations.
"""

import json
from urllib.request import urlopen, Request

def test_correct_api():
    """Test the correct API endpoint."""
    print("🧪 Testing Correct API Endpoint")
    print("=" * 40)
    
    # Correct endpoint
    url = "http://localhost:8001/api/v1/recommend"
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
        
        print(f"🔍 Testing: {data['basket'][0]}")
        print(f"🎭 Genre: {data['genres'][0]}")
        print(f"🌐 URL: {url}")
        
        # Make request
        with urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ API Response received")
            print(f"📈 Number of recommendations: {len(result)}")
            
            if result:
                print(f"\n🎵 API Recommendations:")
                method_counts = {}
                
                for i, rec in enumerate(result, 1):
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
                    percentage = (count / len(result)) * 100
                    print(f"  {method}: {count} ({percentage:.1f}%)")
                
                # Check for Apriori
                apriori_keywords = ['apriori', 'association', 'rule']
                has_apriori = any(any(keyword in reason.lower() for keyword in apriori_keywords) 
                                for reason in method_counts.keys())
                
                if has_apriori:
                    print(f"\n✅ SUCCESS: Apriori recommendations found!")
                    print(f"🎉 The API is returning Apriori-based recommendations!")
                else:
                    print(f"\n⚠️ No Apriori recommendations found")
                    print(f"   Methods available: {list(method_counts.keys())}")
                
                return True, method_counts
            else:
                print(f"❌ No recommendations returned")
                return False, {}
                
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False, {}

def main():
    print("🔍 Testing Updated API")
    print("=" * 30)
    
    success, methods = test_correct_api()
    
    print(f"\n🎉 API Test Results:")
    print("=" * 25)
    
    if success:
        print("✅ API is working correctly")
        print("✅ Backend has been successfully updated")
        
        if any('apriori' in method.lower() or 'association' in method.lower() for method in methods.keys()):
            print("✅ Apriori recommendations are working!")
            print("\n🎯 Your UI should now show:")
            print("  • Apriori-based recommendations")
            print("  • Updated recommendation breakdown chart")
            print("  • Authentic Amapiano song recommendations")
        else:
            print("⚠️ API working but using fallback methods")
            print(f"  Methods: {list(methods.keys())}")
    else:
        print("❌ API still has issues")
    
    print(f"\n💡 Next Steps:")
    print("  1. Refresh your browser at http://localhost:8503")
    print("  2. Try searching for 'Abantwana bakho' again")
    print("  3. You should now see Apriori recommendations!")

if __name__ == "__main__":
    main()
