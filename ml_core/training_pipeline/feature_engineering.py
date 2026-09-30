import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_selection import SelectKBest, chi2, mutual_info_classif
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import joblib
from pathlib import Path


logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        self.vectorizers = {}
        self.scalers = {}
        self.feature_selector = None
    
    def create_text_features(self, texts: List[str], 
                           method: str = 'tfidf',
                           max_features: int = 5000,
                           ngram_range: Tuple[int, int] = (1, 2),
                           use_lda: bool = False,
                           n_topics: int = 10) -> Tuple[np.ndarray, Any]:
        """
        Create text features using various methods
        """
        if method == 'tfidf':
            vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                stop_words='english',
                min_df=2,
                max_df=0.8
            )
        elif method == 'count':
            vectorizer = CountVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                stop_words='english',
                min_df=2,
                max_df=0.8
            )
        else:
            raise ValueError("Method must be 'tfidf' or 'count'")
        
        # Fit and transform
        X_text = vectorizer.fit_transform(texts)
        
        # Apply LDA for topic modeling if requested
        if use_lda:
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                learning_method='online'
            )
            X_topics = lda.fit_transform(X_text)
            self.vectorizers['lda'] = lda
            return X_topics, vectorizer
        
        self.vectorizers[method] = vectorizer
        return X_text, vectorizer
    
    def create_linguistic_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Create features from linguistic characteristics
        """
        linguistic_features = [
            'word_count', 'sentence_count', 'char_count',
            'avg_sentence_length', 'avg_word_length',
            'unique_word_ratio', 'stopword_ratio',
            'exclamation_count', 'question_count',
            'uppercase_ratio', 'digit_ratio',
            'sentiment_positive', 'sentiment_negative',
            'sentiment_neutral', 'sentiment_compound'
        ]
        
        # Select available features
        available_features = [f for f in linguistic_features if f in df.columns]
        X_linguistic = df[available_features].values
        
        # Scale features
        scaler = StandardScaler()
        X_linguistic_scaled = scaler.fit_transform(X_linguistic)
        self.scalers['linguistic'] = scaler
        
        return X_linguistic_scaled
    
    def create_metadata_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Create features from metadata
        """
        metadata_features = []
        
        # Source features (if available)
        if 'source' in df.columns:
            source_dummies = pd.get_dummies(df['source'], prefix='source', drop_first=True)
            metadata_features.append(source_dummies)
        
        # Author features (if available)
        if 'author' in df.columns:
            # Group rare authors
            author_counts = df['author'].value_counts()
            common_authors = author_counts[author_counts > 5].index
            df_author = df['author'].apply(lambda x: x if x in common_authors else 'other')
            author_dummies = pd.get_dummies(df_author, prefix='author', drop_first=True)
            metadata_features.append(author_dummies)
        
        if metadata_features:
            X_metadata = pd.concat(metadata_features, axis=1).values
            return X_metadata
        else:
            return np.empty((len(df), 0))
    
    def select_features(self, X: np.ndarray, y: np.ndarray, 
                       method: str = 'chi2', k: int = 1000) -> np.ndarray:
        """
        Select most important features
        """
        if method == 'chi2':
            selector = SelectKBest(chi2, k=k)
        elif method == 'mutual_info':
            selector = SelectKBest(mutual_info_classif, k=k)
        else:
            raise ValueError("Method must be 'chi2' or 'mutual_info'")
        
        X_selected = selector.fit_transform(X, y)
        self.feature_selector = selector
        
        logger.info(f"Selected {X_selected.shape[1]} features using {method}")
        return X_selected
    
    def create_feature_pipeline(self, df: pd.DataFrame, texts: List[str], 
                              labels: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Create complete feature pipeline
        """
        # Text features
        X_text, text_vectorizer = self.create_text_features(
            texts, method='tfidf', max_features=3000, use_lda=False
        )
        
        # Linguistic features
        X_linguistic = self.create_linguistic_features(df)
        
        # Metadata features
        X_metadata = self.create_metadata_features(df)
        
        # Combine all features
        if X_metadata.shape[1] > 0:
            X_combined = np.hstack([X_text.toarray(), X_linguistic, X_metadata])
        else:
            X_combined = np.hstack([X_text.toarray(), X_linguistic])
        
        # Feature selection
        X_final = self.select_features(X_combined, labels, k=min(2000, X_combined.shape[1]))
        
        feature_info = {
            'text_features': X_text.shape[1],
            'linguistic_features': X_linguistic.shape[1],
            'metadata_features': X_metadata.shape[1],
            'total_features': X_final.shape[1],
            'vectorizer': text_vectorizer,
            'selected_features_mask': self.feature_selector.get_support()
        }
        
        return X_final, feature_info
    
    def save_feature_artifacts(self, output_dir: str):
        """
        Save feature engineering artifacts
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save vectorizers
        for name, vectorizer in self.vectorizers.items():
            joblib.dump(vectorizer, output_path / f"{name}_vectorizer.pkl")
        
        # Save scalers
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, output_path / f"{name}_scaler.pkl")
        
        # Save feature selector
        if self.feature_selector:
            joblib.dump(self.feature_selector, output_path / "feature_selector.pkl")
        
        logger.info(f"Saved feature artifacts to: {output_path}")
# Global instance
feature_engineer = FeatureEngineer()

def extract_features(df, text_column="cleaned_text", fit=True):
    """
    Wrapper to extract features from dataset.
    """
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in dataframe")

    texts = df[text_column].astype(str).tolist()
    
    if fit:
        X = feature_engineer.fit_transform(texts)
    else:
        X = feature_engineer.transform(texts)

    return X

# Singleton instance
feature_engineer = FeatureEngineer()