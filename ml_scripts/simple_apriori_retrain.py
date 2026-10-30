#!/usr/bin/env python3
"""
Simple Apriori retraining without pandas dependency.
"""

import sqlite3
from collections import defaultdict
from itertools import combinations

def simple_apriori_training():
    """Train Apriori algorithm using simple Python without pandas."""
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    print("🤖 Simple Apriori Training (No Pandas)")
    print("=" * 45)
    
    # Get user listening history
    print("📊 Loading user listening history...")
    cursor.execute("""
        SELECT ulh.user_id, s.id, s.track_name, s.artist, s.genre
        FROM user_listening_history ulh
        JOIN songs s ON ulh.song_id = s.id
        ORDER BY ulh.user_id
    """)
    
    listening_data = cursor.fetchall()
    print(f"  ✅ Loaded {len(listening_data):,} listening records")
    
    # Group by user
    user_songs = defaultdict(list)
    for user_id, song_id, track_name, artist, genre in listening_data:
        user_songs[user_id].append((song_id, track_name, artist, genre))
    
    print(f"  👥 {len(user_songs)} users with listening history")
    print(f"  📈 Average songs per user: {len(listening_data)/len(user_songs):.1f}")
    
    # Find frequent song pairs
    print("\n🔍 Finding frequent song pairs...")
    song_pairs = defaultdict(int)
    song_counts = defaultdict(int)
    total_users = len(user_songs)
    
    for user_id, songs in user_songs.items():
        song_ids = [song[0] for song in songs]
        
        # Count individual songs
        for song_id in song_ids:
            song_counts[song_id] += 1
        
        # Count song pairs
        for song1, song2 in combinations(song_ids, 2):
            if song1 != song2:
                # Ensure consistent ordering
                pair = tuple(sorted([song1, song2]))
                song_pairs[pair] += 1
    
    # Filter pairs by minimum support
    min_support_count = max(1, int(total_users * 0.01))  # 1% support
    frequent_pairs = {pair: count for pair, count in song_pairs.items() 
                     if count >= min_support_count}
    
    print(f"  📊 Found {len(frequent_pairs)} frequent song pairs")
    print(f"  ⚙️ Minimum support: {min_support_count} users ({min_support_count/total_users*100:.1f}%)")
    
    # Generate association rules
    print("\n🎯 Generating association rules...")
    cursor.execute("DELETE FROM association_rules")  # Clear existing rules
    
    rules_added = 0
    min_confidence = 0.3  # 30% confidence threshold
    
    for (song1, song2), pair_count in frequent_pairs.items():
        # Rule: song1 -> song2
        song1_count = song_counts[song1]
        confidence1 = pair_count / song1_count if song1_count > 0 else 0
        
        if confidence1 >= min_confidence:
            support = pair_count / total_users
            lift = confidence1 / (song_counts[song2] / total_users) if song_counts[song2] > 0 else 0
            
            cursor.execute("""
                INSERT INTO association_rules 
                (antecedent_song_id, consequent_song_id, support, confidence, lift)
                VALUES (?, ?, ?, ?, ?)
            """, (song1, song2, support, confidence1, lift))
            rules_added += 1
        
        # Rule: song2 -> song1
        song2_count = song_counts[song2]
        confidence2 = pair_count / song2_count if song2_count > 0 else 0
        
        if confidence2 >= min_confidence:
            support = pair_count / total_users
            lift = confidence2 / (song_counts[song1] / total_users) if song_counts[song1] > 0 else 0
            
            cursor.execute("""
                INSERT INTO association_rules 
                (antecedent_song_id, consequent_song_id, support, confidence, lift)
                VALUES (?, ?, ?, ?, ?)
            """, (song2, song1, support, confidence2, lift))
            rules_added += 1
    
    conn.commit()
    print(f"  ✅ Generated {rules_added} association rules")
    
    # Test some Amapiano songs
    print("\n🎵 Testing Amapiano Song Rules...")
    test_songs = ["Abantwana Bakho", "ZENZELE", "Dlala Ka Yona"]
    
    for song_name in test_songs:
        cursor.execute("""
            SELECT id, track_name, artist 
            FROM songs 
            WHERE track_name LIKE ? AND genre = 'Amapiano'
            LIMIT 1
        """, (f"%{song_name}%",))
        
        song = cursor.fetchone()
        if song:
            song_id, track, artist = song
            
            cursor.execute("""
                SELECT COUNT(*) FROM association_rules 
                WHERE antecedent_song_id = ?
            """, (song_id,))
            
            rule_count = cursor.fetchone()[0]
            print(f"  🎵 {track}: {rule_count} rules")
            
            if rule_count > 0:
                cursor.execute("""
                    SELECT s.track_name, s.artist, ar.confidence
                    FROM association_rules ar
                    JOIN songs s ON ar.consequent_song_id = s.id
                    WHERE ar.antecedent_song_id = ?
                    ORDER BY ar.confidence DESC
                    LIMIT 2
                """, (song_id,))
                
                recommendations = cursor.fetchall()
                for rec_track, rec_artist, conf in recommendations:
                    print(f"    → {rec_track} by {rec_artist} (conf: {conf:.2f})")
    
    conn.close()
    return rules_added

def main():
    print("🔄 Simple Apriori Retraining")
    print("=" * 35)
    
    rules_count = simple_apriori_training()
    
    print(f"\n🎉 Training Complete!")
    print(f"✅ Generated {rules_count} association rules")
    print("✅ Amapiano songs now included in training data")
    print("✅ Your recommendation system is updated!")

if __name__ == "__main__":
    main()
