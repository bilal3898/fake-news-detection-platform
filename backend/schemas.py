# backend/schemas.py

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class LabelEnum(str, Enum):
    REAL = "real"
    FAKE = "fake"
    UNCERTAIN = "uncertain"

class FeedbackLabel(str, Enum):
    FAKE = "fake"
    REAL = "real"
    UNSURE = "unsure"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AlgorithmType(str, Enum):
    RANDOM_FOREST = "random-forest"
    LOGISTIC_REGRESSION = "logistic-regression"
    SVM = "svm"
    NEURAL_NETWORK = "neural-network"
    LSTM = "lstm"
    BILSTM = "bilstm"

class TrainingStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# User Schemas
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Add more password strength checks if needed
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int

# Auth Schemas
class EmailVerificationRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class ResendOTPRequest(BaseModel):
    email: EmailStr

class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[UserResponse] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    error: Optional[str] = None

class TokenData(BaseModel):
    user_id: int
    email: str
    role: str

# News Article Schemas
class NewsArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=100)
    published_date: Optional[datetime] = None

class NewsArticleCreate(NewsArticleBase):
    pass

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    source: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=100)
    published_date: Optional[datetime] = None
    verified_label: Optional[LabelEnum] = None
    verification_notes: Optional[str] = None
    is_archived: Optional[bool] = None

class NewsArticleResponse(NewsArticleBase):
    id: int
    predicted_label: Optional[LabelEnum] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    prediction_metadata: Optional[Dict[str, Any]] = None
    verified_label: Optional[LabelEnum] = None
    verified_by: Optional[int] = None
    verification_notes: Optional[str] = None
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NewsArticleListResponse(BaseModel):
    articles: List[NewsArticleResponse]
    total: int
    page: int
    size: int

class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1)
    model_version: Optional[str] = None

class PredictionResponse(BaseModel):
    label: LabelEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    prediction_metadata: Optional[Dict[str, Any]] = None

# Feedback Schemas
class UserFeedbackBase(BaseModel):
    article_id: int
    feedback_label: FeedbackLabel
    confidence: Optional[ConfidenceLevel] = None
    notes: Optional[str] = Field(None, max_length=1000)

class UserFeedbackCreate(UserFeedbackBase):
    pass

class UserFeedbackResponse(UserFeedbackBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Training Schemas
class TrainingSessionBase(BaseModel):
    algorithm: AlgorithmType
    parameters: Optional[Dict[str, Any]] = None

class TrainingSessionCreate(TrainingSessionBase):
    pass

class TrainingSessionResponse(BaseModel):
    id: int
    user_id: Optional[int]
    algorithm: AlgorithmType
    dataset_size: int
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_time: Optional[float] = None
    status: TrainingStatus
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TrainingSessionListResponse(BaseModel):
    sessions: List[TrainingSessionResponse]
    total: int
    page: int
    size: int

class TrainingParameters(BaseModel):
    test_size: float = Field(0.2, ge=0.1, le=0.5)
    epochs: int = Field(10, ge=1, le=1000)
    batch_size: int = Field(32, ge=1, le=1024)
    learning_rate: float = Field(0.001, ge=0.0001, le=1.0)

# Model Version Schemas
class ModelVersionBase(BaseModel):
    version_name: str = Field(..., min_length=1, max_length=50)
    algorithm: AlgorithmType
    parameters: Optional[Dict[str, Any]] = None

class ModelVersionCreate(ModelVersionBase):
    pass

class ModelVersionResponse(ModelVersionBase):
    id: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    is_active: bool
    training_data_size: int
    created_at: datetime

    class Config:
        from_attributes = True

class ModelVersionListResponse(BaseModel):
    models: List[ModelVersionResponse]
    total: int
    page: int
    size: int

# Generic Response Schemas
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool
    error: str
    details: Optional[Dict[str, Any]] = None

# Pagination Schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class SearchParams(PaginationParams):
    query: Optional[str] = None
    source: Optional[str] = None
    label: Optional[LabelEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None