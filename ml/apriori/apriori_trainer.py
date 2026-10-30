"""
Apriori algorithm implementation for mining association rules from music listening data.
"""

import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime

from backend.app.core.database import SessionLocal
from backend.app.models.database import Song, AssociationRule, UserListeningHistory

logger = logging.getLogger(__name__)


class AprioriTrainer:
    """Trainer for Apriori association rule mining."""
    
    def __init__(self, min_support: float = 0.001, min_confidence: float = 0.05, limit_users: Optional[int] = None):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.limit_users = limit_users
        self.db = SessionLocal()
    
    def prepare_transaction_data(self) -> List[List[str]]:
        """
        Prepare transaction data from user listening history.
        Each transaction is a list of songs a user has listened to.
        """
        logger.info("Preparing transaction data from listening history...")
        
        query = self.db.query(
            UserListeningHistory.user_id,
            Song.track_name,
            Song.artist
        ).join(Song)

        if self.limit_users:
            user_ids = [u[0] for u in self.db.query(UserListeningHistory.user_id).distinct().limit(self.limit_users).all()]
            query = query.filter(UserListeningHistory.user_id.in_(user_ids))
        
        listening_data = query.all()
        
        if not listening_data:
            logger.warning("No listening history found")
            return []
        
        # Group by user to create transactions
        user_transactions = {}
        for user_id, track_name, artist in listening_data:
            song_identifier = f"{track_name} - {artist}"
            if user_id not in user_transactions:
                user_transactions[user_id] = set()
            user_transactions[user_id].add(song_identifier)
        
        # Convert to list of lists
        transactions = [list(songs) for songs in user_transactions.values()]
        
        logger.info(f"Prepared {len(transactions)} user transactions")
        return transactions
    
    def create_basket_matrix(self, transactions: List[List[str]]) -> pd.DataFrame:
        """Create binary basket matrix for Apriori algorithm."""
        logger.info("Creating basket matrix...")
        
        # Use TransactionEncoder to create binary matrix
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=te.columns_)
        
        logger.info(f"Created basket matrix with shape {df.shape}")
        return df
    
    def mine_frequent_itemsets(self, basket_df: pd.DataFrame) -> pd.DataFrame:
        """Mine frequent itemsets using fast FP-Growth or Apriori algorithm."""
        logger.info(f"Mining frequent itemsets with min_support={self.min_support}...")
        
        try:
            frequent_itemsets = fpgrowth(
                basket_df, 
                min_support=self.min_support, 
                use_colnames=True,
                max_len=2
            )
        except Exception as e:
            logger.info(f"FP-Growth fallback to Apriori: {e}")
            frequent_itemsets = apriori(
                basket_df, 
                min_support=self.min_support, 
                use_colnames=True,
                max_len=2,
                low_memory=True
            )
        
        if frequent_itemsets.empty:
            logger.warning("No frequent itemsets found. Consider lowering min_support.")
            return frequent_itemsets
        
        logger.info(f"Found {len(frequent_itemsets)} frequent itemsets")
        return frequent_itemsets
    
    def generate_association_rules(self, frequent_itemsets: pd.DataFrame) -> pd.DataFrame:
        """Generate association rules from frequent itemsets."""
        logger.info(f"Generating association rules with min_confidence={self.min_confidence}...")
        
        if frequent_itemsets.empty:
            logger.warning("No frequent itemsets available for rule generation")
            return pd.DataFrame()
        
        # Generate association rules
        rules = association_rules(
            frequent_itemsets,
            metric="confidence",
            min_threshold=self.min_confidence
        )
        
        if rules.empty:
            logger.warning("No association rules found. Consider lowering min_confidence.")
            return rules
        
        # Filter for single-item antecedents and consequents
        rules = rules[
            (rules['antecedents'].apply(len) == 1) & 
            (rules['consequents'].apply(len) == 1)
        ]
        
        logger.info(f"Generated {len(rules)} association rules")
        return rules
    
    def save_rules_to_database(self, rules: pd.DataFrame) -> int:
        """Save association rules to database using bulk insert."""
        logger.info("Saving association rules to database...")
        
        if rules.empty:
            logger.warning("No rules to save")
            return 0
        
        # Clear existing rules
        self.db.query(AssociationRule).delete()
        
        # Pre-load song map for O(1) lookups
        song_map = {
            (s.track_name.strip(), s.artist.strip()): s.id
            for s in self.db.query(Song.id, Song.track_name, Song.artist).all()
        }
        
        rules_to_add = []
        for _, rule in rules.iterrows():
            try:
                # Extract song names from frozensets
                antecedent_song = list(rule['antecedents'])[0]
                consequent_song = list(rule['consequents'])[0]
                
                antecedent_parts = antecedent_song.split(' - ')
                consequent_parts = consequent_song.split(' - ')
                
                if len(antecedent_parts) != 2 or len(consequent_parts) != 2:
                    continue
                
                ant_id = song_map.get((antecedent_parts[0].strip(), antecedent_parts[1].strip()))
                con_id = song_map.get((consequent_parts[0].strip(), consequent_parts[1].strip()))
                
                if not ant_id or not con_id:
                    continue
                
                # Create association rule
                association_rule = AssociationRule(
                    antecedent_song_id=ant_id,
                    consequent_song_id=con_id,
                    support=float(rule['support']),
                    confidence=float(rule['confidence']),
                    lift=float(rule['lift']),
                    conviction=float(rule['conviction']) if not np.isinf(rule['conviction']) else None
                )
                rules_to_add.append(association_rule)
                
            except Exception as e:
                continue
        
        if rules_to_add:
            self.db.bulk_save_objects(rules_to_add)
            self.db.commit()
            
        saved_count = len(rules_to_add)
        logger.info(f"Saved {saved_count} association rules to database")
        return saved_count
    
    def train(self) -> Dict[str, any]:
        """
        Complete training pipeline for Apriori algorithm.
        
        Returns:
            Dictionary with training results and statistics
        """
        start_time = datetime.now()
        logger.info("Starting Apriori training pipeline...")
        
        try:
            # Step 1: Prepare transaction data
            transactions = self.prepare_transaction_data()
            
            if not transactions:
                return {
                    "success": False,
                    "error": "No transaction data available",
                    "duration": (datetime.now() - start_time).total_seconds()
                }
            
            # Step 2: Create basket matrix
            basket_df = self.create_basket_matrix(transactions)
            
            # Step 3: Mine frequent itemsets
            frequent_itemsets = self.mine_frequent_itemsets(basket_df)
            
            # Step 4: Generate association rules
            rules = self.generate_association_rules(frequent_itemsets)
            
            # Step 5: Save to database
            saved_rules = self.save_rules_to_database(rules)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "num_transactions": len(transactions),
                "num_unique_items": len(basket_df.columns),
                "num_frequent_itemsets": len(frequent_itemsets),
                "num_rules_generated": len(rules),
                "num_rules_saved": saved_rules,
                "min_support": self.min_support,
                "min_confidence": self.min_confidence,
                "duration": duration
            }
            
            logger.info(f"Apriori training completed successfully in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Error in Apriori training: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        finally:
            self.db.close()


def main():
    """Main function for running Apriori training."""
    trainer = AprioriTrainer(min_support=0.001, min_confidence=0.05)
    result = trainer.train()
    
    if result["success"]:
        print("✅ Apriori training completed successfully!")
        print(f"📊 Statistics:")
        print(f"   - Transactions: {result['num_transactions']}")
        print(f"   - Unique items: {result['num_unique_items']}")
        print(f"   - Frequent itemsets: {result['num_frequent_itemsets']}")
        print(f"   - Rules generated: {result['num_rules_generated']}")
        print(f"   - Rules saved: {result['num_rules_saved']}")
        print(f"   - Duration: {result['duration']:.2f} seconds")
    else:
        print(f"❌ Apriori training failed: {result['error']}")


if __name__ == "__main__":
    main()
