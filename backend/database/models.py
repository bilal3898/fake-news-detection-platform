# backend/models.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
import hashlib
from datetime import datetime, timedelta
import uuid
import logging

from backend.utils.password_utils import (
    validate_password_strength,
    PasswordPolicy,
    default_policy
)

logger = logging.getLogger(__name__)
Base = declarative_base()

class User(Base):
    """
    User model for authentication and user management with enhanced security
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    # REMOVED role column as it doesn't exist in database
    
    # Timestamps and login info
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Security fields
    verification_token = Column(String(255), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    refresh_token = Column(Text, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    feedback = relationship("UserFeedback", back_populates="user")
    training_jobs = relationship("TrainingJob", back_populates="user")
    trained_models = relationship("TrainedModel", back_populates="user")
    api_logs = relationship("APILog", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    activities = relationship("UserActivity", back_populates="user")

    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower().strip()

    def set_password(self, password: str):
        """Set password with validation and hashing"""
        from backend.utils.password_utils import validate_password_strength, get_password_hash
        
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            raise ValueError(f"Weak password: {message}")
        
        self.hashed_password = get_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        
    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        from backend.utils.password_utils import verify_password
        return verify_password(password, self.hashed_password)
    
    def is_password_expired(self) -> bool:
        """Check if password needs to be changed"""
        if not self.password_changed_at:
            return False
        expiry_date = self.password_changed_at + timedelta(days=default_policy.max_age_days)
        return datetime.utcnow() > expiry_date
    
    def can_login(self) -> bool:
        """Check if user can login"""
        if not self.is_active:
            return False
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return False
        if not self.is_verified:
            return False
        return True
    
    def record_failed_login(self):
        """Record failed login attempt and lock account if needed"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        self.updated_at = datetime.utcnow()
    
    def reset_login_attempts(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }


