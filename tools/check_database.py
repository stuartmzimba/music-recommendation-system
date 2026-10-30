#!/usr/bin/env python3
"""Quick database check script."""

import sqlite3
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get basic stats
    cursor.execute('SELECT COUNT(*) FROM songs')
    songs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_listening_history')
    history = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_listening_history')
    users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT genre) FROM songs')
    genre_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM association_rules')
    rules = cursor.fetchone()[0]
    
    print(f"🎵 Songs: {songs:,}")
    print(f"🎧 Listening Records: {history:,}")
    print(f"👥 Users: {users:,}")
    print(f"🎭 Genres: {genre_count}")
    print(f"🔗 Association Rules: {rules}")
    
    # Get genres
    cursor.execute('SELECT DISTINCT genre FROM songs ORDER BY genre')
    genres = [row[0] for row in cursor.fetchall()]
    
    print(f"\nAvailable genres ({len(genres)}):")
    for i, genre in enumerate(genres, 1):
        print(f"{i:2d}. {genre}")

    # Check sample songs with genres and popularity
    print(f"\nSample songs with genres and popularity:")
    cursor.execute('SELECT track_name, artist, genre, popularity_score FROM songs LIMIT 10')
    songs = cursor.fetchall()
    for song in songs:
        print(f"  {song[0]} by {song[1]} | Genre: {song[2]} | Popularity: {song[3]}")

    # Check genre distribution
    print(f"\nGenre distribution:")
    cursor.execute('SELECT genre, COUNT(*) as count FROM songs GROUP BY genre ORDER BY count DESC LIMIT 10')
    genre_counts = cursor.fetchall()
    for genre, count in genre_counts:
        print(f"  {genre}: {count} songs")

    # Check popularity score range
    cursor.execute('SELECT MIN(popularity_score), MAX(popularity_score), AVG(popularity_score) FROM songs')
    min_pop, max_pop, avg_pop = cursor.fetchone()
    print(f"\nPopularity scores:")
    print(f"  Min: {min_pop}")
    print(f"  Max: {max_pop}")
    print(f"  Average: {avg_pop:.2f}")

    # Check top genres by average popularity
    print(f"\nTop 10 genres by average popularity:")
    cursor.execute('SELECT genre, COUNT(*) as count, AVG(popularity_score) as avg_pop FROM songs GROUP BY genre ORDER BY avg_pop DESC LIMIT 10')
    results = cursor.fetchall()
    for genre, count, avg_pop in results:
        print(f"  {genre}: {count} songs, avg popularity: {avg_pop:.1f}")

    # Check some high and low popularity songs
    print(f"\nTop 5 most popular songs:")
    cursor.execute('SELECT track_name, artist, genre, popularity_score FROM songs ORDER BY popularity_score DESC LIMIT 5')
    top_songs = cursor.fetchall()
    for song in top_songs:
        print(f"  {song[0]} by {song[1]} ({song[2]}) - {song[3]}")

    print(f"\nBottom 5 least popular songs:")
    cursor.execute('SELECT track_name, artist, genre, popularity_score FROM songs ORDER BY popularity_score ASC LIMIT 5')
    bottom_songs = cursor.fetchall()
    for song in bottom_songs:
        print(f"  {song[0]} by {song[1]} ({song[2]}) - {song[3]}")

    conn.close()

if __name__ == "__main__":
    main()
