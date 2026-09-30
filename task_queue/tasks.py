# task_queue/tasks.py

"""
Celery tasks for Fake News Detection application
"""

from celery import Celery, current_task
from celery.signals import task_failure, task_success
from celery.utils.log import get_task_logger
import time
from typing import Dict, Any, Optional
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from backend.utils.config import get_settings
from data_ingestion.url_content_extractor import URLContentExtractor
from data_ingestion.news_api_client import NewsAPIClient
from data_ingestion.rss_scraper import RSSScraper
from data_ingestion.twitter_listener import TwitterListener
from backend.services.preprocessing import TextPreprocessor
from backend.services.prediction_final import final_prediction_service
from backend.services.training import ModelTrainer
from backend.database.mongo_connection import get_database
from backend.database.postgres_connection import get_db
from backend.database.models import PredictionResult, UserFeedback

# Initialize Celery app
from task_queue.celeryconfig import broker_url, result_backend

app = Celery('fake_news_tasks', broker_url=broker_url, result_backend=result_backend)

logger = get_task_logger(__name__)

# Initialize services
url_extractor = URLContentExtractor()
text_preprocessor = TextPreprocessor()
prediction_service = final_prediction_service
news_client = NewsAPIClient()
rss_scraper = RSSScraper()
twitter_listener = TwitterListener()
model_trainer = ModelTrainer()

