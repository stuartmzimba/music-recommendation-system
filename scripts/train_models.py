#!/usr/bin/env python3
"""
Training script for the Music Recommender System.
This script loads data and trains the recommendation models.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ml.data_pipeline.data_loader import DataLoader
from ml.apriori.apriori_trainer import AprioriTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main training pipeline."""
    logger.info("🚀 Starting Music Recommender training pipeline...")
    
    try:
        # Step 1: Load sample data
        logger.info("📊 Step 1: Loading sample data...")
        data_loader = DataLoader()
        
        # Load sample data
        load_results = data_loader.load_sample_data()
        
        if load_results['songs'] == 0:
            logger.error("❌ No songs loaded. Cannot proceed with training.")
            return False
        
        # Print data statistics
        stats = data_loader.get_data_statistics()
        logger.info("📈 Data Statistics:")
        for key, value in stats.items():
            logger.info(f"   - {key}: {value}")
        
        data_loader.close()
        
        # Step 2: Train Apriori model
        logger.info("🤖 Step 2: Training Apriori association rules...")
        apriori_trainer = AprioriTrainer(min_support=0.001, min_confidence=0.05)
        
        training_results = apriori_trainer.train()
        
        if training_results['success']:
            logger.info("✅ Apriori training completed successfully!")
            logger.info(f"📊 Training Results:")
            for key, value in training_results.items():
                if key != 'success':
                    logger.info(f"   - {key}: {value}")
        else:
            logger.error(f"❌ Apriori training failed: {training_results.get('error', 'Unknown error')}")
            return False
        
        # Step 3: Train & persist Content-based model
        logger.info("🎯 Step 3: Training Content-based model...")
        from ml.content_based.content_recommender import ContentBasedRecommender
        cb_recommender = ContentBasedRecommender()
        if cb_recommender.train():
            os.makedirs("models", exist_ok=True)
            cb_recommender.save_model("models/content_based_model.joblib")
            logger.info("✅ Content-based model trained and saved to models/content_based_model.joblib")
        else:
            logger.warning("⚠️ Content-based training completed with warnings")
        cb_recommender.close()
        
        logger.info("🎉 Training pipeline completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Training pipeline failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
