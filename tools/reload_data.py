#!/usr/bin/env python3
"""
Script to reload music data from CSV files.
Use this when you add new songs, artists, or genres to the CSV files.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ml.data_pipeline.data_loader import DataLoader
from backend.app.core.database import get_db

def main():
    """Reload all data from CSV files."""
    print("🎵 MUSIC DATA RELOADER")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize data loader
        loader = DataLoader()
        
        print("📊 Reloading data from CSV files...")
        print("⚠️  This will replace existing data!")
        
        # Confirm with user
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Operation cancelled.")
            return
        
        # Force reload all data
        stats = loader.load_sample_data(force_reload=True)
        
        print("\n✅ Data reload completed!")
        print(f"📈 Results:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
            
        print("\n💡 Next steps:")
        print("   1. Restart your API server")
        print("   2. Refresh your frontend")
        print("   3. Test the new recommendations!")
        
    except Exception as e:
        print(f"❌ Error reloading data: {e}")
        return 1
    
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
