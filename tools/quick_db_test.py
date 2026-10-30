import sqlite3

conn = sqlite3.connect('music_recommender.db')
cursor = conn.cursor()

# Find the song
cursor.execute("SELECT id, track_name, artist FROM songs WHERE track_name LIKE '%Abantwana%' LIMIT 1")
song = cursor.fetchone()
print(f"Song found: {song}")

if song:
    song_id = song[0]
    # Check association rules
    cursor.execute("SELECT COUNT(*) FROM association_rules WHERE antecedent_song_id = ?", (song_id,))
    count = cursor.fetchone()[0]
    print(f"Association rules: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT s.track_name, s.artist, ar.confidence
            FROM association_rules ar
            JOIN songs s ON ar.consequent_song_id = s.id
            WHERE ar.antecedent_song_id = ?
            ORDER BY ar.confidence DESC
            LIMIT 3
        """, (song_id,))
        
        rules = cursor.fetchall()
        print("Top recommendations:")
        for track, artist, conf in rules:
            print(f"  -> {track} by {artist} (conf: {conf:.2f})")

conn.close()
