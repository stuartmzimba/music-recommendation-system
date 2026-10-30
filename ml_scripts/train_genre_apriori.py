#!/usr/bin/env python3
"""Genre-based Apriori training for music recommendations."""

import sqlite3
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_genre_transactions():
    """Create genre-based transactions for Apriori."""
    print("🎭 Creating genre-based transactions...")
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get user genre preferences (genres they listen to)
    cursor.execute('''
        SELECT ulh.user_id, s.genre, COUNT(*) as listen_count
        FROM user_listening_history ulh
        JOIN songs s ON ulh.song_id = s.id
        WHERE s.genre IS NOT NULL
        GROUP BY ulh.user_id, s.genre
        HAVING COUNT(*) >= 3
        ORDER BY ulh.user_id, listen_count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Group by user
    user_genres = {}
    for user_id, genre, count in results:
        if user_id not in user_genres:
            user_genres[user_id] = []
        user_genres[user_id].append(genre)
    
    # Filter users with at least 2 genres
    filtered_transactions = [genres for genres in user_genres.values() if len(genres) >= 2]
    
    print(f"  ✅ Created {len(filtered_transactions)} user genre transactions")
    print(f"  📈 Average genres per user: {sum(len(t) for t in filtered_transactions) / len(filtered_transactions):.1f}")
    
    # Show sample transactions
    print(f"  🎵 Sample user genre preferences:")
    for i, genres in enumerate(filtered_transactions[:5], 1):
        print(f"    User {i}: {', '.join(genres[:5])}")
    
    return filtered_transactions

def create_song_pair_transactions():
    """Create song pair transactions for users with multiple songs."""
    print("🎵 Creating song pair transactions...")
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get users with multiple songs from popular tracks
    cursor.execute('''
        SELECT ulh.user_id, s.track_name, s.artist, ulh.listen_count
        FROM user_listening_history ulh
        JOIN songs s ON ulh.song_id = s.id
        WHERE ulh.song_id IN (
            SELECT song_id 
            FROM user_listening_history 
            GROUP BY song_id 
            HAVING COUNT(DISTINCT user_id) >= 20
        )
        ORDER BY ulh.user_id, ulh.listen_count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Group by user and take top songs
    user_songs = {}
    for user_id, track_name, artist, listen_count in results:
        if user_id not in user_songs:
            user_songs[user_id] = []
        if len(user_songs[user_id]) < 10:  # Limit to top 10 songs per user
            song_key = f"{track_name} by {artist}"
            user_songs[user_id].append(song_key)
    
    # Filter users with at least 3 songs
    filtered_transactions = [songs for songs in user_songs.values() if len(songs) >= 3]
    
    print(f"  ✅ Created {len(filtered_transactions)} user song transactions")
    if filtered_transactions:
        print(f"  📈 Average songs per user: {sum(len(t) for t in filtered_transactions) / len(filtered_transactions):.1f}")
    
    return filtered_transactions

def train_genre_apriori():
    """Train Apriori on genre associations."""
    print("🤖 Training Genre-based Apriori...")
    
    transactions = create_genre_transactions()
    
    if len(transactions) < 10:
        print("❌ Not enough genre transactions")
        return False
    
    # Create basket matrix
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    basket_df = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"  📊 Genre basket matrix: {basket_df.shape}")
    
    # Mine frequent itemsets
    min_support = max(0.05, 20 / len(transactions))  # At least 20 users or 5%
    print(f"  ⚙️ Using min_support: {min_support:.3f}")
    
    try:
        frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True, verbose=1)
        print(f"  ✅ Found {len(frequent_itemsets)} frequent genre combinations")
        
        if len(frequent_itemsets) == 0:
            # Try lower support
            min_support = 10 / len(transactions)
            frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True, verbose=1)
            print(f"  ✅ Found {len(frequent_itemsets)} frequent genre combinations (lower support)")
        
        if len(frequent_itemsets) > 0:
            # Generate rules
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.3, num_itemsets=len(frequent_itemsets))
            
            if len(rules) == 0:
                rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.2, num_itemsets=len(frequent_itemsets))
            
            print(f"  ✅ Generated {len(rules)} genre association rules")
            
            if len(rules) > 0:
                save_genre_rules(rules)
                show_genre_rules(rules)
                return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def train_song_apriori():
    """Train Apriori on song associations."""
    print("\n🎵 Training Song-based Apriori...")
    
    transactions = create_song_pair_transactions()
    
    if len(transactions) < 10:
        print("❌ Not enough song transactions")
        return False
    
    # Create basket matrix
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    basket_df = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"  📊 Song basket matrix: {basket_df.shape}")
    
    # Mine frequent itemsets with very low support
    min_support = max(0.01, 5 / len(transactions))  # At least 5 users
    print(f"  ⚙️ Using min_support: {min_support:.3f}")
    
    try:
        frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True, verbose=1)
        print(f"  ✅ Found {len(frequent_itemsets)} frequent song combinations")
        
        if len(frequent_itemsets) > 0:
            # Generate rules
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.2, num_itemsets=len(frequent_itemsets))
            
            if len(rules) == 0:
                rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1, num_itemsets=len(frequent_itemsets))
            
            print(f"  ✅ Generated {len(rules)} song association rules")
            
            if len(rules) > 0:
                save_song_rules(rules)
                show_song_rules(rules)
                return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def save_genre_rules(rules):
    """Save genre-based rules as song recommendations."""
    print("  💾 Converting genre rules to song recommendations...")

    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()

    # Clear existing rules
    cursor.execute('DELETE FROM association_rules')

    saved_count = 0
    for i, rule in rules.iterrows():
        try:
            antecedent_genre = list(rule['antecedents'])[0]
            consequent_genre = list(rule['consequents'])[0]

            # Skip if same genre
            if antecedent_genre == consequent_genre:
                continue

            # Get multiple popular songs from these genres to create variety
            cursor.execute('''
                SELECT track_name, artist FROM songs
                WHERE genre = ?
                ORDER BY popularity_score DESC
                LIMIT 3
            ''', (antecedent_genre,))
            ant_songs = cursor.fetchall()

            cursor.execute('''
                SELECT track_name, artist FROM songs
                WHERE genre = ?
                ORDER BY popularity_score DESC
                LIMIT 3
            ''', (consequent_genre,))
            cons_songs = cursor.fetchall()

            # Create rules for each combination
            for ant_song in ant_songs:
                for cons_song in cons_songs:
                    if ant_song and cons_song and ant_song != cons_song:
                        # Get song IDs
                        cursor.execute('SELECT id FROM songs WHERE track_name = ? AND artist = ?', ant_song)
                        ant_song_id = cursor.fetchone()

                        cursor.execute('SELECT id FROM songs WHERE track_name = ? AND artist = ?', cons_song)
                        cons_song_id = cursor.fetchone()

                        if ant_song_id and cons_song_id:
                            cursor.execute('''
                                INSERT OR IGNORE INTO association_rules (
                                    antecedent_song_id, consequent_song_id,
                                    confidence, support, lift
                                ) VALUES (?, ?, ?, ?, ?)
                            ''', (
                                ant_song_id[0], cons_song_id[0],
                                float(rule['confidence']), float(rule['support']), float(rule['lift'])
                            ))
                            saved_count += 1

        except Exception as e:
            print(f"    Error saving rule: {e}")
            continue

    conn.commit()
    conn.close()

    print(f"  ✅ Saved {saved_count} genre-based song rules")

