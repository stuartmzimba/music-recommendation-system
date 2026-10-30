#!/usr/bin/env python3
"""Optimized Apriori training for large datasets."""

import sqlite3
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_optimized_dataset():
    """Create an optimized dataset for Apriori by filtering popular songs and active users."""
    print("🔧 Creating optimized dataset for Apriori...")
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get top 500 most popular songs (songs listened to by most users)
    cursor.execute('''
        SELECT song_id, COUNT(DISTINCT user_id) as user_count
        FROM user_listening_history
        GROUP BY song_id
        ORDER BY user_count DESC
        LIMIT 500
    ''')
    popular_songs = [row[0] for row in cursor.fetchall()]
    
    print(f"  📊 Selected top 500 popular songs")
    
    # Get users who listen to at least 5 of these popular songs
    placeholders = ','.join(['?' for _ in popular_songs])
    cursor.execute(f'''
        SELECT user_id, COUNT(DISTINCT song_id) as song_count
        FROM user_listening_history
        WHERE song_id IN ({placeholders})
        GROUP BY user_id
        HAVING COUNT(DISTINCT song_id) >= 5
        ORDER BY song_count DESC
    ''', popular_songs)
    
    active_users = [row[0] for row in cursor.fetchall()]
    print(f"  👥 Selected {len(active_users)} active users")
    
    # Create filtered transactions
    user_placeholders = ','.join(['?' for _ in active_users])
    song_placeholders = ','.join(['?' for _ in popular_songs])
    
    cursor.execute(f'''
        SELECT ulh.user_id, s.track_name, s.artist
        FROM user_listening_history ulh
        JOIN songs s ON ulh.song_id = s.id
        WHERE ulh.user_id IN ({user_placeholders})
        AND ulh.song_id IN ({song_placeholders})
        ORDER BY ulh.user_id
    ''', active_users + popular_songs)
    
    results = cursor.fetchall()
    conn.close()
    
    # Group by user
    transactions = {}
    for user_id, track_name, artist in results:
        song_key = f"{track_name} - {artist}"
        if user_id not in transactions:
            transactions[user_id] = []
        transactions[user_id].append(song_key)
    
    # Convert to list of lists
    transaction_list = list(transactions.values())
    
    print(f"  ✅ Created {len(transaction_list)} user transactions")
    print(f"  📈 Average songs per user: {sum(len(t) for t in transaction_list) / len(transaction_list):.1f}")
    
    return transaction_list

def train_optimized_apriori():
    """Train Apriori with optimized dataset."""
    print("🤖 Training Apriori with optimized dataset...")
    
    # Get optimized transactions
    transactions = create_optimized_dataset()
    
    if len(transactions) < 10:
        print("❌ Not enough transactions for Apriori")
        return False
    
    # Create basket matrix
    print("  🔄 Creating basket matrix...")
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    basket_df = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"  📊 Basket matrix shape: {basket_df.shape}")
    
    # Mine frequent itemsets with lower support
    min_support = max(0.01, 10 / len(transactions))  # At least 10 users or 1%
    print(f"  ⚙️ Using min_support: {min_support:.4f}")
    
    try:
        frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True, verbose=1)
        print(f"  ✅ Found {len(frequent_itemsets)} frequent itemsets")
        
        if len(frequent_itemsets) == 0:
            print("  ⚠️ No frequent itemsets found, lowering support...")
            min_support = 5 / len(transactions)  # At least 5 users
            frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True, verbose=1)
            print(f"  ✅ Found {len(frequent_itemsets)} frequent itemsets with lower support")
        
        if len(frequent_itemsets) == 0:
            print("  ❌ Still no frequent itemsets found")
            return False
        
        # Generate association rules
        min_confidence = 0.1
        print(f"  🔗 Generating association rules with min_confidence: {min_confidence}")
        
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence, num_itemsets=len(frequent_itemsets))
        
        if len(rules) == 0:
            print("  ⚠️ No rules found, lowering confidence...")
            min_confidence = 0.05
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence, num_itemsets=len(frequent_itemsets))
        
        print(f"  ✅ Generated {len(rules)} association rules")
        
        if len(rules) > 0:
            # Save rules to database
            save_rules_to_database(rules)
            
            # Show sample rules
            print(f"\n  🎵 Sample association rules:")
            for i, rule in rules.head(5).iterrows():
                antecedent = list(rule['antecedents'])[0]
                consequent = list(rule['consequents'])[0]
                confidence = rule['confidence']
                support = rule['support']
                print(f"    {antecedent} → {consequent}")
                print(f"      Confidence: {confidence:.2f}, Support: {support:.4f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error in Apriori training: {e}")
        return False

def save_rules_to_database(rules):
    """Save association rules to database."""
    print("  💾 Saving rules to database...")
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Clear existing rules
    cursor.execute('DELETE FROM association_rules')
    
    saved_count = 0
    for i, rule in rules.iterrows():
        try:
            antecedent = list(rule['antecedents'])[0]
            consequent = list(rule['consequents'])[0]
            
            # Parse song names
            if ' - ' in antecedent and ' - ' in consequent:
                ant_parts = antecedent.split(' - ')
                cons_parts = consequent.split(' - ')
                
                if len(ant_parts) >= 2 and len(cons_parts) >= 2:
                    cursor.execute('''
                        INSERT INTO association_rules (
                            antecedent_song, antecedent_artist,
                            consequent_song, consequent_artist,
                            confidence, support, lift
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ant_parts[0].strip(), ant_parts[1].strip(),
                        cons_parts[0].strip(), cons_parts[1].strip(),
                        float(rule['confidence']), float(rule['support']), float(rule['lift'])
                    ))
                    saved_count += 1
        except Exception as e:
            logger.warning(f"Error saving rule: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Saved {saved_count} rules to database")

def main():
    """Main function."""
    print("🚀 Optimized Apriori Training")
    print("=" * 40)
    
    success = train_optimized_apriori()
    
    if success:
        print("\n🎉 Apriori training completed successfully!")
        
        # Check final results
        conn = sqlite3.connect('music_recommender.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM association_rules')
        rule_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Final results: {rule_count} association rules generated")
    else:
        print("\n❌ Apriori training failed")

if __name__ == "__main__":
    main()
