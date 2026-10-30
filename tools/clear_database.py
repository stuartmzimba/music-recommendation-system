#!/usr/bin/env python3
"""
Clear Database Script
Removes all sample data from the music recommender database while keeping the structure.
"""

import sqlite3
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_all_data():
    """Clear all data from all tables while keeping the structure."""

    logger.info("🗑️ Starting database cleanup...")

    # Database file path
    db_path = "music_recommender.db"

    if not os.path.exists(db_path):
        logger.error(f"❌ Database file not found: {db_path}")
        return

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Clear data in dependency order (foreign keys first)
        logger.info("Clearing association rules...")
        cursor.execute("DELETE FROM association_rules")
        deleted_rules = cursor.rowcount
        logger.info(f"   Deleted {deleted_rules} association rules")

        logger.info("Clearing user listening history...")
        cursor.execute("DELETE FROM user_listening_history")
        deleted_history = cursor.rowcount
        logger.info(f"   Deleted {deleted_history} listening history records")

        logger.info("Clearing popular songs...")
        cursor.execute("DELETE FROM popular_songs")
        deleted_popular = cursor.rowcount
        logger.info(f"   Deleted {deleted_popular} popular song records")

        logger.info("Clearing songs...")
        cursor.execute("DELETE FROM songs")
        deleted_songs = cursor.rowcount
        logger.info(f"   Deleted {deleted_songs} songs")

        # Reset auto-increment counters (if table exists)
        logger.info("Resetting auto-increment counters...")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('songs', 'user_listening_history', 'popular_songs', 'association_rules')")
        except sqlite3.OperationalError:
            logger.info("   sqlite_sequence table not found (normal for empty database)")

        # Commit all changes
        conn.commit()

        logger.info("✅ Database cleanup completed successfully!")

        # Verify cleanup
        cursor.execute("SELECT COUNT(*) FROM songs")
        songs_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM user_listening_history")
        history_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM popular_songs")
        popular_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM association_rules")
        rules_count = cursor.fetchone()[0]

        logger.info("📊 Final database state:")
        logger.info(f"   Songs: {songs_count}")
        logger.info(f"   Listening history: {history_count}")
        logger.info(f"   Popular songs: {popular_count}")
        logger.info(f"   Association rules: {rules_count}")

        if songs_count == 0 and history_count == 0 and popular_count == 0 and rules_count == 0:
            logger.info("🎉 Database is now completely empty!")
        else:
            logger.warning("⚠️ Some data may still remain in the database")

    except Exception as e:
        logger.error(f"❌ Error during database cleanup: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function."""
    print("🎵 MUSIC RECOMMENDER DATABASE CLEANUP")
    print("=" * 50)
    print("This will remove ALL data from the database.")
    print("The database structure will remain intact.")
    print("=" * 50)
    
    # Confirm action
    response = input("Are you sure you want to clear all data? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        clear_all_data()
        print("\n💡 Next steps:")
        print("   1. Restart your API server if it's running")
        print("   2. Load new data using reload_data.py or spotify fetchers")
        print("   3. Or start fresh with empty database")
    else:
        print("❌ Database cleanup cancelled.")

if __name__ == "__main__":
    main()
