#!/usr/bin/env python3
"""
Improve Apriori recommendations by adjusting parameters and using genre-based rules.
"""

import sqlite3
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import numpy as np
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedAprioriTrainer:
    def __init__(self, db_path='music_recommender.db'):
        self.db_path = db_path
        
    def get_song_recommendations_from_genre_rules(self, song_name, limit=5):
        """Get song recommendations using genre-based association rules."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get the genre of the input song
            song_query = """
            SELECT genre FROM songs 
            WHERE track_name = ? OR track_name LIKE ?
            LIMIT 1
            """
            song_genre = pd.read_sql_query(
                song_query, 
                conn, 
                params=[song_name, f"%{song_name}%"]
            )
            
            if song_genre.empty:
                logger.warning(f"Song '{song_name}' not found")
                return []
            
            input_genre = song_genre.iloc[0]['genre']
            logger.info(f"Input song genre: {input_genre}")
            
            # Get genre association rules where input genre is antecedent
            genre_rules_query = """
            SELECT DISTINCT consequent_genre, confidence, lift
            FROM association_rules ar
            WHERE antecedent_genre = ?
            ORDER BY confidence DESC, lift DESC
            LIMIT 5
            """
            
            genre_rules = pd.read_sql_query(
                genre_rules_query,
                conn,
                params=[input_genre]
            )
            
            recommendations = []
            
            # For each recommended genre, get popular songs
            for _, rule in genre_rules.iterrows():
                rec_genre = rule['consequent_genre']
                confidence = rule['confidence']
                
                # Get popular songs from recommended genre
                songs_query = """
                SELECT track_name, artist, popularity_score
                FROM songs
                WHERE genre = ?
                ORDER BY popularity_score DESC
                LIMIT 3
                """
                
                genre_songs = pd.read_sql_query(
                    songs_query,
                    conn,
                    params=[rec_genre]
                )
                
                for _, song in genre_songs.iterrows():
                    recommendations.append({
                        'track_name': song['track_name'],
                        'artist': song['artist'],
                        'genre': rec_genre,
                        'confidence': confidence,
                        'popularity': song['popularity_score'],
                        'reason': f"Genre association: {input_genre} → {rec_genre}"
                    })
            
            return recommendations[:limit]
            
        finally:
            conn.close()
    
    def train_with_lower_support(self, min_support=0.005):
        """Train Apriori with lower minimum support threshold."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            print(f"🔄 Retraining with lower support threshold: {min_support}")
            
            # Get user listening history
            query = """
            SELECT ulh.user_id, s.track_name, s.artist
            FROM user_listening_history ulh
            JOIN songs s ON ulh.song_id = s.id
            ORDER BY ulh.user_id
            """
            
            df = pd.read_sql_query(query, conn)
            
            # Create song identifiers
            df['song_id'] = df['track_name'] + ' - ' + df['artist']
            
            # Group by user to create baskets
            user_baskets = df.groupby('user_id')['song_id'].apply(list).tolist()
            
            print(f"  📊 Created {len(user_baskets)} user baskets")
            print(f"  📈 Average songs per basket: {np.mean([len(basket) for basket in user_baskets]):.1f}")
            
            # Create transaction matrix
            te = TransactionEncoder()
            te_ary = te.fit(user_baskets).transform(user_baskets)
            basket_df = pd.DataFrame(te_ary, columns=te.columns_)
            
            print(f"  📊 Basket matrix shape: {basket_df.shape}")
            
            # Apply Apriori with lower support
            frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True)
            
            if len(frequent_itemsets) > 0:
                print(f"  ✅ Found {len(frequent_itemsets)} frequent itemsets")
                
                # Generate association rules
                rules = association_rules(
                    frequent_itemsets, 
                    metric="confidence", 
                    min_threshold=0.3,
                    num_itemsets=len(frequent_itemsets)
                )
                
                if len(rules) > 0:
                    print(f"  ✅ Generated {len(rules)} song association rules")
                    
                    # Save rules to database
                    self._save_song_rules_to_db(rules, conn)
                    return len(rules)
                else:
                    print("  ❌ No association rules generated")
                    return 0
            else:
                print(f"  ❌ No frequent itemsets found with support {min_support}")
                return 0
                
        finally:
            conn.close()
    
    def _save_song_rules_to_db(self, rules, conn):
        """Save song-based association rules to database."""
        cursor = conn.cursor()
        
        # Clear existing song-based rules (keep genre rules)
        cursor.execute("DELETE FROM association_rules WHERE antecedent_song_id IS NOT NULL")
        
        for _, rule in rules.iterrows():
            antecedent = list(rule['antecedents'])[0]
            consequent = list(rule['consequents'])[0]
            
            # Get song IDs
            ant_parts = antecedent.split(' - ')
            cons_parts = consequent.split(' - ')
            
            if len(ant_parts) >= 2 and len(cons_parts) >= 2:
                ant_track, ant_artist = ant_parts[0], ' - '.join(ant_parts[1:])
                cons_track, cons_artist = cons_parts[0], ' - '.join(cons_parts[1:])
                
                # Get song IDs from database
                ant_id = cursor.execute(
                    "SELECT id FROM songs WHERE track_name = ? AND artist = ?",
                    (ant_track, ant_artist)
                ).fetchone()
                
                cons_id = cursor.execute(
                    "SELECT id FROM songs WHERE track_name = ? AND artist = ?",
                    (cons_track, cons_artist)
                ).fetchone()
                
                if ant_id and cons_id:
                    cursor.execute("""
                        INSERT INTO association_rules 
                        (antecedent_song_id, consequent_song_id, confidence, support, lift)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        ant_id[0], cons_id[0],
                        rule['confidence'], rule['support'], rule['lift']
                    ))
        
        conn.commit()
        print(f"  💾 Saved song-based rules to database")

def main():
    print("🔧 Improving Apriori Recommendations")
    print("=" * 50)
    
    trainer = ImprovedAprioriTrainer()
    
    # Test current genre-based recommendations
    print("\n🎵 Testing Genre-based Recommendations:")
    test_songs = [
        "Abantwana Bakho (feat. Thatohatsi, Young Stunna & Nkosazana Daughter)",
        "ZENZELE (feat. Royal MusiQ, Uncool MC, Xduppy, & CowBoii)",
        "Dlala Ka Yona (feat. Focalistic, Ricky Lenyora, Uncool MC & Mellow & Sleazy)"
    ]
    
    for song in test_songs:
        print(f"\n🎵 Testing: {song}")
        recommendations = trainer.get_song_recommendations_from_genre_rules(song)
        
        if recommendations:
            print("  ✅ Genre-based recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"    {i}. {rec['track_name']} by {rec['artist']}")
                print(f"       Genre: {rec['genre']} | Confidence: {rec['confidence']:.2f}")
        else:
            print("  ❌ No genre-based recommendations found")
    
    # Try training with lower support
    print(f"\n🔄 Attempting song-based Apriori with lower support...")
    rules_count = trainer.train_with_lower_support(min_support=0.003)
    
    if rules_count > 0:
        print(f"✅ Successfully generated {rules_count} song-based association rules!")
    else:
        print("❌ Still no song-based rules. Genre-based recommendations are the best option.")
    
    print("\n🎉 Recommendation improvement complete!")

if __name__ == "__main__":
    main()
