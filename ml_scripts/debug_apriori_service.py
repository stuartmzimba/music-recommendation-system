#!/usr/bin/env python3
"""
Debug the Apriori recommendation service to see why it's not working.
"""

import sqlite3
from sqlalchemy import create_engine, or_, desc
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add the backend path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend.app.core.config import settings

def debug_apriori_logic():
    """Debug the Apriori recommendation logic step by step."""
    print("🔍 Debugging Apriori Recommendation Logic")
    print("=" * 50)
    
    # Test the same logic as the service
    basket = ["Abantwana bakho"]
    top_k = 5
    
    print(f"🎵 Testing basket: {basket}")
    print(f"📊 Requesting top_k: {top_k}")
    
    # Connect to database using SQLAlchemy (same as service)
    # Use configured DATABASE_URL so this script follows environment settings
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Import models
        from backend.app.models.database import Song, AssociationRule
        
        print(f"\n1️⃣ Finding songs matching basket items...")
        
        # Find songs matching basket items (same logic as service)
        basket_songs = db.query(Song).filter(
            or_(
                Song.track_name.ilike(f"%{item}%"),
                Song.artist.ilike(f"%{item}%")
            ) for item in basket
        ).all()
        
        print(f"   Found {len(basket_songs)} matching songs:")
        for song in basket_songs:
            print(f"   - {song.track_name} by {song.artist} (ID: {song.id})")
        
        if not basket_songs:
            print("❌ No matching songs found - this is the problem!")
            return
        
        basket_song_ids = [song.id for song in basket_songs]
        print(f"   Basket song IDs: {basket_song_ids}")
        
        print(f"\n2️⃣ Finding association rules...")
        
        # Find association rules (same logic as service)
        rules = db.query(AssociationRule).filter(
            AssociationRule.antecedent_song_id.in_(basket_song_ids)
        ).order_by(desc(AssociationRule.confidence)).limit(top_k * 2).all()
        
        print(f"   Found {len(rules)} association rules")
        
        if not rules:
            print("❌ No association rules found!")
            
            # Check if rules exist for these song IDs
            for song_id in basket_song_ids:
                rule_count = db.query(AssociationRule).filter(
                    AssociationRule.antecedent_song_id == song_id
                ).count()
                print(f"   Song ID {song_id} has {rule_count} rules")
        else:
            print(f"✅ Found association rules:")
            for i, rule in enumerate(rules[:5], 1):
                consequent_song = rule.consequent_song
                print(f"   {i}. {consequent_song.track_name} by {consequent_song.artist}")
                print(f"      Confidence: {rule.confidence:.3f}, Support: {rule.support:.3f}")
        
        print(f"\n3️⃣ Converting to recommendations...")
        
        recommendations = []
        seen_songs = set()
        
        for rule in rules:
            if len(recommendations) >= top_k:
                break
            
            consequent_song = rule.consequent_song
            if consequent_song.id not in seen_songs and consequent_song.id not in basket_song_ids:
                recommendations.append({
                    'track_name': consequent_song.track_name,
                    'artist': consequent_song.artist,
                    'score': rule.confidence,
                    'reason': 'Apriori Association',
                    'genre': consequent_song.genre
                })
                seen_songs.add(consequent_song.id)
        
        print(f"   Generated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['track_name']} by {rec['artist']}")
            print(f"      Score: {rec['score']:.3f}, Method: {rec['reason']}")
        
        if len(recommendations) > 0:
            print(f"\n✅ SUCCESS: Apriori logic is working!")
            print(f"🎉 The service should return {len(recommendations)} Apriori recommendations")
        else:
            print(f"\n❌ PROBLEM: No recommendations generated")
            print(f"   This explains why the API falls back to content-based")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Cannot import backend models - using direct SQL instead")
        
        # Fallback to direct SQL
        debug_with_sql(basket)
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        db.close()

def debug_with_sql(basket):
    """Debug using direct SQL queries."""
    print(f"\n🔍 Debugging with Direct SQL")
    print("=" * 35)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Find matching songs
    item = basket[0]
    cursor.execute("""
        SELECT id, track_name, artist 
        FROM songs 
        WHERE track_name LIKE ? OR artist LIKE ?
    """, (f"%{item}%", f"%{item}%"))
    
    songs = cursor.fetchall()
    print(f"SQL found {len(songs)} matching songs:")
    for song_id, track, artist in songs:
        print(f"  - {track} by {artist} (ID: {song_id})")
        
        # Check rules for this song
        cursor.execute("""
            SELECT COUNT(*) FROM association_rules 
            WHERE antecedent_song_id = ?
        """, (song_id,))
        
        rule_count = cursor.fetchone()[0]
        print(f"    Rules: {rule_count}")
    
    conn.close()

def main():
    print("🔧 Debugging Apriori Service")
    print("=" * 35)
    
    debug_apriori_logic()
    
    print(f"\n💡 Summary:")
    print("  If songs are found but no rules exist, the database might have issues")
    print("  If no songs are found, the search logic might be too strict")
    print("  If rules exist but no recommendations, the conversion logic has issues")

if __name__ == "__main__":
    main()
