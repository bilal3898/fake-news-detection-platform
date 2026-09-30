# backend/routes/auth_routes_otp.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import secrets
import string
from sqlalchemy.orm import Session
from fastapi import Request
from fastapi.responses import JSONResponse

from backend.database.postgres_connection import get_db
from backend.database.models import User
from backend.utils.config import get_settings
from backend.services.otp_service import otp_service
from backend.utils.password_utils import get_password_hash, verify_password

logger = logging.getLogger(__name__)
router = APIRouter()

# Get settings
settings = get_settings()

# Pydantic models for dual OTP registration
class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')  
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class SendOTPRequest(BaseModel):
    email: EmailStr
    phone_number: Optional[str] = None
    full_name: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    email_otp: str = Field(..., min_length=6, max_length=6)
    phone_number: Optional[str] = None
    sms_otp: Optional[str] = Field(None, min_length=6, max_length=6)

class CompleteRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None
    email_otp: str
    sms_otp: Optional[str] = None

class OTPResponse(BaseModel):
    message: str
    email_sent: bool
    sms_sent: bool
    sms_enabled: bool
    expires_in_minutes: int = 5

class RegistrationResponse(BaseModel):
    message: str
    user_id: int
    email_verified: bool
    phone_verified: bool

# Safe error handler for Pydantic validation errors
def safe_handle_validation_error(e):
    """Safely convert Pydantic validation errors to string messages"""
    error_messages = []
    for error in e.errors():
        field = " -> ".join(str(loc) for loc in error.get('loc', []))
        message = error.get('msg', 'Invalid value')
        error_messages.append(f"{field}: {message}")
    
    return "; ".join(error_messages)

