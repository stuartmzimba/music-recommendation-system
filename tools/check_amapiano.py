#!/usr/bin/env python3
"""Check current Amapiano songs in the database."""

import sqlite3

def check_current_amapiano():
    """Check what songs are currently assigned to Amapiano genre."""
    print("🔍 Current Amapiano Songs in Database")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT track_name, artist, popularity_score 
        FROM songs 
        WHERE genre = 'Amapiano' 
        ORDER BY popularity_score DESC 
        LIMIT 15
    ''')
    
    songs = cursor.fetchall()
    
    print(f"Found {len(songs)} Amapiano songs:")
    for i, (track, artist, pop) in enumerate(songs, 1):
        print(f"{i:2d}. {track} by {artist} (popularity: {pop})")
    
    conn.close()

if __name__ == "__main__":
    check_current_amapiano()
