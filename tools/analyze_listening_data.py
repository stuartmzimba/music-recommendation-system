#!/usr/bin/env python3
"""Analyze listening data for Apriori algorithm."""

import sqlite3
import pandas as pd
from collections import defaultdict

def analyze_listening_patterns():
    """Analyze listening patterns to understand Apriori issues."""
    print("🔍 Analyzing Listening Data for Apriori Algorithm...")
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Basic stats
    cursor.execute('SELECT COUNT(*) FROM user_listening_history')
    total_records = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_listening_history')
    unique_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT song_id) FROM user_listening_history')
    unique_songs = cursor.fetchone()[0]
    
    print(f"📊 Basic Statistics:")
    print(f"  Total listening records: {total_records:,}")
    print(f"  Unique users: {unique_users:,}")
    print(f"  Unique songs: {unique_songs:,}")
    print(f"  Average songs per user: {total_records/unique_users:.1f}")
    print(f"  Sparsity ratio: {unique_songs/unique_users:.1f} unique songs per user")
    
    # Check user listening patterns
    cursor.execute('''
        SELECT user_id, COUNT(*) as song_count 
        FROM user_listening_history 
        GROUP BY user_id 
        ORDER BY song_count DESC 
        LIMIT 10
    ''')
    top_users = cursor.fetchall()
    
    print(f"\n👥 Top 10 users by listening activity:")
    for user, count in top_users:
        print(f"  {user}: {count} songs")
    
    # Check song popularity in listening history
    cursor.execute('''
        SELECT s.track_name, s.artist, COUNT(*) as listen_count
        FROM user_listening_history ulh
        JOIN songs s ON ulh.song_id = s.id
        GROUP BY ulh.song_id
        ORDER BY listen_count DESC
        LIMIT 10
    ''')
    popular_songs = cursor.fetchall()
    
    print(f"\n🎵 Top 10 most listened songs:")
    for song, artist, count in popular_songs:
        print(f"  {song} by {artist}: {count} users")
    
    # Check for potential associations
    cursor.execute('''
        SELECT user_id, COUNT(*) as songs_per_user
        FROM user_listening_history
        GROUP BY user_id
        HAVING COUNT(*) >= 2
        ORDER BY songs_per_user DESC
        LIMIT 5
    ''')
    multi_song_users = cursor.fetchall()
    
    print(f"\n🔗 Users with multiple songs (potential for associations):")
    for user, count in multi_song_users:
        print(f"  {user}: {count} songs")
        
        # Show what songs this user listens to
        cursor.execute('''
            SELECT s.track_name, s.artist
            FROM user_listening_history ulh
            JOIN songs s ON ulh.song_id = s.id
            WHERE ulh.user_id = ?
            ORDER BY ulh.listen_count DESC
        ''', (user,))
        user_songs = cursor.fetchall()
        
        for song, artist in user_songs[:5]:  # Show top 5 songs
            print(f"    - {song} by {artist}")
        print()
    
    # Calculate minimum support threshold needed
    min_users_for_support = max(2, int(unique_users * 0.01))  # 1% support
    print(f"📈 Apriori Analysis:")
    print(f"  Minimum users needed for 1% support: {min_users_for_support}")
    
    cursor.execute('''
        SELECT COUNT(*) as song_count
        FROM (
            SELECT song_id, COUNT(*) as users
            FROM user_listening_history
            GROUP BY song_id
            HAVING COUNT(*) >= ?
        )
    ''', (min_users_for_support,))
    
    frequent_songs = cursor.fetchone()[0]
    print(f"  Songs with >= {min_users_for_support} users: {frequent_songs}")
    
    if frequent_songs < 2:
        print(f"  ⚠️ Not enough frequent songs for associations!")
        print(f"  💡 Recommendation: Lower min_support to 0.001 or 0.0001")
    
    conn.close()
    return True

def suggest_apriori_fix():
    """Suggest fixes for Apriori algorithm."""
    print("\n🛠️ Apriori Algorithm Fix Suggestions:")
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Check current association rules
    cursor.execute('SELECT COUNT(*) FROM association_rules')
    current_rules = cursor.fetchone()[0]
    
    print(f"  Current association rules: {current_rules}")
    
    if current_rules == 0:
        print(f"  🔧 Suggested fixes:")
        print(f"    1. Lower min_support from 0.01 to 0.001 (0.1%)")
        print(f"    2. Lower min_confidence from 0.1 to 0.05 (5%)")
        print(f"    3. Focus on genre-based associations instead of individual songs")
        print(f"    4. Create synthetic user clusters with overlapping preferences")
        
        # Check if we can create genre-based associations
        cursor.execute('''
            SELECT s.genre, COUNT(DISTINCT ulh.user_id) as user_count
            FROM user_listening_history ulh
            JOIN songs s ON ulh.song_id = s.id
            GROUP BY s.genre
            ORDER BY user_count DESC
            LIMIT 10
        ''')
        genre_popularity = cursor.fetchall()
        
        print(f"\n  🎭 Genre-based user counts:")
        for genre, users in genre_popularity:
            print(f"    {genre}: {users} users")
    
    conn.close()

def main():
    """Main analysis function."""
    analyze_listening_patterns()
    suggest_apriori_fix()

if __name__ == "__main__":
    main()
