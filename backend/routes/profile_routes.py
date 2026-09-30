# backend/routes/profile_routes.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import logging
import shutil
from pathlib import Path

from backend.database.postgres_connection import get_db
from backend.database.models import User, UserProfile, UserActivity
from backend.dependencies.auth import get_current_user

router = APIRouter(tags=["profile"])
logger = logging.getLogger(__name__)

# Profile storage
AVATARS_DIR = Path("user_avatars")
AVATARS_DIR.mkdir(exist_ok=True)

# Pydantic Models
class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None

class ProfessionalInfo(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    expertise: List[str] = []
    experience: Optional[str] = None

class Preferences(BaseModel):
    language: str = "en"
    timezone: str = "UTC+5:30"
    notifications: bool = True
    newsletter: bool = True
    theme: str = "light"

class ProfileUpdate(BaseModel):
    personal: PersonalInfo
    professional: ProfessionalInfo
    preferences: Preferences

class ProfileResponse(BaseModel):
    personal: PersonalInfo
    professional: ProfessionalInfo
    preferences: Preferences
    stats: Dict[str, Any]

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    try:
        user_id = current_user["id"]
        
        # Get user basic info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get or create profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            # Create default profile
            profile = UserProfile(
                user_id=user_id,
                personal_info=json.dumps({
                    "name": user.full_name,
                    "email": user.email,
                    "phone": "",
                    "location": "",
                    "bio": ""
                }),
                professional_info=json.dumps({
                    "company": "",
                    "role": "",
                    "expertise": [],
                    "experience": ""
                }),
                preferences=json.dumps({
                    "language": "en",
                    "timezone": "UTC+5:30",
                    "notifications": True,
                    "newsletter": True,
                    "theme": "light"
                })
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # Parse profile data
        personal_info = json.loads(profile.personal_info)
        professional_info = json.loads(profile.professional_info)
        preferences = json.loads(profile.preferences)
        
        # Calculate stats (you can replace with actual stats from your database)
        stats = {
            "analyses": db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.activity_type == "analysis"
            ).count(),
            "models_trained": db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.activity_type == "training"
            ).count(),
            "datasets_uploaded": db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.activity_type == "upload"
            ).count(),
            "accuracy": 94.2  # This would come from your model performance data
        }
        
        return ProfileResponse(
            personal=PersonalInfo(**personal_info),
            professional=ProfessionalInfo(**professional_info),
            preferences=Preferences(**preferences),
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to load profile")

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    try:
        user_id = current_user["id"]
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update profile data
        profile.personal_info = json.dumps(profile_data.personal.dict())
        profile.professional_info = json.dumps(profile_data.professional.dict())
        profile.preferences = json.dumps(profile_data.preferences.dict())
        profile.updated_at = datetime.now()
        
        db.commit()
        
        # Log activity
        activity = UserActivity(
            user_id=user_id,
            activity_type="profile_update",
            description="Updated profile information",
            metadata=json.dumps({"section": "profile"})
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload user avatar"""
    try:
        user_id = current_user["id"]
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only JPEG, PNG and GIF images are allowed")
        
        # Validate file size (max 5MB)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to start
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")
        
        # Generate filename
        file_extension = file.filename.split('.')[-1]
        filename = f"{user_id}.{file_extension}"
        file_path = AVATARS_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update profile with avatar path
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            profile.avatar_path = str(file_path)
            db.commit()
        
        return {
            "success": True,
            "message": "Avatar uploaded successfully",
            "avatar_url": f"/api/v1/profile/avatar/{filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")

@router.get("/profile/avatar/{filename}")
async def get_avatar(filename: str):
    """Get user avatar"""
    try:
        file_path = AVATARS_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Avatar not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to get avatar")

@router.get("/profile/activity")
async def get_activity(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get user activity history"""
    try:
        user_id = current_user["id"]
        
        activities = db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(UserActivity.created_at.desc()).limit(limit).all()
        
        activity_list = []
        for activity in activities:
            activity_list.append({
                "id": activity.id,
                "action": activity.description,
                "type": activity.activity_type,
                "time": activity.created_at.isoformat(),
                "metadata": json.loads(activity.metadata) if activity.metadata else {}
            })
        
        return {
            "success": True,
            "activities": activity_list
        }
        
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to load activity")

@router.get("/profile/stats")
async def get_profile_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed profile statistics"""
    try:
        user_id = current_user["id"]
        
        # Calculate various stats
        total_analyses = db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == "analysis"
        ).count()
        
        total_models = db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == "training"
        ).count()
        
        total_datasets = db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == "upload"
        ).count()
        
        # This would come from your actual model performance data
        accuracy_data = {
            "overall": 94.2,
            "last_week": 92.8,
            "trend": "improving"
        }
        
        return {
            "success": True,
            "stats": {
                "analyses": total_analyses,
                "models_trained": total_models,
                "datasets_uploaded": total_datasets,
                "accuracy": accuracy_data,
                "active_days": 45,  # This would be calculated from activity
                "recent_activity": "high"  # low, medium, high
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to load statistics")