class UserProfile(Base):
    """
    Extended user profile information
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, index=True)
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Professional information (JSON)
    professional_info = Column(JSONB, nullable=True)  # {company, position, expertise}
    
    # Preferences (JSON)
    preferences = Column(JSONB, nullable=True)  # {notifications, theme, language}
    
    # Statistics
    total_predictions = Column(Integer, default=0)
    total_feedback = Column(Integer, default=0)
    accuracy_contribution = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")


class UserActivity(Base):
    """
    Track user activities and interactions
    """
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    activity_type = Column(String(50), nullable=False)  # login, prediction, feedback, training
    description = Column(String(255), nullable=False)
    activity_metadata = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="activities")


class EmailVerification(Base):
    """
    Model for storing email verification OTPs
    """
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PredictionResult(Base):
    """
    Model for storing prediction results with enhanced tracking
    """
    __tablename__ = "prediction_results"
    
    id = Column(Integer, primary_key=True, index=True)
    text_hash = Column(String(64), index=True, nullable=False)
    text_content = Column(Text, nullable=False)
    text_snippet = Column(String(500), nullable=False)  # First 500 chars for display
    
    # Source information
    source_domain = Column(String(200), nullable=True)
    source_name = Column(String(200), nullable=True)
    author = Column(String(200), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    url = Column(Text, nullable=True)
    
    # Prediction results
    prediction = Column(String(20), nullable=False)  # 'fake', 'real', 'uncertain', 'unable_to_analyze'
    confidence = Column(Float, nullable=False)
    probabilities = Column(JSONB, nullable=True)  # {fake: 0.8, real: 0.2}
    
    # Model information
    model_version = Column(String(50), nullable=True)
    model_type = Column(String(50), nullable=True)
    model_metadata = Column(JSONB, nullable=True)  # Additional model info
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Analytics
    view_count = Column(Integer, default=0)
    feedback_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    feedback = relationship("UserFeedback", back_populates="prediction")
    verified_by_user = relationship("User", foreign_keys=[verified_by])

    @classmethod
    def create_text_hash(cls, text: str) -> str:
        """Create SHA256 hash of text for deduplication"""
        return hashlib.sha256(text.strip().encode()).hexdigest()

    @classmethod
    def create_snippet(cls, text: str, max_length: int = 500) -> str:
        """Create snippet from text"""
        text = text.strip()
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'


class UserFeedback(Base):
    """
    Enhanced model for storing user feedback on predictions
    """
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("prediction_results.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Feedback details
    is_correct = Column(Boolean, nullable=False)
    user_judgment = Column(String(10), nullable=False)  # 'fake', 'real'
    confidence = Column(String(10), nullable=True)  # 'low', 'medium', 'high'
    comments = Column(Text, nullable=True)
    
    # Feedback metadata
    source = Column(String(50), nullable=True)  # 'web', 'api', 'mobile'
    user_context = Column(JSONB, nullable=True)  # Additional user context
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    prediction = relationship("PredictionResult", back_populates="feedback")
    user = relationship("User", back_populates="feedback")


class NewsSource(Base):
    """
    Enhanced model for tracking news source reliability
    """
    __tablename__ = "news_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(200), unique=True, index=True, nullable=False)
    source_name = Column(String(200), nullable=True)
    
    # Reliability metrics
    reliability_score = Column(Float, default=0.5)
    credibility_rating = Column(String(20), default='unknown')  # high, medium, low, unknown
    
    # Statistics
    total_predictions = Column(Integer, default=0)
    fake_count = Column(Integer, default=0)
    real_count = Column(Integer, default=0)
    average_confidence = Column(Float, default=0.0)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verification_source = Column(String(200), nullable=True)  # URL or reference
    
    # Metadata
    country = Column(String(100), nullable=True)
    language = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)  # news, blog, social_media
    
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelPerformance(Base):
    """
    Enhanced model for tracking ML model performance metrics
    """
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)
    
    # Core metrics
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    
    # Additional metrics
    auc_roc = Column(Float, nullable=True)
    log_loss = Column(Float, nullable=True)
    confusion_matrix = Column(JSONB, nullable=True)
    
    # Dataset info
    training_set_size = Column(Integer, nullable=False)
    test_set_size = Column(Integer, nullable=False)
    dataset_description = Column(Text, nullable=True)
    
    # Timing
    training_date = Column(DateTime(timezone=True), nullable=False)
    evaluation_date = Column(DateTime(timezone=True), server_default=func.now())
    training_duration = Column(Float, nullable=True)  # in seconds
    
    # Metadata
    parameters = Column(JSONB, nullable=True)
    feature_importance = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)


class TrainingJob(Base):
    """
    Enhanced model for tracking model training jobs
    """
    __tablename__ = "training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # Job configuration
    name = Column(String(200), nullable=False)
    algorithm = Column(String(50), nullable=False)
    dataset_name = Column(String(100), nullable=False)
    dataset_size = Column(Integer, nullable=True)
    
    # Status tracking
    status = Column(String(20), nullable=False)  # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0-100
    current_epoch = Column(Integer, nullable=True)
    total_epochs = Column(Integer, nullable=True)
    
    # Metrics and results
    metrics = Column(JSONB, nullable=True)  # Store training metrics
    final_metrics = Column(JSONB, nullable=True)  # Final evaluation metrics
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Model reference
    model_id = Column(String(36), nullable=True)  # Reference to saved model
    
    # Ownership
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="training_jobs")

    @classmethod
    def generate_job_id(cls) -> str:
        """Generate unique training job ID"""
        return str(uuid.uuid4())


class TrainedModel(Base):
    """
    Enhanced model for storing trained model metadata
    """
    __tablename__ = "trained_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # Basic info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    algorithm = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    
    # Dataset info
    dataset_name = Column(String(100), nullable=False)
    dataset_size = Column(Integer, nullable=False)
    dataset_hash = Column(String(64), nullable=True)  # For dataset versioning
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Model status
    status = Column(String(20), default='trained')  # trained, deployed, archived, deprecated
    is_active = Column(Boolean, default=False)  # Only one active model per algorithm
    
    # Storage info
    file_path = Column(String(500), nullable=False)
    model_size = Column(Float, nullable=True)  # Size in MB
    file_hash = Column(String(64), nullable=True)  # For integrity checking
    
    # Training info
    training_time = Column(Float, nullable=True)  # Time in seconds
    parameters = Column(JSONB, nullable=True)  # Model hyperparameters
    feature_names = Column(JSONB, nullable=True)  # List of feature names
    
    # Ownership
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="trained_models")

    @classmethod
    def generate_model_id(cls) -> str:
        """Generate unique model ID"""
        return str(uuid.uuid4())


class APILog(Base):
    """
    Enhanced model for logging API requests and responses
    """
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request info
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Request/response data
    request_headers = Column(JSONB, nullable=True)
    request_data = Column(JSONB, nullable=True)
    response_status = Column(Integer, nullable=False)
    response_headers = Column(JSONB, nullable=True)
    response_data = Column(JSONB, nullable=True)
    
    # Performance
    processing_time = Column(Float, nullable=True)  # Time in milliseconds
    request_size = Column(Integer, nullable=True)  # Size in bytes
    response_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Errors
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="api_logs")


class SystemConfig(Base):
    """
    Enhanced model for storing system configuration
    """
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, index=True, nullable=False)
    config_value = Column(JSONB, nullable=False)
    data_type = Column(String(20), nullable=False)  # string, number, boolean, array, object
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # security, model, email, etc.
    
    # Access control
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Audit
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    updated_by_user = relationship("User")


# Export all models
__all__ = [
    'Base',
    'User',
    'UserProfile',
    'UserActivity',
    'EmailVerification',
    'PredictionResult', 
    'UserFeedback',
    'NewsSource',
    'ModelPerformance',
    'TrainingJob',
    'TrainedModel',
    'APILog',
    'SystemConfig',
]