# ml_core/training_pipeline/train_model.py
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import joblib
import json
from datetime import datetime
import sys
import os
import re
import argparse

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

# Import the new data loader
from ml_core.training_pipeline.data_loader import DatasetLoader

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleModelTrainer:
    ...
    def __init__(self):
        # Create models directory if it doesn't exist
        self.models_dir = Path("ml_core/models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.data_loader = DatasetLoader()

    def load_dataset(self, dataset_type: str):
        """Load specific dataset for training"""
        try:
            logger.info(f"Loading {dataset_type.upper()} dataset...")
            
            if dataset_type.lower() == 'liar':
                return self._load_liar_dataset()
            elif dataset_type.lower() == 'kaggle':
                return self._load_kaggle_dataset()
            elif dataset_type.lower() == 'combined':
                return self._load_combined_dataset()
            elif dataset_type.lower() == 'processed_cleaned':
                return self._load_processed_cleaned_dataset()
            else:
                raise ValueError(f"Unknown dataset type: {dataset_type}")
                
        except Exception as e:
            logger.error(f"Error loading {dataset_type} dataset: {e}")
            return None

    def _load_liar_dataset(self):
        """Load LIAR dataset for training"""
        try:
            train_data = self.data_loader.load_liar_dataset('train')
            test_data = self.data_loader.load_liar_dataset('test')
            valid_data = self.data_loader.load_liar_dataset('valid')

            # Combine available splits
            splits = [d for d in (train_data, test_data, valid_data) if d is not None]
            if not splits:
                raise ValueError("No LIAR splits could be loaded")

            combined_data = pd.concat(splits, ignore_index=True)

            # Normalize column names
            if 'statement' in combined_data.columns:
                combined_data = combined_data.rename(columns={'statement': 'text'})
            if 'binary_label' in combined_data.columns and 'label' not in combined_data.columns:
                combined_data = combined_data.rename(columns={'binary_label': 'label'})

            # Keep only necessary columns
            if 'text' in combined_data.columns and 'label' in combined_data.columns:
                combined_data = combined_data[['text', 'label']]
            else:
                raise ValueError(f"Expected columns 'text' and 'label' not present. Found: {combined_data.columns.tolist()}")

            logger.info(f"Loaded LIAR dataset: {len(combined_data)} statements")
            logger.info(f"Label distribution: {combined_data['label'].value_counts().to_dict()}")

            return combined_data

        except Exception as e:
            logger.error(f"Error loading LIAR dataset: {e}")
            return None

    def _load_kaggle_dataset(self):
        """Load Kaggle dataset for training"""
        try:
            # Load fake and true news
            fake_data = self.data_loader.load_kaggle_dataset('fake')
            true_data = self.data_loader.load_kaggle_dataset('true')

            if fake_data is None or true_data is None:
                raise ValueError("Could not load Kaggle dataset files")

            # Add labels
            fake_data['label'] = 1  # Fake news
            true_data['label'] = 0  # Real news

            # Combine and select relevant columns
            combined_data = pd.concat([fake_data, true_data], ignore_index=True)
            
            # Use 'text' column if available, otherwise use 'title'
            if 'text' in combined_data.columns:
                combined_data = combined_data[['text', 'label']]
            elif 'title' in combined_data.columns:
                combined_data = combined_data.rename(columns={'title': 'text'})
                combined_data = combined_data[['text', 'label']]
            else:
                raise ValueError("No suitable text column found in Kaggle dataset")

            logger.info(f"Loaded Kaggle dataset: {len(combined_data)} articles")
            logger.info(f"Label distribution: {combined_data['label'].value_counts().to_dict()}")

            return combined_data

        except Exception as e:
            logger.error(f"Error loading Kaggle dataset: {e}")
            return None

    def _load_combined_dataset(self):
        """Load combined LIAR + Kaggle dataset"""
        try:
            liar_data = self._load_liar_dataset()
            kaggle_data = self._load_kaggle_dataset()

            if liar_data is None and kaggle_data is None:
                raise ValueError("Could not load either LIAR or Kaggle datasets")

            combined_data = pd.concat([liar_data, kaggle_data], ignore_index=True) if kaggle_data is not None else liar_data

            logger.info(f"Loaded combined dataset: {len(combined_data)} total samples")
            logger.info(f"Label distribution: {combined_data['label'].value_counts().to_dict()}")

            return combined_data

        except Exception as e:
            logger.error(f"Error loading combined dataset: {e}")
            return None
    
    def _load_processed_cleaned_dataset(self):
        """Load the processed cleaned dataset"""
        try:
            # Use consistent path to processed cleaned data
            dataset_path = Path("dataset/processed/cleaned_news_data.csv")
            
            if not dataset_path.exists():
                logger.error(f"Processed cleaned dataset not found: {dataset_path}")
                return None
            
            logger.info(f"Loading processed cleaned dataset: {dataset_path}")
            df = pd.read_csv(dataset_path)
            
            # Standardize column names
            if 'text' in df.columns and 'statement' not in df.columns:
                df = df.rename(columns={'text': 'statement'})
            elif 'title' in df.columns and 'statement' not in df.columns:
                df = df.rename(columns={'title': 'statement'})
            
            # Ensure we have required columns
            if 'statement' not in df.columns:
                logger.error("Required 'statement' or 'text' column not found in processed dataset")
                return None
            
            if 'label' not in df.columns:
                logger.error("Required 'label' column not found in processed dataset")
                return None
            
            logger.info(f"Loaded processed cleaned dataset: {len(df)} samples")
            logger.info(f"Label distribution: {df['label'].value_counts().to_dict()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading processed cleaned dataset: {e}")
            return None

    def clean_text(self, text: str, dataset_type: str = 'general') -> str:
        """Text cleaning with dataset-specific optimizations - CONSISTENT WITH PREDICTION"""
        if pd.isna(text):
            return ""
            
        text = str(text).lower()
        
        # Dataset-specific cleaning - MUST MATCH backend/services/prediction.py
        if dataset_type == 'liar':
            # LIAR dataset: political statements, keep more structure
            text = re.sub(r"http\S+", "", text)
            text = re.sub(r"[^a-zA-Z0-9\s\.\,\!\?]", "", text)  # Keep basic punctuation
        else:
            # Kaggle dataset: news articles, more aggressive cleaning
            text = re.sub(r"http\S+", "", text)
            text = re.sub(r"[^a-zA-Z\s]", "", text)  # Remove all non-letters
        
        # Common cleaning
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def prepare_data(self, df: pd.DataFrame, dataset_type: str = 'general') -> pd.DataFrame:
        """Prepare data for training with dataset-specific processing"""
        logger.info(f"Cleaning text data for {dataset_type} dataset...")
        
        df = df.copy()
        df['cleaned_text'] = df['text'].apply(lambda x: self.clean_text(x, dataset_type))

        # Remove empty texts
        df = df[df['cleaned_text'].str.len() > 0]

        # Handle label conversion
        df = df[~df['label'].isna()].copy()
        
        try:
            # Try direct conversion to int
            df['label'] = df['label'].astype(int)
        except (ValueError, TypeError):
            # Map string labels to integers
            label_map = {
                # LIAR dataset labels
                'pants-fire': 1, 'false': 1, 'barely-true': 1,
                'true': 0, 'mostly-true': 0, 'half-true': 0,
                # Kaggle dataset labels
                'fake': 1, 'real': 0, 'TRUE': 0, 'FALSE': 1
            }
            df['label'] = df['label'].map(label_map)
            
            # Drop any remaining non-numeric labels
            df = df[~df['label'].isna()].copy()
            df['label'] = df['label'].astype(int)

        logger.info(f"Data preparation complete. Final dataset size: {len(df)}")
        return df

    def extract_features(self, train_texts, test_texts, dataset_type: str = 'general'):
        """Extract features with dataset-specific TF-IDF parameters"""
        logger.info(f"Extracting features for {dataset_type} dataset...")

        # Dataset-specific TF-IDF parameters
        if dataset_type == 'liar':
            # LIAR: Political statements - more nuanced features
            vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 3),  # Include trigrams for political context
                stop_words='english',
                min_df=3,
                max_df=0.8,
                sublinear_tf=True
            )
        else:
            # Kaggle/General: News articles - standard parameters
            vectorizer = TfidfVectorizer(
                max_features=3000,
                ngram_range=(1, 2),
                stop_words='english',
                min_df=5,
                max_df=0.7,
                sublinear_tf=True
            )

        X_train = vectorizer.fit_transform(train_texts)
        X_test = vectorizer.transform(test_texts)

        logger.info(f"Feature extraction complete. Shape: {X_train.shape}")
        return X_train, X_test, vectorizer

    def train_model(self, X_train, y_train, dataset_type: str = 'general'):
        """Train model with dataset-specific parameters"""
        logger.info(f"Training Random Forest model for {dataset_type} dataset...")

        # Dataset-specific model parameters
        if dataset_type == 'liar':
            # LIAR: Political statements - more complex patterns
            model = RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight='balanced',
                n_jobs=-1,
                max_depth=20,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features='sqrt',
                bootstrap=True
            )
        else:
            # Kaggle/General: News articles - standard parameters
            model = RandomForestClassifier(
                n_estimators=150,
                random_state=42,
                class_weight='balanced',
                n_jobs=-1,
                max_depth=15,
                min_samples_split=15,
                min_samples_leaf=8,
                max_features='sqrt',
                bootstrap=True
            )

        model.fit(X_train, y_train)
        
        try:
            logger.info(f"OOB Score: {model.oob_score_:.4f}")
        except AttributeError:
            logger.info("OOB score not available")

        return model

    def evaluate_model(self, model, X_train, y_train, X_test, y_test, dataset_type: str):
        """Enhanced evaluation with cross-validation"""
        try:
            print(f"=== {dataset_type.upper()} DATASET EVALUATION ===")
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, n_jobs=-1)
            print(f"CV Scores: {cv_scores}")
            print(f"Mean CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

            # Test set evaluation
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

            # Detailed classification report
            class_report = classification_report(y_test, y_pred, output_dict=True)

            results = {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'cv_scores': [float(s) for s in cv_scores],
                'classification_report': class_report,
                'dataset_type': dataset_type
            }

            logger.info(f"Model evaluation complete. Test Accuracy: {accuracy:.4f}")
            return results
            
        except Exception as e:
            logger.error(f"Error during model evaluation: {str(e)}")
            return {"error": str(e), "dataset_type": dataset_type}

    def save_model(self, model, vectorizer, evaluation_results, dataset_type: str):
        """Save trained model and artifacts with dataset-specific naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_version = f"model_{dataset_type}_{timestamp}"
        model_dir = self.models_dir / model_version
        model_dir.mkdir(exist_ok=True)

        # Save model artifacts
        joblib.dump(model, model_dir / "model.pkl", compress=3)
        joblib.dump(vectorizer, model_dir / "vectorizer.pkl", compress=3)

        # Save evaluation results
        with open(model_dir / "evaluation.json", 'w') as f:
            json.dump(evaluation_results, f, indent=2)

        # Save metadata
        metadata = {
            'model_type': 'random_forest',
            'training_date': timestamp,
            'version': model_version,
            'dataset': dataset_type.upper(),
            'features': 'TF-IDF',
            'algorithm': 'RandomForest',
            'dataset_size': evaluation_results.get('dataset_size', 0),
            'label_distribution': evaluation_results.get('label_distribution', {})
        }
        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to: {model_dir.resolve()}")
        return model_version

    def train_dataset_model(self, dataset_type: str):
        """Complete training pipeline for specific dataset"""
        logger.info(f"Starting {dataset_type.upper()} dataset model training...")

        try:
            # Load data
            dataset = self.load_dataset(dataset_type)
            if dataset is None:
                raise ValueError(f"Failed to load {dataset_type} dataset")

            # Debug dataset structure
            print(f"=== {dataset_type.upper()} DATASET STRUCTURE ===")
            print(f"Columns: {dataset.columns.tolist()}")
            print(f"Shape: {dataset.shape}")
            print(f"Label distribution:")
            print(dataset['label'].value_counts())

            # Prepare data
            processed_data = self.prepare_data(dataset, dataset_type)

            if processed_data.empty or len(processed_data) < 10:
                raise ValueError(f"Processed {dataset_type} dataset is too small for training")

            # Split into train and test
            train_df, test_df = train_test_split(
                processed_data,
                test_size=0.2,
                random_state=42,
                stratify=processed_data['label']
            )

            # Extract features
            X_train, X_test, vectorizer = self.extract_features(
                train_df['cleaned_text'].tolist(),
                test_df['cleaned_text'].tolist(),
                dataset_type
            )

            y_train = train_df['label'].values
            y_test = test_df['label'].values

            # Train model
            model = self.train_model(X_train, y_train, dataset_type)

            # Evaluate model
            evaluation_results = self.evaluate_model(model, X_train, y_train, X_test, y_test, dataset_type)

            # Add dataset info to results
            evaluation_results['dataset_size'] = len(processed_data)
            evaluation_results['label_distribution'] = processed_data['label'].value_counts().to_dict()

            # Save model
            model_version = self.save_model(model, vectorizer, evaluation_results, dataset_type)

            results = {
                'model_version': model_version,
                'evaluation': evaluation_results,
                'training_date': datetime.now().isoformat(),
                'dataset_type': dataset_type,
                'dataset_size': len(processed_data),
                'label_distribution': processed_data['label'].value_counts().to_dict()
            }

            logger.info(f"✅ {dataset_type.upper()} model training completed successfully!")
            self._print_training_summary(results)

            return results

        except Exception as e:
            logger.error(f"❌ {dataset_type.upper()} model training failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _print_training_summary(self, results):
        """Print training summary"""
        print(f"\n=== {results['dataset_type'].upper()} TRAINING SUMMARY ===")
        print(f"Dataset size: {results['dataset_size']}")
        print(f"Label distribution: {results['label_distribution']}")
        
        eval_results = results['evaluation']
        if isinstance(eval_results, dict) and 'accuracy' in eval_results:
            print(f"Test Accuracy: {eval_results['accuracy']:.4f}")
            print(f"CV Mean Accuracy: {eval_results['cv_mean']:.4f}")
            print(f"Precision: {eval_results['precision']:.4f}")
            print(f"Recall: {eval_results['recall']:.4f}")
            print(f"F1 Score: {eval_results['f1_score']:.4f}")
        else:
            print("Evaluation results not available")

    def train_all_models(self):
        """Train models for all available datasets"""
        results = {}
        
        # Train LIAR model
        try:
            liar_results = self.train_dataset_model('liar')
            results['liar'] = liar_results
        except Exception as e:
            logger.error(f"LIAR model training failed: {e}")
            results['liar'] = {'error': str(e)}

        # Train Kaggle model
        try:
            kaggle_results = self.train_dataset_model('kaggle')
            results['kaggle'] = kaggle_results
        except Exception as e:
            logger.error(f"Kaggle model training failed: {e}")
            results['kaggle'] = {'error': str(e)}

        return results


def train_model(dataset_type: str = 'liar', train_all: bool = False):
    """
    Main function to train fake news detection models
    
    Args:
        dataset_type: 'liar', 'kaggle', or 'combined'
        train_all: If True, train all available models
    """
    trainer = SimpleModelTrainer()
    
    if train_all:
        results = trainer.train_all_models()
    else:
        results = trainer.train_dataset_model(dataset_type)
    
    return results


if __name__ == "__main__":
    # Command line argument parsing
    parser = argparse.ArgumentParser(description='Train fake news detection models')
    parser.add_argument('--dataset', type=str, default='liar', 
                       choices=['liar', 'kaggle', 'combined'],
                       help='Dataset to train on (default: liar)')
    parser.add_argument('--all', action='store_true',
                       help='Train all available models')
    
    args = parser.parse_args()

    if args.all:
        print("🚀 Training ALL available models...")
        results = train_model(train_all=True)
    else:
        print(f"🚀 Training with {args.dataset.upper()} Dataset...")
        results = train_model(dataset_type=args.dataset, train_all=False)