@app.task(bind=True, name='process_url_task', max_retries=3, default_retry_delay=60)
def process_url_task(self, url: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process URL content extraction and prediction (background task)
    """
    try:
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'step': 'Extracting content from URL', 'progress': 25}
        )
        
        # Extract content from URL
        content = url_extractor.extract_content(url)
        
        if 'error' in content:
            logger.error(f"Failed to extract content from {url}: {content['error']}")
            raise ValueError(f"Content extraction failed: {content['error']}")
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'step': 'Preprocessing text', 'progress': 50}
        )
        
        # Preprocess text
        cleaned_text = text_preprocessor.clean_text(content['text'])
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'step': 'Making prediction', 'progress': 75}
        )
        
        # Make prediction using enhanced service with content validation
        prediction = final_prediction_service.predict(cleaned_text, content.get('title'))
        
        # Store result in database
        db = next(get_db())
        prediction_record = PredictionResult(
            text_hash=hash(cleaned_text),
            text_snippet=cleaned_text[:500],
            source=url,
            prediction=prediction['prediction'],
            confidence=prediction['confidence'],
            probabilities=prediction.get('probabilities'),
            model_version=prediction.get('model_version'),
            model_type=prediction.get('model_type'),
            user_id=user_id
        )
        
        db.add(prediction_record)
        db.commit()
        
        result = {
            'status': 'COMPLETED',
            'url': url,
            'title': content.get('title', 'No title'),
            'prediction': prediction,
            'content_preview': cleaned_text[:200] + '...' if len(cleaned_text) > 200 else cleaned_text,
            'prediction_id': prediction_record.id,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully processed URL: {url}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        # Retry the task
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            return {
                'status': 'FAILED',
                'url': url,
                'error': str(e),
                'retries_exhausted': True
            }

@app.task(bind=True, name='train_model_task', max_retries=2, default_retry_delay=300)
def train_model_task(self, model_type: str = 'logistic_regression', 
                    data_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Train machine learning model (background task)
    """
    try:
        self.update_state(
            state='PROCESSING',
            meta={'step': 'Starting model training', 'progress': 10}
        )
        
        # Train model
        result = model_trainer.run_training_pipeline(
            data_path=data_path,
            model_type=model_type,
            balance_classes=True
        )
        
        self.update_state(
            state='PROCESSING',
            meta={'step': 'Finalizing training', 'progress': 90}
        )
        
        # Update prediction service with new model
        prediction_service.initialize_predictor()
        
        result['status'] = 'COMPLETED'
        result['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Model training completed: {model_type}")
        return result
        
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        try:
            raise self.retry(exc=e, countdown=300)
        except self.MaxRetriesExceededError:
            return {
                'status': 'FAILED',
                'model_type': model_type,
                'error': str(e),
                'retries_exhausted': True
            }

@app.task(name='scheduled_news_scraping')
def scheduled_news_scraping():
    """
    Scheduled task for news scraping from various sources
    """
    try:
        logger.info("Starting scheduled news scraping...")
        
        # Scrape from multiple sources
        results = {}
        
        # News API
        news_articles = news_client.fetch_and_store_news()
        results['news_api'] = len(news_articles)
        
        # RSS Feeds
        rss_articles = rss_scraper.scheduled_scraping()
        results['rss'] = len(rss_articles)
        
        # Twitter (if configured)
        try:
            tweets = twitter_listener.get_trending_news()
            results['twitter'] = len(tweets)
        except Exception as e:
            logger.warning(f"Twitter scraping failed: {e}")
            results['twitter'] = 0
        
        logger.info(f"News scraping completed: {results}")
        return {
            'status': 'COMPLETED',
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scheduled news scraping failed: {e}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }

@app.task(name='clean_old_tasks')
def clean_old_tasks(days_old: int = 7):
    """
    Clean up old task results from database
    """
    try:
        logger.info(f"Cleaning up tasks older than {days_old} days...")
        
        # This would typically clean up task results from your result backend
        # For Redis, you might use: redis_client.zremrangebyscore('key', '-inf', cutoff_time)
        # For this example, we'll just log the action
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        logger.info(f"Would clean tasks before {cutoff_date}")
        
        return {
            'status': 'COMPLETED',
            'cleaned_before': cutoff_date.isoformat(),
            'message': 'Task cleanup completed (simulated)'
        }
        
    except Exception as e:
        logger.error(f"Task cleanup failed: {e}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }

@app.task(name='check_model_performance')
def check_model_performance():
    """
    Check model performance and trigger retraining if needed
    """
    try:
        logger.info("Checking model performance...")
        
        # Get recent predictions from database
        db = next(get_db())
        recent_predictions = db.query(PredictionResult).filter(
            PredictionResult.created_at >= datetime.utcnow() - timedelta(days=1)
        ).all()
        
        if not recent_predictions:
            return {
                'status': 'COMPLETED',
                'message': 'No recent predictions to analyze'
            }
        
        # Calculate accuracy based on user feedback (if available)
        feedback_count = db.query(UserFeedback).count()
        
        if feedback_count > 100:  # Only check if we have sufficient feedback
            correct_predictions = db.query(UserFeedback).filter(
                UserFeedback.is_correct == True
            ).count()
            
            accuracy = correct_predictions / feedback_count if feedback_count > 0 else 0
            
            if accuracy < 0.7:  # Threshold for retraining
                logger.warning(f"Low model accuracy detected: {accuracy:.3f}. Triggering retraining...")
                # Schedule retraining
                train_model_task.delay(model_type='logistic_regression')
                
                return {
                    'status': 'COMPLETED',
                    'accuracy': accuracy,
                    'retraining_triggered': True
                }
        
        return {
            'status': 'COMPLETED',
            'feedback_count': feedback_count,
            'retraining_triggered': False
        }
        
    except Exception as e:
        logger.error(f"Model performance check failed: {e}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }

@app.task(name='batch_prediction_task')
def batch_prediction_task(texts: List[str], batch_id: str) -> Dict[str, Any]:
    """
    Process batch predictions for multiple texts
    """
    try:
        results = []
        
        for i, text in enumerate(texts):
            # Update progress periodically
            if i % 10 == 0:
                current_task.update_state(
                    state='PROCESSING',
                    meta={
                        'step': f'Processing batch {batch_id}',
                        'progress': (i / len(texts)) * 100,
                        'processed': i,
                        'total': len(texts)
                    }
                )
            
            # Preprocess and predict
            cleaned_text = text_preprocessor.clean_text(text)
            prediction = prediction_service.predict_from_text(cleaned_text)
            
            results.append({
                'text': text[:100] + '...' if len(text) > 100 else text,
                'prediction': prediction,
                'processed_at': datetime.utcnow().isoformat()
            })
        
        return {
            'status': 'COMPLETED',
            'batch_id': batch_id,
            'total_processed': len(results),
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch prediction failed for batch {batch_id}: {e}")
        return {
            'status': 'FAILED',
            'batch_id': batch_id,
            'error': str(e),
            'processed': len(results) if 'results' in locals() else 0
        }

@app.task(name='export_predictions_task')
def export_predictions_task(start_date: str, end_date: str, format: str = 'csv'):
    """
    Export predictions to file (background task)
    """
    try:
        logger.info(f"Exporting predictions from {start_date} to {end_date} in {format} format")
        
        # Query database for predictions in date range
        db = next(get_db())
        predictions = db.query(PredictionResult).filter(
            PredictionResult.created_at.between(start_date, end_date)
        ).all()
        
        # Convert to DataFrame
        import pandas as pd
        data = []
        for pred in predictions:
            data.append({
                'id': pred.id,
                'text_snippet': pred.text_snippet,
                'prediction': pred.prediction,
                'confidence': pred.confidence,
                'model_version': pred.model_version,
                'created_at': pred.created_at
            })
        
        df = pd.DataFrame(data)
        
        # Export based on format
        filename = f"predictions_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"
        filepath = f"/tmp/{filename}"
        
        if format == 'csv':
            df.to_csv(filepath, index=False)
        elif format == 'json':
            df.to_json(filepath, orient='records', indent=2)
        elif format == 'parquet':
            df.to_parquet(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return {
            'status': 'COMPLETED',
            'filename': filename,
            'filepath': filepath,
            'record_count': len(df),
            'format': format
        }
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }

# Task error handler
@task_failure.connect
def task_failure_handler(sender=None, exception=None, traceback=None, **kwargs):
    if hasattr(exception, 'is_retry') and exception.is_retry:
        print(f"Task {sender.name} failed: {exception}")
    else:
        print(f"Task {sender.name} failed: {exception}")

# Task success handler
@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    print(f"Task {sender.name} succeeded: {result}")