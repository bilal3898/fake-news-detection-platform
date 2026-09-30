# backend/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import secrets
import string
from bson import ObjectId

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.database.mongo_connection import get_database
from backend.utils.config import get_settings
from backend.services.email_service import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)
router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Get settings
settings = get_settings()

# Pydantic models with MongoDB compatibility
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: str = Field(..., alias="_id")
    email: str
    full_name: str
    is_verified: bool
    is_active: bool
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def validate_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class VerificationRequest(BaseModel):
    token: str

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def generate_verification_token() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def generate_password_reset_token() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))

# MongoDB dependency
async def get_database_connection():
    db = await get_database()
    return db

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database_connection)
) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    users_collection = db["users"]
    user = await users_collection.find_one({"_id": ObjectId(token_data.user_id)})
    if user is None:
        raise credentials_exception
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@router.post("/register", response_model=Dict[str, Any])
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_database_connection)
):
    """
    Register a new user in MongoDB
    """
    users_collection = db["users"]
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user document
    hashed_password = get_password_hash(user_data.password)
    verification_token = generate_verification_token()
    
    user_doc = {
        "email": user_data.email,
        "hashed_password": hashed_password,
        "full_name": user_data.full_name,
        "verification_token": verification_token,
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "refresh_token": None,
        "reset_token": None,
        "reset_token_expires": None
    }
    
    result = await users_collection.insert_one(user_doc)
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        user_data.email,
        user_data.full_name,
        verification_token
    )
    
    return {
        "message": "User registered successfully. Please check your email for verification.",
        "user_id": str(result.inserted_id)
    }

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_database_connection)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"]},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user["_id"])}
    )
    
    # Store refresh token in database
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"refresh_token": refresh_token}}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db = Depends(get_database_connection)
):
    """
    Refresh access token using refresh token
    """
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        users_collection = db["users"]
        user = await users_collection.find_one({
            "_id": ObjectId(user_id), 
            "refresh_token": refresh_token
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/verify-email")
async def verify_email(
    verification_data: VerificationRequest,
    db = Depends(get_database_connection)
):
    """
    Verify user email with verification token
    """
    users_collection = db["users"]
    
    user = await users_collection.find_one({"verification_token": verification_data.token})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_verified": True, "verification_token": None}}
    )
    
    return {"message": "Email verified successfully"}

@router.post("/request-password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database_connection)
):
    """
    Request password reset email
    """
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": reset_data.email})
    if user:
        reset_token = generate_password_reset_token()
        reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "reset_token": reset_token,
                "reset_token_expires": reset_token_expires
            }}
        )
        
        # Send password reset email in background
        background_tasks.add_task(
            send_password_reset_email,
            user["email"],
            user["full_name"],
            reset_token
        )
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db = Depends(get_database_connection)
):
    """
    Reset password with reset token
    """
    users_collection = db["users"]
    
    user = await users_collection.find_one({
        "reset_token": reset_data.token,
        "reset_token_expires": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    hashed_password = get_password_hash(reset_data.new_password)
    
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "hashed_password": hashed_password,
            "reset_token": None,
            "reset_token_expires": None
        }}
    )
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return UserResponse(**current_user)

@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db = Depends(get_database_connection)
):
    """
    Logout user by invalidating refresh token
    """
    users_collection = db["users"]
    
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"refresh_token": None}}
    )
    
    return {"message": "Logged out successfully"}