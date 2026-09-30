import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score,
    precision_recall_curve, roc_curve, auc
)
from sklearn.model_selection import learning_curve, validation_curve
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelEvaluator:
    def __init__(self):
        self.metrics_history = []
    
    def load_processed_data(self):
        """Load already processed datasets"""
        try:
            # Use absolute path to avoid issues
            current_dir = Path(__file__).parent
            val_path = current_dir.parent.parent / 'dataset' / 'processed' / 'val.csv'
            
            logger.info(f"Loading validation data from: {val_path}")
            
            if val_path.exists():
                val_df = pd.read_csv(val_path)
                logger.info(f"Loaded validation data: {len(val_df)} rows")
                return val_df
            else:
                logger.warning(f"Validation file not found: {val_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading processed data: {e}")
            return None
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, 
                         y_pred_proba: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Calculate comprehensive evaluation metrics
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0),
        }
        
        # For binary classification
        if y_pred_proba is not None and len(np.unique(y_true)) == 2:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba[:, 1])
            except:
                metrics['roc_auc'] = 0.0
        
        return metrics
    
    def evaluate_model(self, model, X_test: np.ndarray, y_test: np.ndarray,
                      class_names: List[str]) -> Dict[str, Any]:
        """
        Comprehensive model evaluation
        """
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
        
        # Calculate metrics
        metrics = self.calculate_metrics(y_test, y_pred, y_pred_proba)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Classification report
        class_report = classification_report(
            y_test, y_pred, 
            target_names=class_names, 
            output_dict=True,
            zero_division=0
        )
        
        # Additional analysis
        feature_importance = self.get_feature_importance(model)
        
        results = {
            'metrics': metrics,
            'confusion_matrix': cm.tolist(),
            'classification_report': class_report,
            'feature_importance': feature_importance,
            'test_set_size': len(y_test),
            'class_distribution': np.bincount(y_test).tolist()
        }
        
        # Add ROC and PR curves if binary classification
        if y_pred_proba is not None and len(class_names) == 2:
            roc_info = self.calculate_roc_curve(y_test, y_pred_proba[:, 1])
            pr_info = self.calculate_pr_curve(y_test, y_pred_proba[:, 1])
            results['roc_curve'] = roc_info
            results['pr_curve'] = pr_info
        
        self.metrics_history.append(metrics)
        return results
    
    def get_feature_importance(self, model) -> List[float]:
        """
        Get feature importance from model
        """
        try:
            if hasattr(model, 'feature_importances_'):
                return model.feature_importances_.tolist()
            elif hasattr(model, 'coef_'):
                return np.mean(np.abs(model.coef_), axis=0).tolist()
            else:
                return []
        except:
            return []
    
    def calculate_roc_curve(self, y_true: np.ndarray, y_scores: np.ndarray) -> Dict[str, Any]:
        """
        Calculate ROC curve data
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_scores)
        roc_auc = auc(fpr, tpr)
        
        return {
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist(),
            'thresholds': thresholds.tolist(),
            'auc': roc_auc
        }
    
    def calculate_pr_curve(self, y_true: np.ndarray, y_scores: np.ndarray) -> Dict[str, Any]:
        """
        Calculate Precision-Recall curve data
        """
        precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
        pr_auc = auc(recall, precision)
        
        return {
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'thresholds': thresholds.tolist(),
            'auc': pr_auc
        }
    
    def create_visualizations(self, evaluation_results: Dict[str, Any], 
                            output_dir: str, model_name: str):
        """
        Create evaluation visualizations
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Confusion matrix heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(evaluation_results['confusion_matrix'], 
                   annot=True, fmt='d', cmap='Blues')
        plt.title(f'Confusion Matrix - {model_name}')
        plt.savefig(output_path / 'confusion_matrix.png')
        plt.close()
        
        # ROC Curve (if available)
        if 'roc_curve' in evaluation_results:
            plt.figure(figsize=(10, 8))
            roc_data = evaluation_results['roc_curve']
            plt.plot(roc_data['fpr'], roc_data['tpr'], 
                    label=f'ROC curve (AUC = {roc_data["auc"]:.2f})')
            plt.plot([0, 1], [0, 1], 'k--')
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title(f'ROC Curve - {model_name}')
            plt.legend()
            plt.savefig(output_path / 'roc_curve.png')
            plt.close()
        
        # Feature importance (if available)
        if evaluation_results['feature_importance']:
            plt.figure(figsize=(12, 6))
            importance = evaluation_results['feature_importance']
            plt.bar(range(len(importance)), importance)
            plt.title(f'Feature Importance - {model_name}')
            plt.savefig(output_path / 'feature_importance.png')
            plt.close()
    
    def compare_models(self, model_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple models
        """
        comparison = {}
        
        for i, results in enumerate(model_results):
            model_name = results.get('model_type', f'model_{i}')
            comparison[model_name] = {
                'accuracy': results['evaluation']['metrics']['accuracy'],
                'f1_score': results['evaluation']['metrics']['f1_score'],
                'precision': results['evaluation']['metrics']['precision'],
                'recall': results['evaluation']['metrics']['recall']
            }
            
            if 'roc_auc' in results['evaluation']['metrics']:
                comparison[model_name]['roc_auc'] = results['evaluation']['metrics']['roc_auc']
        
        return comparison
    
    def save_evaluation_report(self, evaluation_results: Dict[str, Any], 
                             output_path: str):
        """
        Save comprehensive evaluation report
        """
        with open(output_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2)
        
        logger.info(f"Evaluation report saved to: {output_path}")

# Singleton instance
model_evaluator = ModelEvaluator()