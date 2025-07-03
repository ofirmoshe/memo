"""
Database models for extended user profiles.
Designed to work alongside existing User model without breaking compatibility.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base

class UserProfile(Base):
    """Extended user profile information."""
    __tablename__ = "user_profiles"

    # Primary key - use same user_id as the User table for 1:1 relationship
    user_id = Column(String, ForeignKey("users.id"), primary_key=True, index=True)
    
    # Basic profile information
    display_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True, index=True)  # For search
    email = Column(String, nullable=True, index=True)  # For search and notifications
    avatar_url = Column(String, nullable=True)
    
    # Location and language
    country_code = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    timezone = Column(String, nullable=True)
    primary_language = Column(String(2), nullable=True, default="en")  # ISO 639-1
    secondary_languages = Column(JSON, nullable=True)  # List of language codes
    
    # Account metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # User preferences stored as JSON
    preferences = Column(JSON, nullable=True)
    
    # Usage statistics (updated periodically)
    total_items = Column(Integer, default=0, nullable=False)
    total_searches = Column(Integer, default=0, nullable=False)
    days_active = Column(Integer, default=0, nullable=False)
    
    # Relationship to base User model
    user = relationship("User", back_populates="profile")

class UserAuthProvider(Base):
    """Track authentication providers for each user."""
    __tablename__ = "user_auth_providers"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Provider information
    provider = Column(String, nullable=False, index=True)  # 'telegram', 'google', 'apple'
    provider_user_id = Column(String, nullable=False, index=True)  # ID from the provider
    provider_username = Column(String, nullable=True)
    provider_email = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Provider-specific metadata as JSON
    metadata = Column(JSON, nullable=True)
    
    # Relationship to base User model
    user = relationship("User", back_populates="auth_providers")

class UserActivity(Base):
    """Track user activity for analytics and usage patterns."""
    __tablename__ = "user_activity"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Activity information
    activity_type = Column(String, nullable=False, index=True)  # 'login', 'save_content', 'search', etc.
    activity_data = Column(JSON, nullable=True)  # Additional activity-specific data
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)  # Hashed for privacy
    
    # Source information
    source_platform = Column(String, nullable=True)  # 'telegram', 'mobile_app', 'web'
    source_version = Column(String, nullable=True)  # App/bot version
    
    # Relationship to base User model
    user = relationship("User", back_populates="activities")

# Add these relationships to the existing User model
# This will be done through a migration or model extension

def extend_user_model():
    """
    Function to add relationships to existing User model.
    This should be called during database initialization.
    """
    from app.db.database import User
    
    # Add relationships if they don't exist
    if not hasattr(User, 'profile'):
        User.profile = relationship("UserProfile", back_populates="user", uselist=False)
    
    if not hasattr(User, 'auth_providers'):
        User.auth_providers = relationship("UserAuthProvider", back_populates="user")
    
    if not hasattr(User, 'activities'):
        User.activities = relationship("UserActivity", back_populates="user") 