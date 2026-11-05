"""
Content-based recommendation system using song metadata and audio features.
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Optional
import logging
import joblib
import os

from backend.app.core.database import SessionLocal
from backend.app.models.database import Song

logger = logging.getLogger(__name__)


class ContentBasedRecommender:
    """Content-based recommender using song features and metadata."""
    
    def __init__(self):
        self.db = None
        self.tfidf_vectorizer = None
        self.audio_scaler = None
        self.song_features_matrix = None
        self.songs_df = None
        self.is_trained = False
    
    def load_songs_data(self) -> pd.DataFrame:
        """Load songs data from database."""
        logger.info("Loading songs data for content-based filtering...")
        db = SessionLocal()
        try:
            songs = db.query(Song).all()
            
            if not songs:
                logger.warning("No songs found in database")
                return pd.DataFrame()
            
            # Convert to DataFrame
            songs_data = []
            for song in songs:
                songs_data.append({
                    'id': song.id,
                    'track_name': song.track_name,
                    'artist': song.artist,
                    'genre': song.genre or '',
                    'spotify_id': song.spotify_id,
                    'popularity_score': song.popularity_score or 0.0,
                    'danceability': song.danceability or 0.5,
                    'energy': song.energy or 0.5,
                    'valence': song.valence or 0.5,
                    'tempo': song.tempo or 120.0,
                    'acousticness': song.acousticness or 0.5,
                    'instrumentalness': song.instrumentalness or 0.5,
                    'liveness': song.liveness or 0.5,
                    'speechiness': song.speechiness or 0.5
                })
            
            df = pd.DataFrame(songs_data)
            logger.info(f"Loaded {len(df)} songs for content-based filtering")
            return df
        finally:
            db.close()
    
    def create_text_features(self, df: pd.DataFrame) -> np.ndarray:
        """Create TF-IDF features from text metadata."""
        logger.info("Creating text features using TF-IDF...")
        
        # Combine text features
        text_features = df.apply(
            lambda row: f"{row['artist']} {row['genre']}", axis=1
        ).fillna('')
        
        # Create TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        
        # Fit and transform text features
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_features)
        
        logger.info(f"Created TF-IDF matrix with shape {tfidf_matrix.shape}")
        return tfidf_matrix.toarray()
    
    def create_audio_features(self, df: pd.DataFrame) -> np.ndarray:
        """Create normalized audio features."""
        logger.info("Creating audio features...")
        
        # Select audio features
        audio_features = [
            'danceability', 'energy', 'valence', 'tempo',
            'acousticness', 'instrumentalness', 'liveness', 'speechiness'
        ]
        
        # Extract audio feature matrix
        audio_matrix = df[audio_features].values
        
        # Normalize audio features
        self.audio_scaler = StandardScaler()
        audio_matrix_scaled = self.audio_scaler.fit_transform(audio_matrix)
        
        logger.info(f"Created audio features matrix with shape {audio_matrix_scaled.shape}")
        return audio_matrix_scaled
    
    def combine_features(self, text_features: np.ndarray, audio_features: np.ndarray) -> np.ndarray:
        """Combine text and audio features."""
        logger.info("Combining text and audio features...")
        
        # Weight the features (you can adjust these weights)
        text_weight = 0.3
        audio_weight = 0.7
        
        # Normalize text features to same scale as audio features
        text_features_normalized = StandardScaler().fit_transform(text_features)
        
        # Combine features
        combined_features = np.hstack([
            text_features_normalized * text_weight,
            audio_features * audio_weight
        ])
        
        logger.info(f"Combined features matrix shape: {combined_features.shape}")
        return combined_features
    
    def train(self) -> bool:
        """Train the content-based recommender."""
        logger.info("Training content-based recommender...")
        
        try:
            # Load songs data
            self.songs_df = self.load_songs_data()
            
            if self.songs_df.empty:
                logger.error("No songs data available for training")
                return False
            
            # Create text features
            text_features = self.create_text_features(self.songs_df)
            
            # Create audio features
            audio_features = self.create_audio_features(self.songs_df)
            
            # Combine features
            self.song_features_matrix = self.combine_features(text_features, audio_features)
            
            self.is_trained = True
            logger.info("✅ Content-based recommender training completed")
            return True
            
        except Exception as e:
            logger.error(f"Error training content-based recommender: {e}")
            return False
    
    def find_similar_songs(
        self, 
        song_indices: List[int], 
        top_k: int = 10,
        exclude_indices: List[int] = None
    ) -> List[Tuple[int, float]]:
        """Find songs similar to the given song indices."""
        if not self.is_trained:
            logger.warning("Recommender not trained. Training now...")
            if not self.train():
                return []
        
        exclude_indices = exclude_indices or []
        
        # Get features for input songs
        input_features = self.song_features_matrix[song_indices]
        
        # Calculate average feature vector if multiple songs
        if len(input_features) > 1:
            avg_features = np.mean(input_features, axis=0).reshape(1, -1)
        else:
            avg_features = input_features
        
        # Calculate cosine similarity with all songs
        similarities = cosine_similarity(avg_features, self.song_features_matrix)[0]
        
        # Get song indices sorted by similarity
        similar_indices = np.argsort(similarities)[::-1]
        
        # Filter out input songs and excluded songs with artist-level blending
        filtered_indices = []
        seed_indices_set = set(song_indices)
        exclude_set = set(exclude_indices)
        seed_allowed_count = 2 if len(song_indices) > 2 else 0
        seed_included = 0

        for idx in similar_indices:
            if idx in exclude_set:
                continue
            if idx in seed_indices_set:
                if seed_included < seed_allowed_count:
                    seed_included += 1
                    filtered_indices.append((idx, similarities[idx]))
                    if len(filtered_indices) >= top_k:
                        break
                continue

            filtered_indices.append((idx, similarities[idx]))
            if len(filtered_indices) >= top_k:
                break

        return filtered_indices
    
    def get_recommendations_by_song_names(
        self,
        song_names: List[str],
        top_k: int = 10,
        exclude_song_names: List[str] = None
    ) -> List[Dict]:
        """Get recommendations based on song names."""
        if not self.is_trained:
            if not self.train():
                return []
        
        exclude_song_names = exclude_song_names or []
        
        # Find song indices for input songs
        song_indices = []
        for song_name in song_names:
            # Try to match by track name or artist
            matches = self.songs_df[
                (self.songs_df['track_name'].str.contains(song_name, case=False, na=False)) |
                (self.songs_df['artist'].str.contains(song_name, case=False, na=False))
            ]
            
            if not matches.empty:
                song_indices.extend(matches.index.tolist())
        
        if not song_indices:
            logger.warning(f"No matching songs found for: {song_names}")
            return []
        
        # Find exclude indices
        exclude_indices = []
        for exclude_name in exclude_song_names:
            matches = self.songs_df[
                (self.songs_df['track_name'].str.contains(exclude_name, case=False, na=False)) |
                (self.songs_df['artist'].str.contains(exclude_name, case=False, na=False))
            ]
            if not matches.empty:
                exclude_indices.extend(matches.index.tolist())
        
        # Get similar songs
        similar_songs = self.find_similar_songs(song_indices, top_k, exclude_indices)
        
        # Convert to recommendation format
        recommendations = []
        for idx, similarity_score in similar_songs:
            song_row = self.songs_df.iloc[idx]
            recommendations.append({
                'track_name': song_row['track_name'],
                'artist': song_row['artist'],
                'score': float(similarity_score),
                'reason': 'content_based',
                'genre': song_row['genre'],
                'spotify_id': song_row['spotify_id']
            })
        
        return recommendations
    
    def get_recommendations_by_genre(
        self,
        genres: List[str],
        top_k: int = 10,
        exclude_song_names: List[str] = None
    ) -> List[Dict]:
        """Get recommendations based on genres."""
        if not self.is_trained:
            if not self.train():
                return []
        
        exclude_song_names = exclude_song_names or []
        
        # Filter songs by genre (case-insensitive)
        genres_lower = [g.lower() for g in genres]
        genre_songs = self.songs_df[
            self.songs_df['genre'].fillna('').astype(str).str.lower().isin(genres_lower)
        ].copy()
        
        if genre_songs.empty:
            logger.warning(f"No songs found for genres: {genres}")
            return []
        
        # Sort by popularity and audio features that match the genre
        if 'amapiano' in [g.lower() for g in genres]:
            # For amapiano, prefer high danceability and energy
            genre_songs['genre_score'] = (
                genre_songs['danceability'] * 0.4 +
                genre_songs['energy'] * 0.3 +
                genre_songs['valence'] * 0.2 +
                genre_songs['popularity_score'] * 0.1
            )
        elif 'afrobeats' in [g.lower() for g in genres]:
            # For afrobeats, prefer rhythm and energy
            genre_songs['genre_score'] = (
                genre_songs['danceability'] * 0.3 +
                genre_songs['energy'] * 0.3 +
                genre_songs['valence'] * 0.2 +
                genre_songs['popularity_score'] * 0.2
            )
        else:
            # Default scoring
            genre_songs['genre_score'] = genre_songs['popularity_score']
        
        # Sort by genre score
        genre_songs = genre_songs.sort_values('genre_score', ascending=False)
        
        # Filter out excluded songs
        if exclude_song_names:
            for exclude_name in exclude_song_names:
                genre_songs = genre_songs[
                    ~(genre_songs['track_name'].str.contains(exclude_name, case=False, na=False)) &
                    ~(genre_songs['artist'].str.contains(exclude_name, case=False, na=False))
                ]
        
        # Convert to recommendations
        recommendations = []
        for _, song_row in genre_songs.head(top_k).iterrows():
            recommendations.append({
                'track_name': song_row['track_name'],
                'artist': song_row['artist'],
                'score': float(song_row['genre_score']),
                'reason': 'content_based',
                'genre': song_row['genre'],
                'spotify_id': song_row['spotify_id']
            })
        
        return recommendations
    
    def save_model(self, model_path: str):
        """Save the trained model."""
        if not self.is_trained:
            logger.error("Cannot save untrained model")
            return False
        
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            model_data = {
                'tfidf_vectorizer': self.tfidf_vectorizer,
                'audio_scaler': self.audio_scaler,
                'song_features_matrix': self.song_features_matrix,
                'songs_df': self.songs_df
            }
            
            joblib.dump(model_data, model_path)
            logger.info(f"Model saved to {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_path: str):
        """Load a trained model."""
        try:
            model_data = joblib.load(model_path)
            
            self.tfidf_vectorizer = model_data['tfidf_vectorizer']
            self.audio_scaler = model_data['audio_scaler']
            self.song_features_matrix = model_data['song_features_matrix']
            self.songs_df = model_data['songs_df']
            self.is_trained = True
            
            logger.info(f"Model loaded from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'db') and self.db:
            try:
                self.db.close()
            except Exception:
                pass


_CONTENT_RECOMMENDER_INSTANCE = None

def get_content_recommender(model_dir: str = None) -> ContentBasedRecommender:
    """Get or initialize singleton instance of ContentBasedRecommender."""
    global _CONTENT_RECOMMENDER_INSTANCE
    if _CONTENT_RECOMMENDER_INSTANCE is not None and _CONTENT_RECOMMENDER_INSTANCE.is_trained:
        return _CONTENT_RECOMMENDER_INSTANCE

    if model_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_dir = os.path.join(project_root, "models")

    instance = ContentBasedRecommender()
    model_path = os.path.join(model_dir, "content_based_model.joblib")
    if os.path.exists(model_path):
        if instance.load_model(model_path):
            _CONTENT_RECOMMENDER_INSTANCE = instance
            return instance

    # Otherwise train and save
    if instance.train():
        try:
            os.makedirs(model_dir, exist_ok=True)
            instance.save_model(model_path)
        except Exception as e:
            logger.warning(f"Could not persist content-based model: {e}")
        _CONTENT_RECOMMENDER_INSTANCE = instance
        return instance

    _CONTENT_RECOMMENDER_INSTANCE = instance
    return instance


def main():
    """Main function for training content-based recommender."""
    logging.basicConfig(level=logging.INFO)
    
    recommender = ContentBasedRecommender()
    
    try:
        # Train the recommender
        if recommender.train():
            print("✅ Content-based recommender training completed!")
            
            # Test recommendations
            test_songs = ["Master KG", "Amapiano"]
            recommendations = recommender.get_recommendations_by_song_names(test_songs, top_k=5)
            
            print(f"\n🎵 Test recommendations for {test_songs}:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec['track_name']} - {rec['artist']} (Score: {rec['score']:.3f})")
            
            # Save model
            model_path = "models/content_based_model.joblib"
            recommender.save_model(model_path)
            
        else:
            print("❌ Content-based recommender training failed!")
    
    finally:
        recommender.close()


if __name__ == "__main__":
    main()
