# prediction_final.py - Final hybrid approach using ML + targeted fake detection
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
from datetime import datetime
import joblib
import json
import re
from typing import Dict, Any, Optional, List
import logging

# Try relative imports first, fallback to absolute.  Configuration is optional
# here: prediction must still fail safely when an application configuration file
# has not been created yet.
try:
    from utils.config import get_settings
    from utils.logger import get_logger
    from .content_detector import content_detector
except ImportError:
    try:
        from backend.utils.config import get_settings
        from backend.utils.logger import get_logger
    except ImportError:
        get_settings = None
        get_logger = None
    from backend.services.content_detector import content_detector

logger = logging.getLogger(__name__)
settings = get_settings() if get_settings else None


class FinalPredictionService:
    _instance: Optional['FinalPredictionService'] = None
    MIN_CONFIDENCE = 0.70
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FinalPredictionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Load ML models and initialize hybrid detection"""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        try:
            # Initialize model registry
            self.models = {}
            self.active_model = None
            
            # Load production model
            self._load_production_model()
            
            # Set default model
            self._set_default_model()
            
            logger.info("✅ FinalPredictionService: ML prediction service initialized")
            
        except Exception as e:
            logger.error(f"❌ FinalPredictionService initialization failed: {e}")
            self.models = {}
            self.active_model = None
            
        self._initialized = True

    def _load_production_model(self):
        """Load the best production model"""
        try:
            project_root = Path(__file__).resolve().parents[2]
            production_models_dir = project_root / "ml_core" / "models"
            
            # Look for improved models first
            improved_model_paths = list(production_models_dir.glob("model_production_improved_*"))
            regular_model_paths = list(production_models_dir.glob("model_production_*"))
            
            # Choose improved if available, otherwise regular
            if improved_model_paths:
                model_paths = improved_model_paths
            else:
                model_paths = regular_model_paths
            
            if model_paths:
                latest_production_model = max(model_paths, key=lambda x: x.stat().st_mtime)
                model_path = latest_production_model / "model.pkl"
                
                if model_path.exists():
                    self.models['production'] = {
                        'model': joblib.load(model_path),
                        'model_type': 'production',
                        'loaded_at': datetime.now(),
                        'path': latest_production_model
                    }
                    
                    # Load metadata
                    metadata_path = latest_production_model / "metadata.json"
                    evaluation_path = latest_production_model / "evaluation.json"
                    
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            self.models['production']['metadata'] = json.load(f)
                    
                    if evaluation_path.exists():
                        with open(evaluation_path, 'r') as f:
                            self.models['production']['evaluation'] = json.load(f)
                    
                    model_type = "improved" if "improved" in latest_production_model.name else "standard"
                    logger.info(f"✅ Production model loaded: {latest_production_model.name} ({model_type})")
                else:
                    logger.warning("❌ Production model file not found")
            else:
                logger.warning("❌ No production models found")
                
        except Exception as e:
            logger.error(f"❌ Production model loading failed: {e}")

    def _set_default_model(self):
        """Set the default active model"""
        if 'production' in self.models:
            self.active_model = 'production'
            logger.info("✅ Default model set to: Production model")
        else:
            self.active_model = None
            logger.warning("⚠️ No ML models available; predictions will be marked uncertain")

    def clean_text(self, text: str) -> str:
        """Clean input text for prediction"""
        if pd.isna(text):
            return ""
            
        text = str(text).lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Keep meaningful characters
        text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', '', text)
        
        return text.strip()

    def predict(self, text: str, title: str = None) -> Dict[str, Any]:
        """Predict only when a trained model is available and sufficiently confident."""
        
        # Step 1: Check for content loading issues
        content_check = content_detector.detect_content_issues(text, title)
        
        if content_check["has_issues"]:
            # Log the issue
            logger.warning(f"Content issue detected: {content_check['issue_type']} (confidence: {content_check['confidence']:.2f})")
            
            # If severe issue, return appropriate response
            if content_detector.should_skip_prediction(content_check):
                fallback_response = content_detector.get_fallback_response(content_check, text, title)
                fallback_response["content_status"] = content_check
                fallback_response["model_type"] = "content_validation"
                return fallback_response
        
        # Use ML rather than phrase lists.  Phrases such as "government announces"
        # are not evidence that an article is real or fake.
        if self.active_model and self.active_model in self.models:
            try:
                model_info = self.models[self.active_model]
                cleaned_text = self.clean_text(text)
                
                if len(cleaned_text) >= 10:
                    # Get ML prediction
                    prediction = model_info['model'].predict([cleaned_text])[0]
                    probability = model_info['model'].predict_proba([cleaned_text])[0]
                    
                    classes = list(model_info['model'].classes_)
                    fake_index = classes.index(1) if 1 in classes else classes.index('FAKE')
                    real_index = classes.index(0) if 0 in classes else classes.index('REAL')
                    fake_prob = float(probability[fake_index])
                    real_prob = float(probability[real_index])
                    predicted_class = "FAKE" if prediction in (1, 'FAKE') else "REAL"
                    confidence = max(real_prob, fake_prob)
                    
                    ml_result = {
                        "prediction": predicted_class,
                        "confidence": confidence,
                        "probabilities": {"real": real_prob, "fake": fake_prob},
                        "raw_prediction": int(prediction) if isinstance(prediction, (int, np.integer)) else prediction,
                        "raw_probabilities": probability.tolist(),
                        "model_type": self.active_model,
                    }
                    
                    ml_result['content_status'] = content_check
                    if confidence < self.MIN_CONFIDENCE:
                        ml_result['prediction'] = 'UNCERTAIN'
                        ml_result['method'] = 'low_confidence_ml'
                        ml_result['message'] = 'The model confidence is below the decision threshold.'
                    return ml_result
                    
            except Exception as e:
                logger.error(f"ML prediction error: {e}")
        
        return {
            "prediction": "UNCERTAIN",
            "confidence": 0.0,
            "method": "model_unavailable",
            "model_type": "none",
            "message": "No trained model was available to make a reliable prediction.",
            "content_status": content_check,
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        info = {
            "active_model": self.active_model,
            "available_models": list(self.models.keys()),
            "models_loaded": len(self.models) > 0,
            "approach": "confidence_thresholded_ml",
            "minimum_confidence": self.MIN_CONFIDENCE,
        }
        
        if self.active_model and self.active_model in self.models:
            model_info = self.models[self.active_model]
            if 'metadata' in model_info:
                info['model_metadata'] = model_info['metadata']
            if 'evaluation' in model_info:
                info['model_evaluation'] = model_info['evaluation']
        
        return info


# Create singleton instance
final_prediction_service = FinalPredictionService()
