from fastapi import FastAPI, Depends, HTTPException, Request, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager
from pydantic import BaseModel
import logging
import time
import uuid
import json
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import joblib
from typing import Dict, Any, Optional, List

# Handle both relative and absolute imports
try:
    from .dependencies.auth import get_current_user
    from .utils.config import get_settings
    from .utils.logger import get_logger
    from .database.mongo_connection import connect_to_mongo, close_mongo_connection
    from .database.postgres_connection import init_db, test_connection
    from .routes import auth_routes_otp, auth_routes
    from .routes.news_route import router as news_router
    from .routes.user_routes import router as user_router
    from .routes.auth_routes import router as auth_router
    from .routes.admin_routes import router as admin_router
    from .routes.dataset_routes import router as dataset_router
    from .routes import profile_routes
    from .middleware.auth_middleware import AuthMiddleware
    from .middleware.logging_middleware import LoggingMiddleware
    from .middleware.error_handler import add_error_handlers
    from .middleware.cors_middleware import add_cors_middleware
    from .services.preprocessing import TextPreprocessor
    from .services.prediction import PredictionService
except ImportError:
    # Fallback to absolute imports
    from dependencies.auth import get_current_user
    from utils.config import get_settings
    from utils.logger import get_logger
    from database.mongo_connection import connect_to_mongo, close_mongo_connection
    from database.postgres_connection import init_db, test_connection
    from routes import auth_routes_otp, auth_routes
    from routes.news_route import router as news_router
    from routes.user_routes import router as user_router
    from routes.auth_routes import router as auth_router
    from routes.admin_routes import router as admin_router
    from routes.dataset_routes import router as dataset_router
    from routes import profile_routes
    from middleware.auth_middleware import AuthMiddleware
    from middleware.logging_middleware import LoggingMiddleware
    from middleware.error_handler import add_error_handlers
    from middleware.cors_middleware import add_cors_middleware
    from services.preprocessing import TextPreprocessor
    from services.prediction import PredictionService
from task_queue.tasks import process_url_task, train_model_task
from ml_core.training_pipeline.data_loader import dataset_loader
from ml_core.training_pipeline.train_model import SimpleModelTrainer


# Setup logging
# setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# In-memory storage for training jobs (production mein database use karein)
training_jobs = {}
trained_models = {}
MODELS_DIR = Path("ml_core/saved_models")
MODELS_DIR.mkdir(exist_ok=True)

# Pydantic models for model routes
class TrainingRequest(BaseModel):
    dataset_id: str
    source_file: Optional[str] = None
    algorithm: str = "random-forest"
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    test_size: float = 0.2
    validation_split: float = 0.1
    model_name: Optional[str] = None

