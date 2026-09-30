from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from backend.database.postgres_connection import get_db
from backend.database.models import User
from backend.schemas import UserUpdate, SuccessResponse
from backend.utils.password_utils import (
    get_password_hash,
    verify_password,
    validate_password_strength
)
from backend.dependencies.auth import get_current_active_user
from pydantic import BaseModel

# Logger setup
logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("/stats")
async def user_stats():
    """Return simple user stats"""
    return {"total_users": 100, "active_users": 50}


@router.put("/profile", response_model=SuccessResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    try:
        if user_data.full_name:
            current_user.full_name = user_data.full_name

        if user_data.email and user_data.email != current_user.email:
            # Check if new email is already taken
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            current_user.email = user_data.email
            current_user.is_verified = False  # Require re-verification

        db.commit()

        return SuccessResponse(
            success=True,
            message="Profile updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.put("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Validate new password strength
        is_strong, message = validate_password_strength(password_data.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Weak password: {message}"
            )

        # Update password with hash
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.password_changed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Password changed for user: {current_user.email}")

        return SuccessResponse(
            success=True,
            message="Password changed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Password change failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )