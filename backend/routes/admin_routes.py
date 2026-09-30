# backend/routes/admin_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from typing import List, Dict, Any

from backend.database.postgres_connection import get_db
from backend.database.models import User, PredictionResult, ModelPerformance
from backend.schemas import SuccessResponse
from backend.services.training import model_trainer
from backend.services.prediction import prediction_service
from backend.utils.password_utils import get_password_hash, generate_secure_password
from backend.dependencies.auth import get_current_admin_user
from data_ingestion.news_api_client import news_api_client
from data_ingestion.rss_scraper import rss_scraper
from data_ingestion.twitter_listener import twitter_listener

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])

# ----------------- Endpoints ----------------- #

@router.get("/stats/detailed")
async def get_detailed_stats():
    """
    Get detailed system statistics for admin dashboard
    """
    try:
        # Placeholder for actual analytics
        return {"message": "Detailed stats endpoint"}
    except Exception as e:
        logger.error(f"Error getting detailed stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/retrain")
async def retrain_model():
    """
    Trigger manual model retraining
    """
    try:
        result = model_trainer.train_model()
        return {"message": "Model retraining started", "result": result}
    except Exception as e:
        logger.error(f"Error retraining model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/list")
async def list_models():
    """
    List all available trained models
    """
    try:
        models = model_trainer.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/refresh")
async def refresh_data():
    """
    Trigger data refresh from all sources
    """
    try:
        # Refresh from multiple sources
        news_articles = news_api_client.fetch_and_store_news()
        rss_articles = rss_scraper.scheduled_scraping()
        tweets = twitter_listener.get_trending_news()
        
        return {
            "message": "Data refresh completed",
            "results": {
                "news_articles": len(news_articles),
                "rss_articles": len(rss_articles),
                "tweets": len(tweets)
            }
        }
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/reset-password", response_model=SuccessResponse)
async def admin_reset_user_password(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin resets a user password (generates temporary password)
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate secure temporary password
        temp_password = generate_secure_password(12)
        user.password_hash = get_password_hash(temp_password)
        user.password_changed_at = datetime.utcnow()
        db.commit()
        
        # In production, email the temp password instead of returning it
        logger.info(f"Admin reset password for user {user.email}. Temp password: {temp_password}")
        
        return SuccessResponse(
            success=True,
            message="Password reset successfully",
            data={"temp_password": temp_password}  # Only for demo
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Admin password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )