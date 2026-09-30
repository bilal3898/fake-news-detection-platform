# train_improved_production_model.py - Enhanced production model
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

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import VotingClassifier
import re
from sklearn.model_selection import GridSearchCV

def advanced_text_preprocessing(text):
    """Enhanced text preprocessing"""
    if pd.isna(text):
        return ""
    
    text = str(text).lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Keep more meaningful characters
    text = re.sub(r'[^\w\s\.\,\!\?\-\(\)\[\]\:\;\'\"]', '', text)
    
    return text.strip()

def load_and_balance_data():
    """Load and balance the training data"""
    try:
        # Load training data
        train_df = pd.read_csv('dataset/processed/train.csv')
        test_df = pd.read_csv('dataset/processed/test.csv')
        
        # Combine for training
        df = pd.concat([train_df, test_df], ignore_index=True)
        
        # Clean data
        df = df.dropna(subset=['text', 'label'])
        df = df[df['text'].str.len() > 50]
        
        print(f"Loaded {len(df)} samples")
        print(f"Original label distribution: {df['label'].value_counts().to_dict()}")
        
        # Balance the dataset
        fake_samples = df[df['label'] == 'FAKE']
        real_samples = df[df['label'] == 'REAL']
        
        # Sample to balance
        min_samples = min(len(fake_samples), len(real_samples))
        fake_balanced = fake_samples.sample(n=min_samples, random_state=42)
        real_balanced = real_samples.sample(n=min_samples, random_state=42)
        
        df_balanced = pd.concat([fake_balanced, real_balanced], ignore_index=True)
        df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
        
        print(f"Balanced dataset: {len(df_balanced)} samples")
        print(f"Balanced label distribution: {df_balanced['label'].value_counts().to_dict()}")
        
        return df_balanced
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def train_improved_production_model():
    """Train an improved production model"""
    print("🚀 Loading and balancing training data...")
    
    # Load data
    df = load_and_balance_data()
    if df is None:
        return None
    
    # Preprocess text
    print("🧹 Preprocessing text...")
    df['processed_text'] = df['text'].apply(advanced_text_preprocessing)
    
    # Remove very short texts after preprocessing
    df = df[df['processed_text'].str.len() > 20]
    
    print(f"After preprocessing: {len(df)} samples")
    
    # Split data
    X = df['processed_text']
    y = df['label']
    
    # Convert labels to numeric
    y_numeric = y.map({'FAKE': 1, 'REAL': 0})
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_numeric, test_size=0.2, random_state=42, stratify=y_numeric
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Create enhanced TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=15000,  # Increased features
        ngram_range=(1, 3),    # Include trigrams
        min_df=3,
        max_df=0.7,
        stop_words='english',
        sublinear_tf=True,
        analyzer='word',
        lowercase=True
    )
    
    # Create individual models with optimized parameters
    rf_clf = RandomForestClassifier(
        n_estimators=500,
        max_depth=25,
        min_samples_split=3,
        min_samples_leaf=1,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    lr_clf = LogisticRegression(
        random_state=42,
        max_iter=2000,
        class_weight='balanced',
        C=2.0,
        solver='liblinear'
    )
    
    gb_clf = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=6,
        random_state=42,
        subsample=0.8,
        max_features='sqrt'
    )
    
    nb_clf = MultinomialNB(alpha=0.05)
    
    # Create weighted ensemble model
    ensemble_clf = VotingClassifier(
        estimators=[
            ('rf', rf_clf),
            ('lr', lr_clf),
            ('gb', gb_clf),
            ('nb', nb_clf)
        ],
        voting='soft',
        weights=[3, 2, 2, 1]  # Give more weight to RF and LR
    )
    
    # Create pipeline
    pipeline = Pipeline([
        ('vectorizer', vectorizer),
        ('classifier', ensemble_clf)
    ])
    
    print("🤖 Training improved production model...")
    pipeline.fit(X_train, y_train)
    
    # Cross-validation
    print("📊 Cross-validation...")
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
    print(f"CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    # Evaluate on test set
    print("📊 Evaluating model...")
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"✅ Model trained successfully!")
    print(f"📈 Test Accuracy: {accuracy:.4f}")
    print(f"📈 Classification Report:")
    
    # Convert back to string labels for report
    y_test_str = y_test.map({0: 'REAL', 1: 'FAKE'})
    y_pred_str = pd.Series(y_pred).map({0: 'REAL', 1: 'FAKE'})
    
    print(classification_report(y_test_str, y_pred_str))
    
    # Save model
    models_dir = Path("ml_core/models")
    models_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = models_dir / f"model_production_improved_{timestamp}"
    model_dir.mkdir(exist_ok=True)
    
    # Save pipeline
    joblib.dump(pipeline, model_dir / "model.pkl")
    
    # Save metadata
    metadata = {
        'model_type': 'ensemble_voting_improved',
        'training_date': timestamp,
        'version': f'model_production_improved_{timestamp}',
        'dataset': 'production_balanced_40k_samples',
        'features': 'TF-IDF (trigrams, enhanced)',
        'algorithm': 'VotingClassifier(RF+LR+GB+NB)',
        'dataset_size': len(df),
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'label_distribution': df['label'].value_counts().to_dict(),
        'accuracy': accuracy,
        'cv_accuracy_mean': cv_scores.mean(),
        'cv_accuracy_std': cv_scores.std(),
        'parameters': {
            'max_features': 15000,
            'ngram_range': '(1, 3)',
            'ensemble_models': ['RandomForest', 'LogisticRegression', 'GradientBoosting', 'MultinomialNB'],
            'voting_weights': [3, 2, 2, 1]
        }
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save evaluation results
    evaluation = {
        'accuracy': accuracy,
        'cv_accuracy_mean': cv_scores.mean(),
        'cv_accuracy_std': cv_scores.std(),
        'classification_report': classification_report(y_test_str, y_pred_str, output_dict=True),
        'confusion_matrix': confusion_matrix(y_test_str, y_pred_str).tolist()
    }
    
    with open(model_dir / "evaluation.json", 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    print(f"✅ Model saved to: {model_dir}")
    
    # Test with sample predictions
    print("\n🧪 Testing model with sample predictions:")
    
    test_samples = [
        "Scientists confirm that drinking cola three times a day can cure cancer completely within a week.",
        "The Indian Space Research Organisation successfully launched a satellite to improve weather forecasting.",
        "A new smartphone app can charge your phone battery to 100% without using electricity.",
        "Medical researchers are conducting clinical trials to develop better treatments for chronic diseases.",
        "Time travel has been successfully tested, but results are being hidden from the public.",
        "Artificial intelligence is being used to automate customer support through chatbots."
    ]
    
    for i, sample in enumerate(test_samples, 1):
        processed_sample = advanced_text_preprocessing(sample)
        prediction = pipeline.predict([processed_sample])[0]
        confidence = np.max(pipeline.predict_proba([processed_sample])[0])
        predicted_label = "FAKE" if prediction == 1 else "REAL"
        print(f"Test {i}: {predicted_label} (confidence: {confidence:.3f})")
        print(f"   Text: {sample[:80]}...")
    
    return model_dir

if __name__ == "__main__":
    train_improved_production_model()
