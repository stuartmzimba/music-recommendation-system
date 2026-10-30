#!/usr/bin/env python3
"""Check current songs in database."""

import sqlite3

def check_songs():
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Check total songs
    cursor.execute('SELECT COUNT(*) FROM songs')
    total = cursor.fetchone()[0]
    print(f"Total songs: {total}")
    
    # Check songs with Spotify IDs
    cursor.execute('SELECT COUNT(*) FROM songs WHERE spotify_id IS NOT NULL')
    spotify_songs = cursor.fetchone()[0]
    print(f"Songs with Spotify IDs: {spotify_songs}")
    
    # Show sample songs
    cursor.execute('SELECT track_name, artist, genre, spotify_id FROM songs LIMIT 10')
    songs = cursor.fetchall()
    
    print("\nSample songs:")
    for song in songs:
        spotify_status = "✅ Spotify" if song[3] else "❌ No Spotify ID"
        print(f"  {song[0]} - {song[1]} ({song[2]}) [{spotify_status}]")
    
    conn.close()

if __name__ == "__main__":
    check_songs()
