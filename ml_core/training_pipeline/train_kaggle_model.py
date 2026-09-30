# train_kaggle_direct.py
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json
from datetime import datetime

def load_kaggle_dataset_direct():
    """Direct Kaggle dataset loading"""
    dataset_path = Path("dataset/raw")
    
    try:
        # Load fake news
        fake_df = pd.read_csv(dataset_path / "kaggle_fake.csv")
        print(f"Loaded fake news: {len(fake_df)} samples")
        
        # Load true news  
        true_df = pd.read_csv(dataset_path / "kaggle_true.csv")
        print(f"Loaded true news: {len(true_df)} samples")
        
        # Add labels
        fake_df['label'] = 1  # Fake news
        true_df['label'] = 0  # Real news
        
        # Combine datasets
        combined_df = pd.concat([fake_df, true_df], ignore_index=True)
        
        # Use text column (fallback to title if text not available)
        if 'text' in combined_df.columns:
            combined_df = combined_df[['text', 'label']]
        elif 'title' in combined_df.columns:
            combined_df = combined_df.rename(columns={'title': 'text'})
            combined_df = combined_df[['text', 'label']]
        else:
            # Use first column that contains text
            text_columns = [col for col in combined_df.columns if combined_df[col].dtype == 'object']
            if text_columns:
                combined_df = combined_df.rename(columns={text_columns[0]: 'text'})
                combined_df = combined_df[['text', 'label']]
            else:
                raise ValueError("No text columns found in Kaggle dataset")
        
        print(f"Final dataset: {len(combined_df)} samples")
        print(f"Label distribution: {combined_df['label'].value_counts().to_dict()}")
        
        return combined_df
        
    except Exception as e:
        print(f"Error loading Kaggle dataset: {e}")
        return None

def clean_text(text):
    """Simple text cleaning"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())  # Remove extra whitespace
    return text

def train_kaggle_model():
    """Train Kaggle model directly"""
    print("🚀 Loading Kaggle dataset...")
    
    # Load data
    df = load_kaggle_dataset_direct()
    if df is None:
        print("❌ Failed to load Kaggle dataset")
        return
    
    # Clean text
    print("🧹 Cleaning text...")
    df['cleaned_text'] = df['text'].apply(clean_text)
    df = df[df['cleaned_text'].str.len() > 50]  # Remove very short texts
    
    print(f"After cleaning: {len(df)} samples")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['cleaned_text'], df['label'], 
        test_size=0.2, random_state=42, stratify=df['label']
    )
    
    # Vectorize text
    print("🔡 Vectorizing text...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words='english',
        min_df=5,
        max_df=0.7
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    print(f"Feature matrix shape: {X_train_vec.shape}")
    
    # Train model
    print("🤖 Training model...")
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train_vec, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"✅ Model trained successfully!")
    print(f"📊 Accuracy: {accuracy:.4f}")
    print(f"📈 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model
    models_dir = Path("ml_core/models")
    models_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = models_dir / f"model_kaggle_{timestamp}"
    model_dir.mkdir(exist_ok=True)
    
    joblib.dump(model, model_dir / "model.pkl")
    joblib.dump(vectorizer, model_dir / "vectorizer.pkl")
    
    # Save metadata
    metadata = {
        'model_type': 'random_forest',
        'dataset': 'kaggle',
        'accuracy': accuracy,
        'training_date': timestamp,
        'dataset_size': len(df)
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Model saved to: {model_dir}")

if __name__ == "__main__":
    train_kaggle_model()