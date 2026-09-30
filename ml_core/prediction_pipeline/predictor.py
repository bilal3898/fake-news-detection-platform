import joblib
import numpy as np
import pandas as pd
import re
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime
import json

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from ml_core.settings import get_settings
from ml_core.prediction_pipeline.preprocessor import TextPreprocessor


logger = logging.getLogger(__name__)
settings = get_settings()


class AdvancedFakeNewsPredictor:
    def __init__(self, model_dir: str = "ml_core/models/model_latest"):
        self.model_dir = Path(model_dir)
        self.models = {}
        self.vectorizers = {}
        self.label_encoders = {}
        self.transformers_pipelines = {}
        self.ensemble_weights = {}
        
        self._load_models()
        self._setup_ensemble_weights()

    @staticmethod
    def clean_text(text: str) -> str:
        """Simple text cleaning"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _load_models(self):
        """Load ML and Transformer models"""
        try:
            # Load traditional ML models
            self._load_ml_models()
            # Load transformer models
            self._load_transformer_models()
            logger.info("All models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    def _load_ml_models(self):
        model_files = list(self.model_dir.glob("*.pkl"))
        for model_file in model_files:
            try:
                model_name = model_file.stem
                if model_name == "vectorizer":
                    self.vectorizers["vectorizer"] = joblib.load(model_file)
                elif model_name == "label_encoder":
                    self.label_encoders["label_encoder"] = joblib.load(model_file)
                elif model_name.endswith("_model"):
                    model_type = model_name.replace("_model", "")
                    self.models[model_type] = joblib.load(model_file)
                    logger.info(f"Loaded {model_type} model")
            except Exception as e:
                logger.warning(f"Failed to load {model_file}: {e}")

    def _load_transformer_models(self):
        transformer_models = {
            "bert": "bert-base-uncased",
            "distilbert": "distilbert-base-uncased",
            "roberta": "roberta-base",
        }

        for model_name, model_path in transformer_models.items():
            try:
                local_path = self.model_dir / model_name
                if local_path.exists():
                    tokenizer = AutoTokenizer.from_pretrained(local_path)
                    model = AutoModelForSequenceClassification.from_pretrained(local_path)
                else:
                    tokenizer = AutoTokenizer.from_pretrained(model_path)
                    model = AutoModelForSequenceClassification.from_pretrained(model_path)

                pipe = pipeline(
                    "text-classification",
                    model=model,
                    tokenizer=tokenizer,
                    device=0 if torch.cuda.is_available() else -1,
                    return_all_scores=True
                )

                self.transformers_pipelines[model_name] = pipe
                logger.info(f"Loaded {model_name} transformer model")

            except Exception as e:
                logger.warning(f"Failed to load {model_name} transformer: {e}")

    def _setup_ensemble_weights(self):
        self.ensemble_weights = {
            "logistic_regression": 0.3,
            "random_forest": 0.25,
            "bert": 0.45
        }

    def predict(self, text: str, use_ensemble: bool = True) -> Dict[str, Any]:
        try:
            processed_text = TextPreprocessor.prepare_for_ml(text)

            if use_ensemble and len(self.models) + len(self.transformers_pipelines) > 1:
                result = self._ensemble_predict(processed_text)
            else:
                result = self._single_model_predict(processed_text)

            result.update({
                "timestamp": datetime.utcnow().isoformat(),
                "processed_text_length": len(processed_text),
            })

            return result

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._fallback_prediction(text, str(e))

    def _single_model_predict(self, processed_text: str) -> Dict[str, Any]:
        for model_name, pipe in self.transformers_pipelines.items():
            try:
                return self._transformers_predict(processed_text, pipe, model_name)
            except:
                continue

        for model_name, model in self.models.items():
            try:
                return self._ml_model_predict(processed_text, model, model_name)
            except:
                continue

        return self._fallback_prediction(processed_text, "No models available")

    def _ensemble_predict(self, processed_text: str) -> Dict[str, Any]:
        predictions = []
        confidences = []

        for model_name, model in self.models.items():
            try:
                pred = self._ml_model_predict(processed_text, model, model_name)
                predictions.append(pred["prediction"])
                confidences.append(pred["confidence"])
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")

        for model_name, pipe in self.transformers_pipelines.items():
            try:
                pred = self._transformers_predict(processed_text, pipe, model_name)
                predictions.append(pred["prediction"])
                confidences.append(pred["confidence"])
            except Exception as e:
                logger.warning(f"Transformer {model_name} failed: {e}")

        if not predictions:
            return self._fallback_prediction(processed_text, "All models failed")

        fake_votes = real_votes = total_confidence = 0
        for pred, conf in zip(predictions, confidences):
            weight = self.ensemble_weights.get("default", 0.5)
            if pred == "FAKE":
                fake_votes += weight * conf
            else:
                real_votes += weight * conf
            total_confidence += conf

        if fake_votes > real_votes:
            final_prediction = "FAKE"
            confidence = fake_votes / (fake_votes + real_votes)
        else:
            final_prediction = "REAL"
            confidence = real_votes / (fake_votes + real_votes)

        return {
            "prediction": final_prediction,
            "confidence": float(confidence),
            "model_type": "ensemble",
            "component_predictions": predictions,
            "component_confidences": confidences
        }

    def _ml_model_predict(self, processed_text: str, model, model_name: str) -> Dict[str, Any]:
        if "vectorizer" not in self.vectorizers:
            raise ValueError("No vectorizer available")

        X = self.vectorizers["vectorizer"].transform([processed_text])
        prediction = model.predict(X)
        probability = model.predict_proba(X)

        if "label_encoder" in self.label_encoders:
            decoded_pred = self.label_encoders["label_encoder"].inverse_transform(prediction)[0]
        else:
            decoded_pred = "FAKE" if prediction[0] == 1 else "REAL"

        confidence = float(np.max(probability[0]))

        return {
            "prediction": decoded_pred,
            "confidence": confidence,
            "model_type": model_name,
            "probabilities": {
                "real": float(probability[0][0]),
                "fake": float(probability[0][1])
            }
        }

    def _transformers_predict(self, processed_text: str, pipe, model_name: str) -> Dict[str, Any]:
        results = pipe(processed_text)
        probs = {result['label']: result['score'] for result in results[0]}

        if probs.get('FAKE', 0) > probs.get('REAL', 0):
            prediction = "FAKE"
            confidence = probs.get('FAKE', 0)
        else:
            prediction = "REAL"
            confidence = probs.get('REAL', 0)

        return {
            "prediction": prediction,
            "confidence": float(confidence),
            "model_type": f"transformer_{model_name}",
            "probabilities": probs
        }

    def _fallback_prediction(self, text: str, error: str = "") -> Dict[str, Any]:
        fake_keywords = ['fake', 'false', 'hoax', 'conspiracy', 'rumor', 'lie']
        fake_count = sum(1 for keyword in fake_keywords if keyword in text.lower())

        if fake_count > 1:
            confidence = min(0.7, fake_count * 0.2)
            prediction = "FAKE"
        else:
            confidence = 0.6
            prediction = "REAL"

        return {
            "prediction": prediction,
            "confidence": confidence,
            "model_type": "rule_based_fallback",
            "error": error,
            "warning": "Using fallback prediction due to model failure"
        }

    def get_model_info(self) -> Dict[str, Any]:
        info = {
            "traditional_ml_models": list(self.models.keys()),
            "transformer_models": list(self.transformers_pipelines.keys()),
            "vectorizers": list(self.vectorizers.keys()),
            "label_encoders": list(self.label_encoders.keys()),
            "ensemble_weights": self.ensemble_weights,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            eval_path = self.model_dir / "evaluation.json"
            if eval_path.exists():
                with open(eval_path, 'r') as f:
                    info["performance_metrics"] = json.load(f)
        except:
            pass

        return info


# Singleton instance
fake_news_predictor = AdvancedFakeNewsPredictor()


# Simple direct prediction function for standalone usage
def predict_news(text: str) -> Dict[str, Any]:
    cleaned_text = AdvancedFakeNewsPredictor.clean_text(text)

    # Load default model and vectorizer as fallback
    model = joblib.load('ml_core/models/model_20250917_000744/model.pkl')
    vectorizer = joblib.load('ml_core/models/model_20250917_000744/vectorizer.pkl')

    features = vectorizer.transform([cleaned_text])
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0]

    return {
        'prediction': 'Fake' if prediction == 1 else 'Real',
        'confidence': max(probability),
        'fake_probability': probability[1],
        'real_probability': probability[0]
    }


if __name__ == "__main__":
    # Example test
    test_text = "This is a sample news article to check if it's fake or real."
    result = fake_news_predictor.predict(test_text)
    print(f"[AdvancedPredictor] Prediction: {result['prediction']}, Confidence: {result['confidence']:.2%}")

    result_simple = predict_news(test_text)
    print(f"[SimplePredict] Prediction: {result_simple['prediction']}, Confidence: {result_simple['confidence']:.2%}")