class TrainingProgress(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed, stopped
    progress: float  # 0-100
    current_epoch: Optional[int] = None
    total_epochs: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ModelInfo(BaseModel):
    id: str
    name: str
    algorithm: str
    dataset: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    status: str  # trained, deployed, archived
    created_at: datetime
    training_time: Optional[float] = None
    model_size: Optional[float] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting Fake News Detection API")
    
    try:
        # Initialize MongoDB connection
        await connect_to_mongo()
        logger.info("✅ MongoDB connection established")
        
        # Initialize PostgreSQL database
        init_db()
        if test_connection():
            logger.info("✅ PostgreSQL connection established")
        else:
            logger.warning("⚠️ PostgreSQL connection failed")
        
        # Additional startup tasks
        await perform_startup_checks()
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Fake News Detection API")
    await close_mongo_connection()
    logger.info("✅ MongoDB connection closed")

async def perform_startup_checks():
    """Perform various startup checks and initializations"""
    try:
        # Check if ML models are available (UPDATED)
        from backend.services.prediction import prediction_service
        
        # NEW: Check using new method
        if prediction_service.models:  # Check if any models are loaded
            model_info = prediction_service.get_model_info()
            logger.info(f"✅ ML models loaded: {model_info['available_models']}")
            
            # Test prediction with new method
            test_result = prediction_service.predict("This is a startup test")
            logger.info(f"✅ Test prediction: {test_result['prediction']} (confidence: {test_result['confidence']:.3f})")
        else:
            logger.warning("⚠️ No ML models available, using rule-based mode")
        
        # Check external services
        from data_ingestion.news_api_client import news_api_client

        if getattr(news_api_client, "api_key", None):
            logger.info("✅ News API configured")
        else:
            logger.warning("⚠️ News API not configured")
        
        # ✅ NEW: Check SMS Service
        from backend.services.sms_service import sms_service
        logger.info(f"📱 SMS Service Status: {'✅ ENABLED' if sms_service.is_enabled else '❌ DISABLED'}")
        if sms_service.is_enabled:
            logger.info(f"   Twilio Phone: {sms_service.twilio_phone}")
            logger.info("✅ SMS service is ready for sending messages")
        else:
            logger.warning("❌ SMS service is disabled - check Twilio configuration")
        
        logger.info("✅ All startup checks completed")
        
    except Exception as e:
        logger.warning(f"Startup checks partially failed: {e}")
        
# Create FastAPI application
app = FastAPI(
    title="Fake News Detection API",
    description="A comprehensive API for detecting fake news using machine learning and AI",
    version="2.0.0",
    docs_url=None,  # We'll create custom docs endpoint
    redoc_url="/redoc",
    lifespan=lifespan
)

# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["*"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(news_router, prefix="/api/v1/news", tags=["news"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(user_router, prefix="/api/user", tags=["user"])
app.include_router(dataset_router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(profile_routes.router, prefix="/api/v1")
app.include_router(auth_routes_otp.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/api/v1/debug-sms")
async def debug_sms():
    """Debug SMS service"""
    from backend.services.sms_service import sms_service
    from backend.services.otp_service import otp_service
    
    return {
        "sms_service": {
            "enabled": sms_service.is_enabled,
            "client_available": sms_service.client is not None,
            "twilio_phone": sms_service.twilio_phone
        },
        "otp_service": {
            "sms_service_available": otp_service.sms_service is not None,
            "sms_service_enabled": otp_service.sms_service.is_enabled if otp_service.sms_service else False
        }
    }

@app.get("/api/v1/test-sms")
async def test_sms_endpoint():
    """Test SMS service endpoint"""
    try:
        from backend.services.sms_service import sms_service
        from backend.services.otp_service import otp_service
        
        test_phone = "+918392905339"  # Your test number
        test_name = "SMS Test User"
        
        logger.info(f"Testing SMS service for {test_phone}")
        
        # Test direct SMS service
        sms_result = sms_service.send_otp(test_phone, "123456", test_name)
        
        # Test OTP service integration
        otp_result = otp_service.send_sms_otp(test_phone, test_name)
        
        return {
            "sms_service": {
                "enabled": sms_service.is_enabled,
                "twilio_phone": sms_service.twilio_phone,
                "direct_test": sms_result,
                "via_otp_service": otp_result
            }
        }
        
    except Exception as e:
        logger.error(f"SMS test failed: {e}")
        raise HTTPException(status_code=500, detail=f"SMS test failed: {str(e)}")
@app.get("/api/v1/datasets/", tags=["datasets"])
async def list_datasets():
    return {
        "available_routes": {
            "public": "/api/v1/datasets/public",
            "my": "/api/v1/datasets/my",
            "models": "/api/v1/models/datasets/"
        }
    }

@app.get("/api/v1/datasets/public", tags=["datasets"])
async def get_public_datasets():
    try:
        datasets = ["kaggle_fake.csv", "kaggle_true.csv"]  # or however you load them
        return [{"name": d, "path": f"dataset/raw/{d}"} for d in datasets]
    except Exception as e:
        logger.error(f"Error getting datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading datasets: {e}")

# backend/app.py में

@app.get("/api/v1/datasets/my", tags=["datasets"])
async def get_my_datasets():
    """Get user's datasets - TEMPORARILY PUBLIC"""
    try:
        # Return empty datasets for now
        return {
            "success": True,
            "datasets": [
                {
                    "id": "sample_1",
                    "name": "Sample Dataset 1", 
                    "description": "This is a sample dataset",
                    "dataset_type": "text",
                    "size": "1.2 MB",
                    "records": 1000,
                    "created": "2024-01-01T00:00:00",
                    "status": "active",
                    "file_name": "sample1.csv",
                    "is_public": False
                },
                {
                    "id": "sample_2", 
                    "name": "Sample Dataset 2",
                    "description": "Another sample dataset",
                    "dataset_type": "text", 
                    "size": "2.5 MB",
                    "records": 2500,
                    "created": "2024-01-02T00:00:00",
                    "status": "active",
                    "file_name": "sample2.csv",
                    "is_public": True
                }
            ],
            "total": 2
        }
    except Exception as e:
        logger.error(f"Error getting datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading datasets: {e}")

# Model routes (directly included in app.py)
@app.get("/api/v1/models/datasets/", tags=["models"])
async def get_datasets():
    """Get all available datasets"""
    try:
        datasets_info = dataset_loader.get_dataset_info()
        
        formatted_datasets = []
        
        # Kaggle dataset
        kaggle_fake = datasets_info['file_paths']['kaggle_fake']
        kaggle_true = datasets_info['file_paths']['kaggle_true']
        
        if kaggle_fake['exists'] and kaggle_true['exists']:
            fake_count = get_csv_row_count(Path(kaggle_fake['path']))
            true_count = get_csv_row_count(Path(kaggle_true['path']))
            
            formatted_datasets.append({
                "id": "kaggle",
                "name": "Kaggle Fake News Dataset",
                "type": "binary",
                "description": "General news articles with true/fake labels from Kaggle",
                "labels": ["true", "fake"],
                "files": [
                    {
                        "name": "kaggle_fake.csv", 
                        "samples": fake_count, 
                        "size": get_file_size(Path(kaggle_fake['path']))
                    },
                    {
                        "name": "kaggle_true.csv", 
                        "samples": true_count, 
                        "size": get_file_size(Path(kaggle_true['path']))
                    }
                ],
                "total_samples": fake_count + true_count,
                "total_size": kaggle_fake['size'] + kaggle_true['size'],
                "available": True
            })
        
        # LIAR dataset
        liar_info = datasets_info['file_paths']['liar']
        liar_files = []
        total_liar_samples = 0
        
        for split in ['train', 'test', 'valid']:
            if liar_info[split]['exists']:
                split_path = Path(liar_info[split]['path'])
                sample_count = get_tsv_row_count(split_path)
                liar_files.append({
                    "name": f"{split}.tsv",
                    "samples": sample_count,
                    "size": get_file_size(split_path)
                })
                total_liar_samples += sample_count
        
        if liar_files:
            formatted_datasets.append({
                "id": "liar",
                "name": "LIAR Political Dataset",
                "type": "fine-grained",
                "description": "Political statements with 6-level truth ratings from LIAR dataset",
                "labels": ["true", "mostly-true", "half-true", "barely-true", "false", "pants-fire"],
                "files": liar_files,
                "total_samples": total_liar_samples,
                "total_size": sum(f['size'] for f in liar_files),
                "available": True
            })
        
        return {
            "success": True,
            "datasets": formatted_datasets,
            "total_datasets": len(formatted_datasets)
        }
        
    except Exception as e:
        logger.error(f"Error getting datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading datasets: {str(e)}")

@app.post("/api/v1/models/train", tags=["models"])
async def train_model(training_request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start model training"""
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create training job
        training_job = {
            "id": job_id,
            "status": "pending",
            "progress": 0,
            "request": training_request.dict(),
            "start_time": datetime.now(),
            "end_time": None,
            "metrics": {},
            "model_id": None
        }
        
        training_jobs[job_id] = training_job
        
        # Start training in background
        background_tasks.add_task(
            run_training, 
            job_id, 
            training_request
        )
        
        return {
            "success": True,
            "message": "Training started successfully",
            "training_job": {
                "id": job_id,
                "status": "pending",
                "progress": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting training: {str(e)}")

@app.get("/api/v1/models/training/{training_id}/progress", tags=["models"])
async def get_training_progress(training_id: str):
    """Get training progress"""
    if training_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    job = training_jobs[training_id]
    
    return {
        "success": True,
        "progress": {
            "job_id": training_id,
            "status": job["status"],
            "percentage": job["progress"],
            "current_epoch": job.get("current_epoch"),
            "total_epochs": job.get("total_epochs"),
            "metrics": job.get("metrics", {}),
            "error": job.get("error"),
            "start_time": job["start_time"].isoformat() if job["start_time"] else None,
            "end_time": job["end_time"].isoformat() if job["end_time"] else None
        }
    }

@app.post("/api/v1/models/training/{training_id}/stop", tags=["models"])
async def stop_training(training_id: str):
    """Stop ongoing training"""
    if training_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    job = training_jobs[training_id]
    
    if job["status"] not in ["running", "pending"]:
        raise HTTPException(status_code=400, detail="Training is not running")
    
    job["status"] = "stopped"
    job["progress"] = 0
    job["end_time"] = datetime.now()
    
    return {
        "success": True,
        "message": "Training stopped successfully"
    }

@app.get("/api/v1/models/history", tags=["models"])
async def get_training_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get training history"""
    try:
        # Load from saved models directory
        model_files = list(MODELS_DIR.glob("*.joblib"))
        model_files.extend(list(MODELS_DIR.glob("*.pkl")))
        model_files.extend(list(MODELS_DIR.glob("*.h5")))
        
        models = []
        
        for model_file in model_files[offset:offset+limit]:
            try:
                model_id = model_file.stem
                metadata_file = MODELS_DIR / f"{model_id}_metadata.json"
                
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    model_info = ModelInfo(
                        id=model_id,
                        name=metadata.get('name', f"Model-{model_id}"),
                        algorithm=metadata.get('algorithm', 'unknown'),
                        dataset=metadata.get('dataset', 'unknown'),
                        accuracy=metadata.get('accuracy'),
                        precision=metadata.get('precision'),
                        recall=metadata.get('recall'),
                        f1_score=metadata.get('f1_score'),
                        status=metadata.get('status', 'trained'),
                        created_at=datetime.fromisoformat(metadata.get('created_at')),
                        training_time=metadata.get('training_time'),
                        model_size=model_file.stat().st_size / (1024 * 1024)  # MB
                    )
                    models.append(model_info.dict())
            except Exception as e:
                logger.error(f"Error loading model {model_file}: {e}")
                continue
        
        # Add in-memory trained models
        for model_id, model_data in trained_models.items():
            if model_id not in [m['id'] for m in models]:
                models.append(model_data)
        
        # Sort by creation date (newest first)
        models.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            "success": True,
            "models": models,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(model_files) + len(trained_models),
                "has_more": (offset + limit) < (len(model_files) + len(trained_models))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting training history: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading training history: {str(e)}")

@app.post("/api/v1/models/{model_id}/deploy", tags=["models"])
async def deploy_model(model_id: str):
    """Deploy a trained model"""
    try:
        # Check if model exists
        model_path = MODELS_DIR / f"{model_id}.joblib"
        metadata_path = MODELS_DIR / f"{model_id}_metadata.json"
        
        if not model_path.exists():
            # Check if it's in memory
            if model_id not in trained_models:
                raise HTTPException(status_code=404, detail="Model not found")
            
            # Update in-memory model status
            trained_models[model_id]['status'] = 'deployed'
            
            return {
                "success": True,
                "message": "Model deployed successfully",
                "model_id": model_id
            }
        
        # Update metadata
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['status'] = 'deployed'
            metadata['deployed_at'] = datetime.now().isoformat()
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "message": "Model deployed successfully",
            "model_id": model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        raise HTTPException(status_code=500, detail=f"Error deploying model: {str(e)}")

@app.get("/api/v1/models/{model_id}/download", tags=["models"])
async def download_model(model_id: str):
    """Download model files"""
    try:
        # Check for different model formats
        model_path = None
        for ext in ['.joblib', '.pkl', '.h5']:
            potential_path = MODELS_DIR / f"{model_id}{ext}"
            if potential_path.exists():
                model_path = potential_path
                break
        
        if not model_path:
            raise HTTPException(status_code=404, detail="Model file not found")
        
        # Check metadata
        metadata_path = MODELS_DIR / f"{model_id}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            model_name = metadata.get('name', f"model_{model_id}")
        else:
            model_name = f"model_{model_id}"
        
        return FileResponse(
            path=model_path,
            filename=f"{model_name}{model_path.suffix}",
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading model: {str(e)}")

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

# Health check and monitoring endpoints
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Fake News Detection API",
        "version": "2.0.0",
        "description": "AI-powered fake news detection system",
        "docs": "/docs",
        "health": "/health",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check MongoDB
    try:
        from backend.database.mongo_connection import mongodb
        if mongodb.client:
            await mongodb.client.admin.command('ping')
            health_status["services"]["mongodb"] = "healthy"
        else:
            health_status["services"]["mongodb"] = "unavailable"
    except Exception as e:
        health_status["services"]["mongodb"] = f"unhealthy: {str(e)}"
    
    # Check PostgreSQL
    try:
        health_status["services"]["postgresql"] = "healthy" if test_connection() else "unhealthy"
    except Exception as e:
        health_status["services"]["postgresql"] = f"unhealthy: {str(e)}"
    
    # Check ML model (UPDATED)
    try:
        from backend.services.prediction import prediction_service
        if prediction_service.models:
            health_status["services"]["ml_models"] = {
                "status": "healthy",
                "loaded_models": list(prediction_service.models.keys()),
                "active_model": prediction_service.active_model
            }
        else:
            health_status["services"]["ml_models"] = "no_models_loaded"
    except Exception as e:
        health_status["services"]["ml_models"] = f"unhealthy: {str(e)}"
    
    # If any service is unhealthy, overall status is degraded
    if any("unhealthy" in str(status) for status in health_status["services"].values()):
        health_status["status"] = "degraded"
    if all("unavailable" in str(status) for status in health_status["services"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/status")
async def status_check():
    """
    Detailed system status with statistics
    """
    try:
        from backend.database.mongo_connection import get_database
        from backend.database.postgres_connection import get_db
        from sqlalchemy import func
        
        db = next(get_db())
        
        # Get prediction statistics using proper models
        try:
            from backend.database.models import PredictionResult, User
            total_predictions = db.query(PredictionResult).count()
            fake_predictions = db.query(PredictionResult).filter(
                PredictionResult.prediction == "FAKE"
            ).count()
            total_users = db.query(User).count()
        except ImportError:
            # Fallback if models are not available
            total_predictions = 0
            fake_predictions = 0
            total_users = 0
        
        return {
            "status": "operational",
            "statistics": {
                "total_predictions": total_predictions or 0,
                "fake_predictions": fake_predictions or 0,
                "real_predictions": (total_predictions or 0) - (fake_predictions or 0),
                "total_users": total_users or 0,
                "uptime": time.time() - app.startup_time if hasattr(app, 'startup_time') else 0
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": time.time()
        }
@app.get("/test-cors")
async def test_cors():
    return {"message": "CORS working"}

@app.get("/info")
async def system_info():
    """
    System information and configuration
    """
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "version": "2.0.0",
        "features": {
            "authentication": True,
            "machine_learning": True,
            "real_time_processing": True,
            "database": True,
            "api_docs": True
        },
        "supported_models": [
            "logistic_regression",
            "random_forest",
            "svm",
            "naive_bayes",
            "xgboost"
        ]
    }

# Static files (for serving frontend if needed)
app.mount("/static", StaticFiles(directory="frontend/public/static"), name="static")

# Add startup time
app.startup_time = time.time()

# Background training function
async def run_training(job_id: str, request: TrainingRequest):
    """Run model training in background"""
    try:
        job = training_jobs[job_id]
        job["status"] = "running"
        job["progress"] = 5
        
        logger.info(f"Starting training job {job_id} with algorithm: {request.algorithm}")
        
        # Load dataset based on request
        if request.dataset_id == "kaggle":
            dataset = dataset_loader.load_kaggle_dataset()
            dataset_name = "Kaggle Fake News"
        elif request.dataset_id == "liar":
            dataset = dataset_loader.load_liar_dataset('train')
            dataset_name = "LIAR Dataset"
        else:
            # Load combined dataset
            dataset = dataset_loader.load_combined_dataset(use_liar=True, use_kaggle=True)
            dataset_name = "Combined Dataset"
        
        if dataset is None or len(dataset) == 0:
            raise Exception("Failed to load dataset")
        
        job["progress"] = 20
        
        # Initialize model trainer
        trainer = SimpleModelTrainer()
        
        # Update progress
        job["progress"] = 30
        job["current_epoch"] = 0
        job["total_epochs"] = request.epochs
        
        # Train model using the correct dataset type
        if request.dataset_id == "kaggle":
            model_result = trainer.train_dataset_model('kaggle')
        elif request.dataset_id == "liar":
            model_result = trainer.train_dataset_model('liar')
        else:
            model_result = trainer.train_dataset_model('combined')
        
        job["progress"] = 90
        
        # Save model
        model_id = str(uuid.uuid4())
        model_filename = f"{model_id}.joblib"
        model_path = MODELS_DIR / model_filename
        
        # Save model
        joblib.dump(model_result['model'], model_path)
        
        # Save metadata
        metadata = {
            "id": model_id,
            "name": request.model_name or f"Model-{model_id}",
            "algorithm": request.algorithm,
            "dataset": dataset_name,
            "accuracy": model_result.get('accuracy'),
            "precision": model_result.get('precision'),
            "recall": model_result.get('recall'),
            "f1_score": model_result.get('f1_score'),
            "status": "trained",
            "created_at": datetime.now().isoformat(),
            "training_time": model_result.get('training_time'),
            "parameters": {
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "learning_rate": request.learning_rate,
                "test_size": request.test_size
            }
        }
        
        metadata_path = MODELS_DIR / f"{model_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update job
        job["progress"] = 100
        job["status"] = "completed"
        job["end_time"] = datetime.now()
        job["metrics"] = {
            "accuracy": model_result.get('accuracy'),
            "precision": model_result.get('precision'),
            "recall": model_result.get('recall'),
            "f1_score": model_result.get('f1_score')
        }
        job["model_id"] = model_id
        
        # Store in memory
        trained_models[model_id] = metadata
        
        logger.info(f"Training completed successfully for job {job_id}")
        
    except Exception as e:
        logger.error(f"Training failed for job {job_id}: {e}")
        job = training_jobs[job_id]
        job["status"] = "failed"
        job["error"] = str(e)
        job["end_time"] = datetime.now()

def update_training_progress(job_id: str, progress: float, epoch: int, metrics: Dict[str, Any]):
    """Update training progress"""
    if job_id in training_jobs:
        job = training_jobs[job_id]
        job["progress"] = progress
        job["current_epoch"] = epoch
        job["metrics"] = metrics

# Helper functions
def get_csv_row_count(file_path: Path) -> int:
    """Get approximate row count for CSV file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f) - 1  # Subtract header
    except:
        return 0

def get_tsv_row_count(file_path: Path) -> int:
    """Get approximate row count for TSV file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f)
    except:
        return 0

def get_file_size(file_path: Path) -> str:
    """Get human readable file size"""
    try:
        size_bytes = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    except:
        return "Unknown"

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
        workers=4
    )