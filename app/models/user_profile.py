"""
User Profile Models and Schemas
Extends the basic User model with comprehensive profile information.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class AuthProvider(str, Enum):
    """Supported authentication providers."""
    TELEGRAM = "telegram"
    GOOGLE = "google"
    APPLE = "apple"
    EMAIL = "email"  # For future email-based auth

class LanguageCode(str, Enum):
    """Supported language codes (ISO 639-1)."""
    EN = "en"  # English
    HE = "he"  # Hebrew
    ES = "es"  # Spanish
    FR = "fr"  # French
    DE = "de"  # German
    IT = "it"  # Italian
    RU = "ru"  # Russian
    AR = "ar"  # Arabic
    ZH = "zh"  # Chinese
    JA = "ja"  # Japanese
    KO = "ko"  # Korean
    PT = "pt"  # Portuguese

class CountryCode(str, Enum):
    """Common country codes (ISO 3166-1 alpha-2)."""
    US = "US"  # United States
    IL = "IL"  # Israel
    GB = "GB"  # United Kingdom
    CA = "CA"  # Canada
    AU = "AU"  # Australia
    DE = "DE"  # Germany
    FR = "FR"  # France
    ES = "ES"  # Spain
    IT = "IT"  # Italy
    BR = "BR"  # Brazil
    MX = "MX"  # Mexico
    JP = "JP"  # Japan
    KR = "KR"  # South Korea
    CN = "CN"  # China
    IN = "IN"  # India
    OTHER = "OTHER"  # For unlisted countries

class UserPreferences(BaseModel):
    """User preferences and settings."""
    # Content preferences
    default_language: LanguageCode = LanguageCode.EN
    auto_translate: bool = True
    preferred_content_types: List[str] = Field(default_factory=list)  # e.g., ["articles", "videos"]
    
    # Search and AI preferences
    search_suggestions: bool = True
    ai_analysis_enabled: bool = True
    auto_tagging: bool = True
    
    # Notification preferences
    daily_summary: bool = False
    weekly_digest: bool = False
    content_reminders: bool = False
    
    # Privacy preferences
    anonymous_analytics: bool = True
    data_retention_days: int = 365  # How long to keep content
    
    # UI preferences
    theme: Literal["light", "dark", "auto"] = "auto"
    items_per_page: int = 20
    default_view: Literal["grid", "list", "cards"] = "cards"

class AuthProviderInfo(BaseModel):
    """Information specific to each auth provider."""
    provider: AuthProvider
    provider_user_id: str  # ID from the auth provider
    provider_username: Optional[str] = None
    provider_email: Optional[str] = None
    is_primary: bool = False  # Whether this is the primary auth method
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    # Provider-specific metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UserProfile(BaseModel):
    """Complete user profile information."""
    # Basic identification (required)
    user_id: str = Field(..., description="Internal user ID (unchanged for compatibility)")
    
    # Profile information (optional, can be filled over time)
    display_name: Optional[str] = Field(None, description="User's display name")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    username: Optional[str] = Field(None, description="User's username/handle")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")
    
    # Location and language
    country_code: Optional[CountryCode] = Field(None, description="User's country")
    timezone: Optional[str] = Field(None, description="User's timezone (e.g., 'Asia/Jerusalem')")
    primary_language: LanguageCode = Field(LanguageCode.EN, description="User's primary language")
    secondary_languages: List[LanguageCode] = Field(default_factory=list, description="Additional languages")
    
    # Account metadata
    auth_providers: List[AuthProviderInfo] = Field(default_factory=list, description="Connected auth providers")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: Optional[datetime] = None
    
    # User preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Account status
    is_active: bool = True
    is_verified: bool = False  # Email/phone verification status
    is_premium: bool = False  # For future premium features
    
    # Usage statistics (computed)
    total_items: int = 0
    total_searches: int = 0
    days_active: int = 0
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Request/Response models for API

class CreateUserProfileRequest(BaseModel):
    """Request to create or update user profile."""
    user_id: str
    auth_provider: AuthProvider
    provider_user_id: str
    
    # Optional profile data
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    country_code: Optional[CountryCode] = None
    timezone: Optional[str] = None
    primary_language: Optional[LanguageCode] = None
    
    # Provider-specific metadata
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)

class UpdateUserProfileRequest(BaseModel):
    """Request to update user profile."""
    # All fields optional for partial updates
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    country_code: Optional[CountryCode] = None
    timezone: Optional[str] = None
    primary_language: Optional[LanguageCode] = None
    secondary_languages: Optional[List[LanguageCode]] = None
    preferences: Optional[UserPreferences] = None

class TelegramUserData(BaseModel):
    """Telegram user data for profile creation/update."""
    telegram_user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_bot: bool = False
    is_premium: bool = False
    
    # Additional Telegram metadata
    can_join_groups: Optional[bool] = None
    can_read_all_group_messages: Optional[bool] = None
    supports_inline_queries: Optional[bool] = None

class GoogleUserData(BaseModel):
    """Google user data for profile creation/update."""
    google_user_id: str
    email: EmailStr
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None  # Avatar URL
    locale: Optional[str] = None
    verified_email: bool = False

class AppleUserData(BaseModel):
    """Apple user data for profile creation/update."""
    apple_user_id: str
    email: Optional[EmailStr] = None  # Apple allows hiding email
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    # Apple doesn't provide much profile data by default 