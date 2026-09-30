# train_production_model.py - Production-ready fake news detection model
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
from datetime import datetime
import joblib
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import VotingClassifier
import re

def load_production_data():
    """Load the actual training data"""
    try:
        # Load training data
        train_df = pd.read_csv('dataset/processed/train.csv')
        test_df = pd.read_csv('dataset/processed/test.csv')
        
        # Combine for training
        df = pd.concat([train_df, test_df], ignore_index=True)
        
        # Clean data
        df = df.dropna(subset=['text', 'label'])
        df = df[df['text'].str.len() > 50]  # Remove very short texts
        
        print(f"Loaded {len(df)} samples")
        print(f"Label distribution: {df['label'].value_counts().to_dict()}")
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def advanced_text_preprocessing(text):
    """Advanced text preprocessing"""
    if pd.isna(text):
        return ""
    
    text = str(text).lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep important ones
    text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', '', text)
    
    return text.strip()

def train_production_model():
    """Train a production-ready model using actual data"""
    print("🚀 Loading production training data...")
    
    # Load data
    df = load_production_data()
    if df is None:
        return None
    
    # Preprocess text
    print("🧹 Preprocessing text...")
    df['processed_text'] = df['text'].apply(advanced_text_preprocessing)
    
    # Remove very short texts after preprocessing
    df = df[df['processed_text'].str.len() > 20]
    
    print(f"After preprocessing: {len(df)} samples")
    print(f"Final label distribution: {df['label'].value_counts().to_dict()}")
    
    # Split data
    X = df['processed_text']
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Create advanced TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=10000,  # Increased features
        ngram_range=(1, 3),    # Include trigrams
        min_df=2,
        max_df=0.8,
        stop_words='english',
        sublinear_tf=True
    )
    
    # Create multiple models for ensemble
    rf_clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    lr_clf = LogisticRegression(
        random_state=42,
        max_iter=1000,
        class_weight='balanced',
        C=1.0
    )
    
    nb_clf = MultinomialNB(alpha=0.1)
    
    # Create ensemble model
    ensemble_clf = VotingClassifier(
        estimators=[
            ('rf', rf_clf),
            ('lr', lr_clf),
            ('nb', nb_clf)
        ],
        voting='soft',
        weights=[2, 2, 1]  # Give more weight to RF and LR
    )
    
    # Create pipeline
    pipeline = Pipeline([
        ('vectorizer', vectorizer),
        ('classifier', ensemble_clf)
    ])
    
    print("🤖 Training production model...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    print("📊 Evaluating model...")
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"✅ Model trained successfully!")
    print(f"📈 Accuracy: {accuracy:.4f}")
    print(f"📈 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model
    models_dir = Path("ml_core/models")
    models_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = models_dir / f"model_production_{timestamp}"
    model_dir.mkdir(exist_ok=True)
    
    # Save pipeline
    joblib.dump(pipeline, model_dir / "model.pkl")
    
    # Save metadata
    metadata = {
        'model_type': 'ensemble_voting',
        'training_date': timestamp,
        'version': f'model_production_{timestamp}',
        'dataset': 'production_46k_samples',
        'features': 'TF-IDF (trigrams)',
        'algorithm': 'VotingClassifier(RF+LR+NB)',
        'dataset_size': len(df),
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'label_distribution': df['label'].value_counts().to_dict(),
        'accuracy': accuracy,
        'parameters': {
            'max_features': 10000,
            'ngram_range': '(1, 3)',
            'ensemble_models': ['RandomForest', 'LogisticRegression', 'MultinomialNB'],
            'voting_weights': [2, 2, 1]
        }
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save evaluation results
    evaluation = {
        'accuracy': accuracy,
        'classification_report': classification_report(y_test, y_pred, output_dict=True),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
    }
    
    with open(model_dir / "evaluation.json", 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    print(f"✅ Model saved to: {model_dir}")
    
    # Test with some sample predictions
    print("\n🧪 Testing model with sample predictions:")
    
    test_samples = [
        "Scientists confirm that drinking cola three times a day can cure cancer completely within a week.",
        "The Indian Space Research Organisation successfully launched a satellite to improve weather forecasting.",
        "A new smartphone app can charge your phone battery to 100% without using electricity.",
        "Medical researchers are conducting clinical trials to develop better treatments for chronic diseases."
    ]
    
    for i, sample in enumerate(test_samples, 1):
        processed_sample = advanced_text_preprocessing(sample)
        prediction = pipeline.predict([processed_sample])[0]
        confidence = np.max(pipeline.predict_proba([processed_sample])[0])
        print(f"Test {i}: {prediction} (confidence: {confidence:.3f})")
        print(f"   Text: {sample[:80]}...")
    
    return model_dir

if __name__ == "__main__":
    train_production_model()
