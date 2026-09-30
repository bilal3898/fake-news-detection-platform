# backend/database/schema.py

from sqlalchemy import Column, Integer, Enum, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, List
import enum
from backend.database.enums import TrainingStatusEnum

Base = declarative_base()

class LabelEnum(enum.Enum):
    REAL = "real"
    FAKE = "fake"
    UNCERTAIN = "uncertain"

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    feedback = relationship("UserFeedback", back_populates="user")
    training_sessions = relationship("TrainingSession", back_populates="user")

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)  # e.g., 'BBC', 'Twitter', 'Facebook'
    url = Column(String(500), nullable=True, unique=True)
    author = Column(String(100), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    
    # AI Prediction fields
    predicted_label = Column(String(20), nullable=True)  # 'fake', 'real', 'uncertain'
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0
    prediction_metadata = Column(JSON, nullable=True)  # Store model version, features etc.
    
    # Manual verification fields
    verified_label = Column(String(20), nullable=True)  # Manually verified label
    verified_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # System fields
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    feedback = relationship("UserFeedback", back_populates="article")

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    feedback_label = Column(String(20), nullable=False)  # 'fake', 'real', 'unsure'
    confidence = Column(String(20), nullable=True)  # 'low', 'medium', 'high'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("NewsArticle", back_populates="feedback")
    user = relationship("User", back_populates="feedback")

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    algorithm = Column(String(50), nullable=False)  # 'random-forest', 'lstm', etc.
    dataset_size = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    training_time = Column(Float, nullable=True)  # in seconds
    model_path = Column(String(500), nullable=True)  # Path to saved model
    parameters = Column(JSON, nullable=True)  # Training parameters
    status = Column(
    Enum("running", "completed", "failed", name="status_enum"),
    default="running",
    nullable=False
)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="training_sessions")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(50), unique=True, nullable=False)
    algorithm = Column(String(50), nullable=False)
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    model_path = Column(String(500), nullable=False)
    training_data_size = Column(Integer, nullable=False)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())