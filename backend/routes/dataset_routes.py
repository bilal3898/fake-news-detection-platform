# backend/routes/dataset_routes.py
# backend/routes/dataset_routes.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
from pathlib import Path
import uuid
import json
import shutil
import logging
from datetime import datetime
import os

# Add this import for authentication
from backend.dependencies.auth import get_current_user

router = APIRouter(tags=["datasets"])
logger = logging.getLogger(__name__)

# Dataset storage paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "user_datasets"
DATASETS_DIR.mkdir(exist_ok=True)

# Pydantic models
class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_type: str = "text"
    is_public: bool = False

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    dataset_type: str
    size: str
    records: int
    created: str
    status: str
    file_name: str
    is_public: bool
    user_id: Optional[str] = None

class PublicDataset(BaseModel):
    id: str
    name: str
    description: str
    dataset_type: str
    size: str
    records: int
    source: str
    rating: float
    downloads: int
    file_name: str

# In-memory storage (production mein database use karein)
user_datasets = {}
public_datasets = {}

@router.get("/datasets/my")
async def get_my_datasets(current_user: dict = Depends(get_current_user)):
    """Get user's datasets"""
    try:
        user_id = current_user.get("id", "default_user")
        user_dir = DATASETS_DIR / user_id
        datasets = []
        
        if user_dir.exists():
            for dataset_file in user_dir.glob("*.json"):
                try:
                    with open(dataset_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Check if data file exists
                    data_file = user_dir / metadata['file_name']
                    if data_file.exists():
                        datasets.append(DatasetResponse(**metadata))
                    else:
                        logger.warning(f"Data file missing for dataset {metadata['id']}")
                except Exception as e:
                    logger.error(f"Error loading dataset {dataset_file}: {e}")
        
        # Add any in-memory datasets
        if user_id in user_datasets:
            datasets.extend(user_datasets[user_id])
        
        return {
            "success": True,
            "datasets": datasets,
            "total": len(datasets)
        }
        
    except Exception as e:
        logger.error(f"Error getting user datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading datasets: {str(e)}")

@router.get("/datasets/public")
async def get_public_datasets():
    """Get public datasets - No authentication required"""
    try:
        public_dir = DATASETS_DIR / "public"
        datasets = []
        
        if public_dir.exists():
            for dataset_file in public_dir.glob("*.json"):
                try:
                    with open(dataset_file, 'r') as f:
                        metadata = json.load(f)
                    
                    datasets.append(PublicDataset(**metadata))
                except Exception as e:
                    logger.error(f"Error loading public dataset {dataset_file}: {e}")
        
        # Add default public datasets
        default_datasets = [
            {
                "id": "kaggle_fake_news",
                "name": "Fake News Challenge Dataset",
                "description": "Comprehensive dataset for fake news detection from Kaggle",
                "dataset_type": "text",
                "size": "15.2 MB",
                "records": 50000,
                "source": "Kaggle",
                "rating": 4.8,
                "downloads": 12450,
                "file_name": "kaggle_fake_news.csv"
            },
            {
                "id": "liar_dataset",
                "name": "LIAR Political Statements",
                "description": "Political statements with truth ratings for fake news analysis",
                "dataset_type": "text",
                "size": "8.7 MB",
                "records": 32000,
                "source": "LIAR Project",
                "rating": 4.6,
                "downloads": 8920,
                "file_name": "liar_dataset.tsv"
            }
        ]
        
        datasets.extend(default_datasets)
        
        return {
            "success": True,
            "datasets": datasets,
            "total": len(datasets)
        }
        
    except Exception as e:
        logger.error(f"Error getting public datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading public datasets: {str(e)}")

# Other routes remain the same but add Depends(get_current_user) to protected ones
@router.post("/datasets/upload")
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    dataset_type: str = Form("text"),
    is_public: bool = Form(False),
    current_user: dict = Depends(get_current_user)
):
    """Upload a new dataset"""
    try:
        user_id = current_user.get("id", "default_user")
        
        # Validate file type
        allowed_extensions = ['.csv', '.json', '.txt', '.tsv']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported. Use: {', '.join(allowed_extensions)}"
            )
        
        # Create user directory
        user_dir = DATASETS_DIR / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Generate unique ID
        dataset_id = str(uuid.uuid4())
        file_name = f"{dataset_id}{file_extension}"
        file_path = user_dir / file_name
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Analyze dataset
        records_count = await analyze_dataset(file_path, file_extension)
        file_size = get_file_size(file_path)
        
        # Create metadata
        metadata = {
            "id": dataset_id,
            "name": name,
            "description": description,
            "dataset_type": dataset_type,
            "size": file_size,
            "records": records_count,
            "created": datetime.now().isoformat(),
            "status": "active",
            "file_name": file_name,
            "is_public": is_public,
            "user_id": user_id
        }
        
        # Save metadata
        metadata_file = user_dir / f"{dataset_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # If public, also save to public directory
        if is_public:
            public_dir = DATASETS_DIR / "public"
            public_dir.mkdir(exist_ok=True)
            public_metadata_file = public_dir / f"{dataset_id}.json"
            with open(public_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"Dataset uploaded successfully: {dataset_id}")
        
        return {
            "success": True,
            "message": "Dataset uploaded successfully",
            "dataset": DatasetResponse(**metadata)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Similarly update other protected routes with Depends(get_current_user)
@router.get("/datasets/{dataset_id}/download")
async def download_dataset(
    dataset_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Download dataset file"""
    try:
        user_id = current_user.get("id", "default_user")
        user_dir = DATASETS_DIR / user_id
        metadata_file = user_dir / f"{dataset_id}.json"
        
        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        file_path = user_dir / metadata['file_name']
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Increment download count for public datasets
        if metadata.get('is_public'):
            public_dir = DATASETS_DIR / "public"
            public_metadata_file = public_dir / f"{dataset_id}.json"
            if public_metadata_file.exists():
                with open(public_metadata_file, 'r') as f:
                    public_metadata = json.load(f)
                public_metadata['downloads'] = public_metadata.get('downloads', 0) + 1
                with open(public_metadata_file, 'w') as f:
                    json.dump(public_metadata, f, indent=2)
        
        return FileResponse(
            path=file_path,
            filename=metadata['file_name'],
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, user_id: str = "default_user", limit: int = 10):
    """Preview dataset data"""
    try:
        user_dir = DATASETS_DIR / user_id
        metadata_file = user_dir / f"{dataset_id}.json"
        
        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        file_path = user_dir / metadata['file_name']
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read data based on file type
        file_extension = Path(file_path).suffix.lower()
        data = await read_dataset_preview(file_path, file_extension, limit)
        
        return {
            "success": True,
            "dataset": metadata,
            "preview": data,
            "total_records": metadata['records']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, user_id: str = "default_user"):
    """Delete a dataset"""
    try:
        user_dir = DATASETS_DIR / user_id
        metadata_file = user_dir / f"{dataset_id}.json"
        
        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Delete data file
        file_path = user_dir / metadata['file_name']
        if file_path.exists():
            file_path.unlink()
        
        # Delete metadata file
        metadata_file.unlink()
        
        # Delete from public if exists
        public_dir = DATASETS_DIR / "public"
        public_metadata_file = public_dir / f"{dataset_id}.json"
        if public_metadata_file.exists():
            public_metadata_file.unlink()
        
        return {
            "success": True,
            "message": "Dataset deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# Helper functions
async def analyze_dataset(file_path: Path, file_extension: str) -> int:
    """Analyze dataset file and return record count"""
    try:
        if file_extension == '.csv':
            df = pd.read_csv(file_path, nrows=1000)  # Read first 1000 rows for speed
            return len(df)
        elif file_extension in ['.json', '.txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_extension == '.json':
                    data = json.load(f)
                    if isinstance(data, list):
                        return len(data)
                    else:
                        return 1
                else:
                    return sum(1 for _ in f)
        elif file_extension == '.tsv':
            df = pd.read_csv(file_path, sep='\t', nrows=1000)
            return len(df)
        else:
            return 0
    except Exception as e:
        logger.error(f"Error analyzing dataset: {e}")
        return 0

async def read_dataset_preview(file_path: Path, file_extension: str, limit: int = 10):
    """Read preview of dataset"""
    try:
        if file_extension == '.csv':
            df = pd.read_csv(file_path, nrows=limit)
            return df.fillna('').to_dict('records')
        elif file_extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data[:limit]
                else:
                    return [data]
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()[:limit]]
                return [{"text": line} for line in lines]
        elif file_extension == '.tsv':
            df = pd.read_csv(file_path, sep='\t', nrows=limit)
            return df.fillna('').to_dict('records')
        else:
            return []
    except Exception as e:
        logger.error(f"Error reading dataset preview: {e}")
        return []

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