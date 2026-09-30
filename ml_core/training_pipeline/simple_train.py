# ml_core/training_pipeline/simple_train.py
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import re

def clean_text(text):
    """Simple text cleaning"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("Loading datasets...")
    
    # Load datasets
    base_path = Path("dataset/raw")
    fake_df = pd.read_csv(base_path / "kaggle_fake.csv")
    true_df = pd.read_csv(base_path / "kaggle_true.csv")
    
    # Add labels
    fake_df['label'] = 1  # Fake news
    true_df['label'] = 0  # True news
    
    # Combine
    df = pd.concat([fake_df, true_df], ignore_index=True)
    print(f"Total samples: {len(df)}")
    print(f"Fake: {len(fake_df)}, True: {len(true_df)}")
    
    # Clean text
    print("Cleaning text...")
    df['cleaned_text'] = df['text'].apply(clean_text)
    df = df[df['cleaned_text'].str.len() > 0]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['cleaned_text'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
    )
    
    # Vectorize
    print("Vectorizing text...")
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # Train model
    print("Training model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_vec, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")
    
    # Save model
    Path("ml_core/models").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, "ml_core/models/model.pkl")
    joblib.dump(vectorizer, "ml_core/models/vectorizer.pkl")
    print("Model saved to ml_core/models/")
    
    return accuracy

if __name__ == "__main__":
    main()