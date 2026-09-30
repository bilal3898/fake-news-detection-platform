# backend/routes/news_routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import re
from datetime import datetime
import io
from PIL import Image
import pytesseract

from services.prediction_final import final_prediction_service
from backend.database.mongo_connection import get_database
from task_queue.tasks import process_url_task
from backend.database.postgres_connection import get_db, get_db_session
from backend.database.models import PredictionResult
from sqlalchemy.orm import Session
from backend.services.preprocessing import TextPreprocessor
from backend.services.prediction import PredictionService
from backend.middleware.auth_middleware import AuthMiddleware
from backend.utils.logger import get_logger

logger = logging.getLogger(__name__)
router = APIRouter()

class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=10, description="News text to analyze")
    source: Optional[str] = None
    title: Optional[str] = None

class URLRequest(BaseModel):
    url: str = Field(..., description="URL to analyze")

@router.post("/predict")
async def predict_news(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    mongo_db = Depends(get_database)
) -> Dict[str, Any]:
    """
    Analyze news text, store in PostgreSQL and MongoDB
    """
    try:
        # Clean text: remove null characters and other problematic characters
        text_for_prediction = request.text
        
        # Remove null characters and other control characters that cause issues
        if isinstance(text_for_prediction, str):
            # Remove null bytes and other problematic control characters
            text_for_prediction = text_for_prediction.replace('\x00', '').replace('\0', '')
            # Remove other control characters except newlines and tabs
            text_for_prediction = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text_for_prediction)
            # Limit extremely long inputs for prediction to avoid timeouts/memory spikes
            if len(text_for_prediction) > 20000:
                logger.info(f"Input text length {len(text_for_prediction)} > 20000; truncating for prediction only")
                text_for_prediction = text_for_prediction[:20000]
        
        if not text_for_prediction or len(text_for_prediction.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text is too short or contains only invalid characters. Minimum 10 characters required.")

        # Get prediction from enhanced ML service with content validation
        result = final_prediction_service.predict(text_for_prediction, request.title)

        # --- Store in PostgreSQL ---
        prediction_record = PredictionResult(
            text_hash = PredictionResult.create_text_hash(request.text),
            text_content=request.text,
            text_snippet=PredictionResult.create_snippet(request.text),
            source_name=request.source,
            prediction=result["prediction"],
            confidence=result["confidence"],
            probabilities=result.get("probabilities"),
            model_version=result.get("model_version"),
            model_type=result.get("model_type")
        )
        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)

        # --- Store in MongoDB (raw + audit) ---
        if mongo_db is not None:
            await mongo_db.predictions.insert_one({
                "text_snippet": request.text[:500],
                "source": request.source,
                "prediction_result": result,
                "timestamp": datetime.utcnow()
            })

        # Add SQL ID to result
        result["prediction_id"] = prediction_record.id

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Prediction API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-url")
async def predict_from_url(
    request: URLRequest,
    db: Session = Depends(get_db),
    mongo_db = Depends(get_database)
) -> Dict[str, Any]:
    """
    Analyze news from URL (synchronous processing with fallback)
    """
    try:
        from data_ingestion.url_content_extractor import URLContentExtractor
        
        # Extract content from URL
        url_extractor = URLContentExtractor()
        content = url_extractor.extract_content(request.url)
        
        if 'error' in content:
            error_msg = content.get('error', 'Unknown error')
            # Provide more helpful error message
            if 'Could not extract content' in error_msg:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unable to extract readable content from this URL. The page may require JavaScript, be behind a paywall, or have restricted access. Please try copying the text directly or use a different URL."
                )
            raise HTTPException(status_code=400, detail=f"Failed to extract content from URL: {error_msg}")
        
        if not content.get('text'):
            raise HTTPException(status_code=400, detail="No text content found in the URL. The page may be empty or contain only images/media.")
        
        # Clean extracted text
        extracted_text = content['text']
        # Remove null characters and control characters
        extracted_text = extracted_text.replace('\x00', '').replace('\0', '')
        extracted_text = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', extracted_text)
        
        if len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail=f"Extracted content is too short ({len(extracted_text.strip())} characters). Minimum 10 characters required. The page may not contain enough readable text."
            )
        
        # Update content with cleaned text
        content['text'] = extracted_text
        
        # Preprocess text
        text_preprocessor = TextPreprocessor()
        cleaned_text = text_preprocessor.clean_text(content['text'])
        
        # Limit text length for prediction
        text_for_prediction = cleaned_text
        if len(text_for_prediction) > 20000:
            logger.info(f"URL text length {len(text_for_prediction)} > 20000; truncating")
            text_for_prediction = text_for_prediction[:20000]
        
        # Get prediction from enhanced ML service with content validation
        result = final_prediction_service.predict(text_for_prediction, content.get('title'))
        
        # Store in PostgreSQL
        prediction_record = PredictionResult(
            text_hash=PredictionResult.create_text_hash(cleaned_text),
            text_content=cleaned_text,
            text_snippet=PredictionResult.create_snippet(cleaned_text),
            source_domain=content.get('source', ''),
            source_name=content.get('title', '')[:200],  # Limit to 200 chars
            prediction=result["prediction"],
            confidence=result["confidence"],
            probabilities=result.get("probabilities"),
            model_version=result.get("model_version"),
            model_type=result.get("model_type")
        )
        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)
        
        # Store in MongoDB
        if mongo_db is not None:
            await mongo_db.predictions.insert_one({
                "text_snippet": cleaned_text[:500],
                "source": request.url,
                "prediction_result": result,
                "timestamp": datetime.utcnow()
            })
        
        # Add metadata to result
        result["prediction_id"] = prediction_record.id
        result["url"] = request.url
        result["text_snippet"] = PredictionResult.create_snippet(cleaned_text)
        result["title"] = content.get("title", "")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process URL: {str(e)}")

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Check status of a background task
    """
    try:
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None
        }
        
    except Exception as e:
        logger.error(f"Task status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def recent_news():
    return [{"title": "News 1"}, {"title": "News 2"}]

@router.get("/stats")
async def get_stats(db = Depends(get_database)) -> Dict[str, Any]:
    """
    Get prediction statistics
    """
    try:
        if db is None:
            return {"total_predictions": 0}
        
        total = await db.predictions.count_documents({})
        fake_count = await db.predictions.count_documents({"prediction_result.prediction": "FAKE"})
        
        return {
            "total_predictions": total,
            "fake_count": fake_count,
            "real_count": total - fake_count
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def extract_text_from_image(image_file: UploadFile) -> str:
    """
    Extract text from uploaded image using OCR
    """
    try:
        # Read image file
        image_data = image_file.file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Extract text using OCR
        extracted_text = pytesseract.image_to_string(image, lang='eng')
        
        # Clean up the extracted text
        extracted_text = extracted_text.strip()
        
        if not extracted_text:
            raise HTTPException(
                status_code=400, 
                detail="No text could be extracted from the image. Please ensure the image contains readable text."
            )
        
        return extracted_text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to extract text from image: {str(e)}"
        )

@router.post("/predict-image")
async def predict_from_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    mongo_db = Depends(get_database)
) -> Dict[str, Any]:
    """
    Analyze news from uploaded image using OCR
    """
    try:
        # Debug logging
        logger.info(f"Received image file: {file.filename}, type: {file.content_type}")
        
        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'image/bmp']
        if file.content_type not in allowed_types:
            logger.error(f"Invalid file type: {file.content_type}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload an image file (PNG, JPG, JPEG, TIFF, BMP)"
            )
        
        # Extract text from image
        extracted_text = extract_text_from_image(file)
        logger.info(f"Extracted text length: {len(extracted_text)}")
        
        if len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail=f"Extracted text is too short ({len(extracted_text.strip())} characters). Minimum 10 characters required. Please ensure the image contains sufficient readable text."
            )
        
        # Clean extracted text
        cleaned_text = extracted_text.replace('\x00', '').replace('\0', '')
        cleaned_text = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', cleaned_text)
        
        # Limit text length for prediction
        text_for_prediction = cleaned_text
        if len(text_for_prediction) > 20000:
            logger.info(f"Image text length {len(text_for_prediction)} > 20000; truncating")
            text_for_prediction = text_for_prediction[:20000]
        
        # Get prediction from enhanced ML service
        result = final_prediction_service.predict(text_for_prediction, f"Image: {file.filename}")
        
        # Store in PostgreSQL
        prediction_record = PredictionResult(
            text_hash=PredictionResult.create_text_hash(cleaned_text),
            text_content=cleaned_text,
            text_snippet=PredictionResult.create_snippet(cleaned_text),
            source_name=f"Image: {file.filename}",
            prediction=result["prediction"],
            confidence=result["confidence"],
            probabilities=result.get("probabilities"),
            model_version=result.get("model_version"),
            model_type=result.get("model_type")
        )
        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)
        
        # Store in MongoDB
        if mongo_db is not None:
            await mongo_db.predictions.insert_one({
                "text_snippet": cleaned_text[:500],
                "source": f"Image upload: {file.filename}",
                "prediction_result": result,
                "timestamp": datetime.utcnow()
            })
        
        # Add metadata to result
        result["prediction_id"] = prediction_record.id
        result["source"] = f"Image upload: {file.filename}"
        result["text_snippet"] = PredictionResult.create_snippet(cleaned_text)
        result["extracted_text"] = cleaned_text
        
        logger.info(f"Image prediction successful: {result['prediction']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")