def save_song_rules(rules):
    """Save song-based rules."""
    print("  💾 Saving song rules...")
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    saved_count = 0
    for i, rule in rules.iterrows():
        try:
            antecedent = list(rule['antecedents'])[0]
            consequent = list(rule['consequents'])[0]
            
            # Parse "Song by Artist" format
            if ' by ' in antecedent and ' by ' in consequent:
                ant_parts = antecedent.split(' by ')
                cons_parts = consequent.split(' by ')
                
                if len(ant_parts) == 2 and len(cons_parts) == 2:
                    # Get song IDs
                    cursor.execute('SELECT id FROM songs WHERE track_name = ? AND artist = ?',
                                 (ant_parts[0].strip(), ant_parts[1].strip()))
                    ant_song_id = cursor.fetchone()

                    cursor.execute('SELECT id FROM songs WHERE track_name = ? AND artist = ?',
                                 (cons_parts[0].strip(), cons_parts[1].strip()))
                    cons_song_id = cursor.fetchone()

                    if ant_song_id and cons_song_id:
                        cursor.execute('''
                            INSERT INTO association_rules (
                                antecedent_song_id, consequent_song_id,
                                confidence, support, lift
                            ) VALUES (?, ?, ?, ?, ?)
                        ''', (
                            ant_song_id[0], cons_song_id[0],
                            float(rule['confidence']), float(rule['support']), float(rule['lift'])
                        ))
                        saved_count += 1
                    
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Saved {saved_count} song rules")

def show_genre_rules(rules):
    """Show sample genre rules."""
    print(f"\n  🎭 Sample genre association rules:")
    for i, rule in rules.head(5).iterrows():
        antecedent = list(rule['antecedents'])[0]
        consequent = list(rule['consequents'])[0]
        print(f"    {antecedent} → {consequent} (confidence: {rule['confidence']:.2f})")

def show_song_rules(rules):
    """Show sample song rules."""
    print(f"\n  🎵 Sample song association rules:")
    for i, rule in rules.head(3).iterrows():
        antecedent = list(rule['antecedents'])[0]
        consequent = list(rule['consequents'])[0]
        print(f"    {antecedent} → {consequent} (confidence: {rule['confidence']:.2f})")

def main():
    """Main function."""
    print("🚀 Genre & Song Apriori Training")
    print("=" * 40)
    
    # Try genre-based first
    genre_success = train_genre_apriori()
    
    # Try song-based if genre didn't work well
    song_success = train_song_apriori()
    
    # Check final results
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM association_rules')
    rule_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n🎉 Training completed!")
    print(f"📊 Final results: {rule_count} association rules generated")
    
    if rule_count > 0:
        print("✅ Apriori algorithm is now working!")
    else:
        print("⚠️ No rules generated - content-based recommendations will be primary")

if __name__ == "__main__":
    main()