# Fixed OTP sending logic - extract boolean from dictionary response
@router.post("/register/request-otp", response_model=OTPResponse)
async def request_registration_otp(
    request: SendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Step 1: Request OTP for registration (both email and SMS if phone provided)
    """
    try:
        # Check if user already exists using raw SQL to avoid ORM issues
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id, email, is_verified FROM users WHERE email = :email"),
            {"email": request.email}
        )
        existing_user = result.fetchone()
        
        if existing_user and existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists and is verified"
            )
        
        # Send email OTP - this returns a dictionary, extract the boolean
        email_result = otp_service.send_email_otp(request.email, request.full_name, db)
        email_sent = email_result.get("success", False)  # Extract boolean from dictionary
        
        # Send SMS OTP if phone number provided AND it's a valid phone number
        sms_sent = False
        sms_enabled = False
        sms_development_otp = None
        
        if request.phone_number:
            # Validate phone number format
            if request.phone_number.startswith('+') and request.phone_number[1:].isdigit():
                sms_result = otp_service.send_sms_otp(request.phone_number, request.full_name)
                sms_sent = sms_result.get("success", False)  # Extract boolean from dictionary
                sms_enabled = True
                sms_development_otp = sms_result.get("sms_development_otp")
                logger.info(f"SMS OTP requested for phone: {request.phone_number}, Success: {sms_sent}")
            else:
                logger.warning(f"Invalid phone number format: {request.phone_number}")
                sms_enabled = True  # Still mark as enabled but not sent
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email OTP"
            )
        
        # Create response with development OTPs included
        response_data = {
            "message": "OTP codes sent successfully",
            "email_sent": email_sent,  # This is now a boolean
            "sms_sent": sms_sent,      # This is now a boolean
            "sms_enabled": sms_enabled,
            "expires_in_minutes": 5
        }
        
        # Add development OTPs if available
        if email_result.get("development_otp"):
            response_data["development_otp"] = email_result.get("development_otp")
        if sms_development_otp:
            response_data["sms_development_otp"] = sms_development_otp
            
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send OTP for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP codes"
        )

# In your auth_routes_otp.py, update the verify-otp endpoint:

@router.post("/register/verify-otp")
async def verify_registration_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Step 2: Verify OTP codes (both email and SMS if provided)
    """
    try:
        logger.info(f"🔐 OTP Verification Request: email={request.email}, phone={request.phone_number}")
        logger.info(f"📧 Email OTP received: {request.email_otp}")
        if request.sms_otp:
            logger.info(f"📱 SMS OTP received: {request.sms_otp}")
        
        # Verify email OTP (required)
        email_verified = otp_service.verify_email_otp(request.email, request.email_otp)
        
        if not email_verified:
            logger.error(f"❌ Email OTP verification failed for {request.email}")
            return {
                "success": False,
                "verified": False,
                "ready_for_registration": False,
                "message": "Invalid or expired email OTP",
                "email_verified": False,
                "phone_verified": False
            }
        
        # Verify SMS OTP if phone number and OTP provided
        sms_verified = True  # Default to true if no SMS verification required
        if request.phone_number and request.sms_otp:
            sms_verified = otp_service.verify_sms_otp(request.phone_number, request.sms_otp)
            
            if not sms_verified:
                logger.error(f"❌ SMS OTP verification failed for {request.phone_number}")
                return {
                    "success": False,
                    "verified": False,
                    "ready_for_registration": False,
                    "message": "Invalid SMS OTP",
                    "email_verified": False,
                    "phone_verified": False
                }
        
        logger.info(f"✅ OTP verification successful for {request.email}")
        return {
            "success": True,
            "verified": True,
            "ready_for_registration": True,
            "message": "OTP verification successful",
            "email_verified": email_verified,
            "phone_verified": sms_verified
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to verify OTP for {request.email}: {e}")
        return {
            "success": False,
            "verified": False,
            "ready_for_registration": False,
            "message": "OTP verification failed",
            "email_verified": False,
            "phone_verified": False
        }

# backend/routes/auth_routes_otp.py
@router.post("/register/complete")
async def complete_registration(
    request: CompleteRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Step 3: Complete registration after OTP verification
    """
    try:
        logger.info(f"🚀 Completing registration for: {request.email}")
        
        # ✅ REMOVE OTP VERIFICATION - They were already verified in step 2
        # Just proceed with registration since OTPs were already validated
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user and existing_user.is_verified:
            logger.error(f"❌ User already exists and is verified: {request.email}")
            return {
                "success": False,
                "message": "User already exists and is verified",
                "user_id": None,
                "email_verified": False,
                "phone_verified": False
            }
        
        # Hash password - ensure we're using the correct password
        # Strip password to remove any accidental whitespace
        clean_password = request.password.strip()
        logger.info(f"🔐 Hashing password for user: {request.email}")
        logger.debug(f"   Password length: {len(clean_password)}")
        hashed_password = get_password_hash(clean_password)
        logger.info(f"✅ Password hashed successfully (hash length: {len(hashed_password)})")
        
        if existing_user:
            # Update existing unverified user
            logger.info(f"🔄 Updating existing user: {request.email}")
            existing_user.hashed_password = hashed_password
            existing_user.full_name = request.full_name
            existing_user.is_verified = True
            existing_user.verified_at = datetime.utcnow()
            user = existing_user
        else:
            # Create new user
            logger.info(f"🆕 Creating new user: {request.email}")
            user = User(
                email=request.email,
                hashed_password=hashed_password,
                full_name=request.full_name,
                is_verified=True,
                verified_at=datetime.utcnow(),
                is_active=True
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        # Verify password was stored correctly (use cleaned password)
        test_verify = verify_password(clean_password, user.hashed_password)
        logger.info(f"🧪 Password verification test after registration: {test_verify}")
        if not test_verify:
            logger.error(f"❌ CRITICAL: Password verification failed immediately after registration for {request.email}")
            logger.error(f"   This indicates a serious issue with password hashing/verification")
        
        # ✅ Clean up any remaining OTPs (they should already be deleted from verification)
        if request.email in otp_service.otp_storage:
            del otp_service.otp_storage[request.email]
            logger.info(f"✅ Cleaned up email OTP for {request.email}")
        if request.phone_number and request.phone_number in otp_service.otp_storage:
            del otp_service.otp_storage[request.phone_number]
            logger.info(f"✅ Cleaned up SMS OTP for {request.phone_number}")
        
        logger.info(f"✅ User registered successfully: {request.email}")
        
        return {
            "success": True,
            "message": "Registration completed successfully",
            "user_id": user.id,
            "email_verified": True,
            "phone_verified": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to complete registration for {request.email}: {e}")
        db.rollback()
        return {
            "success": False,
            "message": "Registration failed",
            "user_id": None,
            "email_verified": False,
            "phone_verified": False
        }

@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint that requires verified users
    """
    try:
        logger.info(f"Login attempt for email: {form_data.username}")
        
        user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user:
            logger.warning(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password - strip to handle any whitespace issues
        clean_login_password = form_data.password.strip()
        logger.info(f"🔐 Verifying password for user: {form_data.username}")
        logger.debug(f"   Password length: {len(clean_login_password)}")
        logger.debug(f"   Password hash length: {len(user.hashed_password) if user.hashed_password else 0}")
        logger.debug(f"   Password hash prefix: {user.hashed_password[:20] if user.hashed_password else 'None'}...")
        
        password_verified = verify_password(clean_login_password, user.hashed_password)
        logger.info(f"   Password verification result: {password_verified}")
        
        if not password_verified:
            logger.warning(f"❌ Invalid password for user: {form_data.username}")
            logger.debug(f"   Attempted password (first 3 chars, length {len(clean_login_password)}): {clean_login_password[:3]}...")
            logger.debug(f"   Stored hash (first 30 chars): {user.hashed_password[:30] if user.hashed_password else 'None'}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Account deactivated: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is deactivated"
            )
        
        if not user.is_verified:
            logger.warning(f"Account not verified: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is not verified. Please complete registration with OTP verification."
            )
        
        # Create access token
        from backend.routes.auth_routes import create_access_token, create_refresh_token
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        
        logger.info(f"Login successful for: {form_data.username}")
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified
            }
        }
        
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except Exception as e:
        logger.error(f"Login failed for {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

# Add email check endpoint
class EmailCheckRequest(BaseModel):
    email: EmailStr

@router.post("/check-email")
async def check_email_exists(
    request: EmailCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check if email already exists and is verified
    """
    try:
        existing_user = db.query(User).filter(User.email == request.email).first()
        
        if existing_user:
            return {
                "exists": True,
                "verified": existing_user.is_verified
            }
        else:
            return {"exists": False, "verified": False}
            
    except Exception as e:
        logger.error(f"Error checking email: {e}")
        return {"exists": False, "verified": False}

# REMOVED: The problematic exception handler that was causing the error
# @router.exception_handler(Exception)  # This line was causing the AttributeError
# async def global_exception_handler(request: Request, exc: Exception):
#     """Global exception handler to catch all unhandled exceptions"""
#     logger.error(f"Global exception handler: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "success": False,
#             "message": "An internal server error occurred",
#             "error": str(exc)
#         }
#     )