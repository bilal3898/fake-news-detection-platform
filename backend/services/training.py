# backend/services/training.py

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import json
import joblib
from pathlib import Path
import shutil

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from ml_core.training_pipeline.data_cleaning import data_preprocessor
from ml_core.training_pipeline.feature_engineering import extract_features
from ml_core.training_pipeline.train_model import SimpleModelTrainer
from ml_core.training_pipeline.evaluate_model import ModelEvaluator

from backend.services.preprocessing import TextPreprocessor
from backend.database.postgres_connection import get_db
from backend.database.mongo_connection import MongoDB
from backend.database.models import ModelPerformance
from backend.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelTrainer:
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.models_dir = Path(settings.MODEL_PATH)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def get_dataset_paths():
        """Get paths to all dataset files"""
        base_path = Path('../dataset')
        
        return {
            'raw_kaggle_fake': base_path / 'raw' / 'kaggle_fake.csv',
            'raw_kaggle_true': base_path / 'raw' / 'kaggle_true.csv',
            'processed_train': base_path / 'processed' / 'train.csv',
            'processed_test': base_path / 'processed' / 'test.csv',
            'processed_cleaned': base_path / 'processed' / 'cleaned_news_data.csv'
        }
    
    def load_training_data(self, data_path: Optional[str] = None) -> Tuple[List[str], List[str]]:
        """
        Load training data from various sources
        """
        if data_path:
            # Load from file
            df = pd.read_csv(data_path)
            texts = df['text'].tolist()
            labels = df['label'].tolist()
        else:
            # Load from database (example)
            try:
                from backend.database.models import PredictionResult
                db = next(get_db())
                results = db.query(PredictionResult).filter(
                    PredictionResult.confidence > 0.8
                ).limit(10000).all()
                
                texts = [result.text_snippet for result in results]
                labels = [result.prediction for result in results]
                
            except Exception as e:
                logger.error(f"Error loading data from database: {e}")
                raise
        
        return texts, labels
    
    def train_model(self, 
                   model_type: str = 'logistic_regression',
                   param_grid: Optional[Dict] = None,
                   data_path: Optional[str] = None,
                   test_size: float = 0.2,
                   cv_folds: int = 5) -> Dict[str, Any]:
        """
        Train a machine learning model
        """
        try:
            # Load data
            texts, labels = self.load_training_data(data_path)
            
            if not texts or not labels:
                raise ValueError("No training data available")
            
            logger.info(f"Training on {len(texts)} samples")
            
            # Prepare training data
            X_train, X_test, y_train, y_test, vectorizer, label_encoder = \
                self.preprocessor.prepare_training_data(
                    texts, labels, test_size=test_size
                )
            
            # Define model
            if model_type == 'logistic_regression':
                model = LogisticRegression(
                    random_state=42, 
                    max_iter=1000,
                    class_weight='balanced'
                )
                default_params = {
                    'C': [0.1, 1, 10],
                    'solver': ['liblinear', 'saga']
                }
                
            elif model_type == 'random_forest':
                model = RandomForestClassifier(
                    random_state=42,
                    class_weight='balanced',
                    n_jobs=-1
                )
                default_params = {
                    'n_estimators': [100, 200],
                    'max_depth': [None, 10, 20],
                    'min_samples_split': [2, 5]
                }
                
            elif model_type == 'svm':
                model = SVC(
                    random_state=42,
                    class_weight='balanced',
                    probability=True
                )
                default_params = {
                    'C': [0.1, 1, 10],
                    'kernel': ['linear', 'rbf']
                }
                
            elif model_type == 'naive_bayes':
                model = MultinomialNB()
                default_params = {'alpha': [0.1, 0.5, 1.0]}
                
            elif model_type == 'xgboost':
                model = XGBClassifier(
                    random_state=42,
                    use_label_encoder=False,
                    eval_metric='logloss'
                )
                default_params = {
                    'max_depth': [3, 6],
                    'learning_rate': [0.01, 0.1],
                    'n_estimators': [100, 200]
                }
                
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Hyperparameter tuning
            search_params = param_grid or default_params
            grid_search = GridSearchCV(
                model, search_params, 
                cv=cv_folds, 
                scoring='f1_weighted',
                n_jobs=-1,
                verbose=1
            )
            
            # Train model
            grid_search.fit(X_train, y_train)
            
            # Get best model
            best_model = grid_search.best_estimator_
            
            # Evaluate model
            evaluation = self.evaluate_model(best_model, X_test, y_test, label_encoder)
            
            # Save model
            model_version = self.save_model(
                best_model, vectorizer, label_encoder, evaluation, model_type
            )
            
            # Store performance in database
            self.store_performance_metrics(evaluation, model_type, model_version)
            
            return {
                'model_type': model_type,
                'model_version': model_version,
                'evaluation': evaluation,
                'best_params': grid_search.best_params_,
                'best_score': grid_search.best_score_
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def evaluate_model(self, model, X_test, y_test, label_encoder) -> Dict[str, Any]:
        """
        Evaluate model performance
        """
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # ROC AUC for binary classification
        if len(label_encoder.classes_) == 2:
            roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])
        else:
            roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovo')
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Classification report
        class_report = classification_report(
            y_test, y_pred, 
            target_names=label_encoder.classes_, 
            output_dict=True
        )
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'confusion_matrix': cm.tolist(),
            'classification_report': class_report,
            'test_set_size': len(y_test)
        }
    
    def save_model(self, model, vectorizer, label_encoder, evaluation, model_type: str) -> str:
        """
        Save trained model and artifacts
        """
        # Create versioned directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_version = f"{model_type}_{timestamp}"
        model_dir = self.models_dir / model_version
        model_dir.mkdir(exist_ok=True)
        
        # Save artifacts
        joblib.dump(model, model_dir / "model.pkl")
        joblib.dump(vectorizer, model_dir / "vectorizer.pkl")
        joblib.dump(label_encoder, model_dir / "label_encoder.pkl")
        
        # Save evaluation metrics
        with open(model_dir / "evaluation.json", 'w') as f:
            json.dump(evaluation, f, indent=2)
        
        # Save metadata
        metadata = {
            'model_type': model_type,
            'training_date': timestamp,
            'version': model_version,
            'classes': label_encoder.classes_.tolist()
        }
        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update latest symlink
        latest_path = self.models_dir / "model_latest"
        if latest_path.exists():
            latest_path.unlink()
        latest_path.symlink_to(model_version, target_is_directory=True)
        
        logger.info(f"Model saved to {model_dir}")
        return model_version
    
    def store_performance_metrics(self, evaluation: Dict[str, Any], model_type: str, version: str):
        """
        Store model performance in database
        """
        try:
            db = next(get_db())
            
            performance = ModelPerformance(
                model_version=version,
                accuracy=evaluation['accuracy'],
                precision=evaluation['precision'],
                recall=evaluation['recall'],
                f1_score=evaluation['f1_score'],
                training_date=datetime.now(),
                test_set_size=evaluation['test_set_size'],
                notes=f"{model_type} model trained on {datetime.now().date()}"
            )
            
            db.add(performance)
            db.commit()
            logger.info("Model performance metrics stored in database")
            
        except Exception as e:
            logger.error(f"Error storing performance metrics: {e}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available trained models
        """
        models = []
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir() and not model_dir.name.startswith('.'):
                metadata_path = model_dir / "metadata.json"
                eval_path = model_dir / "evaluation.json"
                
                if metadata_path.exists() and eval_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    with open(eval_path, 'r') as f:
                        evaluation = json.load(f)
                    
                    models.append({
                        'version': metadata['version'],
                        'model_type': metadata['model_type'],
                        'training_date': metadata['training_date'],
                        'evaluation': evaluation
                    })
        
        return sorted(models, key=lambda x: x['training_date'], reverse=True)
    
    def retrain_model(self, new_data: List[Dict[str, Any]], model_version: str) -> Dict[str, Any]:
        """
        Retrain model with new data
        """
        # Load existing model
        model_dir = self.models_dir / model_version
        if not model_dir.exists():
            raise ValueError(f"Model version {model_version} not found")
        
        model = joblib.load(model_dir / "model.pkl")
        vectorizer = joblib.load(model_dir / "vectorizer.pkl")
        label_encoder = joblib.load(model_dir / "label_encoder.pkl")
        
        # Prepare new data
        new_texts = [item['text'] for item in new_data]
        new_labels = [item['label'] for item in new_data]
        
        # Preprocess new texts
        cleaned_texts = self.preprocessor.batch_preprocess(new_texts)
        
        # Transform using existing vectorizer
        X_new = vectorizer.transform(cleaned_texts)
        y_new = label_encoder.transform(new_labels)
        
        # Retrain model (partial fit if supported)
        if hasattr(model, 'partial_fit'):
            model.partial_fit(X_new, y_new, classes=label_encoder.classes_)
        else:
            # For models that don't support partial fit, retrain completely
            # This would require combining with original training data
            logger.warning("Model doesn't support partial fit. Need full retraining.")
            # Implement full retraining logic here
        
        # Evaluate and save updated model
        evaluation = self.evaluate_model(model, X_new, y_new, label_encoder)
        new_version = self.save_model(model, vectorizer, label_encoder, evaluation, model.__class__.__name__)
        
        return {
            'new_version': new_version,
            'evaluation': evaluation,
            'samples_added': len(new_data)
        }

# Singleton instance
model_trainer = ModelTrainer()