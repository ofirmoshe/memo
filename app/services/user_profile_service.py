"""
User Profile Service
Handles all user profile operations while maintaining backward compatibility.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_or_create_user, User, SessionLocal
from app.db.user_profile_models import UserProfile, UserAuthProvider, UserActivity
from app.models.user_profile import (
    AuthProvider, LanguageCode, CountryCode, UserPreferences,
    CreateUserProfileRequest, UpdateUserProfileRequest,
    TelegramUserData, GoogleUserData, AppleUserData,
    UserProfile as UserProfileModel
)

logger = logging.getLogger(__name__)

class UserProfileService:
    """Service for managing user profiles and authentication providers."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def get_or_create_user_with_profile(
        self, 
        user_id: str, 
        auth_provider: AuthProvider = None,
        provider_data: Dict[str, Any] = None
    ) -> tuple[User, UserProfile]:
        """
        Get or create user with profile. Maintains backward compatibility.
        
        Args:
            user_id: Internal user ID (Telegram ID as string for existing users)
            auth_provider: Authentication provider
            provider_data: Provider-specific data
            
        Returns:
            Tuple of (User, UserProfile)
        """
        try:
            # Get or create basic user (maintains compatibility)
            user = get_or_create_user(self.db, user_id)
            
            # Get or create user profile
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                # Create new profile
                profile = UserProfile(
                    user_id=user_id,
                    preferences=UserPreferences().dict(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(profile)
                
                # If provider data is available, extract profile info
                if auth_provider and provider_data:
                    self._populate_profile_from_provider(profile, auth_provider, provider_data)
                
                self.db.commit()
                self.db.refresh(profile)
                logger.info(f"Created new profile for user {user_id}")
            
            # Handle auth provider if provided
            if auth_provider and provider_data:
                self._update_auth_provider(user_id, auth_provider, provider_data)
            
            return user, profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user profile for {user_id}: {str(e)}")
            raise
    
    def update_profile(self, user_id: str, update_data: UpdateUserProfileRequest) -> UserProfile:
        """Update user profile with provided data."""
        try:
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                raise ValueError(f"Profile not found for user {user_id}")
            
            # Update fields if provided
            update_dict = update_data.dict(exclude_unset=True)
            
            for field, value in update_dict.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
            
            profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Updated profile for user {user_id}")
            return profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating profile for {user_id}: {str(e)}")
            raise
    
    def get_profile(self, user_id: str) -> Optional[UserProfileModel]:
        """Get complete user profile."""
        try:
            # Get basic user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Get profile
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                # Create minimal profile for existing users
                _, profile = self.get_or_create_user_with_profile(user_id)
            
            # Get auth providers
            auth_providers = self.db.query(UserAuthProvider).filter(
                UserAuthProvider.user_id == user_id
            ).all()
            
            # Convert to response model
            return self._build_profile_response(user, profile, auth_providers)
            
        except Exception as e:
            logger.error(f"Error getting profile for {user_id}: {str(e)}")
            raise
    
    def create_from_telegram(self, telegram_data: TelegramUserData) -> UserProfileModel:
        """Create user profile from Telegram data."""
        user_id = str(telegram_data.telegram_user_id)
        
        provider_data = {
            "first_name": telegram_data.first_name,
            "last_name": telegram_data.last_name,
            "username": telegram_data.username,
            "language_code": telegram_data.language_code,
            "is_premium": telegram_data.is_premium,
            "metadata": telegram_data.dict()
        }
        
        user, profile = self.get_or_create_user_with_profile(
            user_id=user_id,
            auth_provider=AuthProvider.TELEGRAM,
            provider_data=provider_data
        )
        
        auth_providers = self.db.query(UserAuthProvider).filter(
            UserAuthProvider.user_id == user_id
        ).all()
        
        return self._build_profile_response(user, profile, auth_providers)
    
    def create_from_google(self, google_data: GoogleUserData) -> UserProfileModel:
        """Create user profile from Google data."""
        # For Google, we need to generate an internal user ID
        # In practice, you might want to use a more sophisticated ID generation
        user_id = f"google_{google_data.google_user_id}"
        
        provider_data = {
            "email": google_data.email,
            "name": google_data.name,
            "given_name": google_data.given_name,
            "family_name": google_data.family_name,
            "picture": google_data.picture,
            "locale": google_data.locale,
            "verified_email": google_data.verified_email,
            "metadata": google_data.dict()
        }
        
        user, profile = self.get_or_create_user_with_profile(
            user_id=user_id,
            auth_provider=AuthProvider.GOOGLE,
            provider_data=provider_data
        )
        
        auth_providers = self.db.query(UserAuthProvider).filter(
            UserAuthProvider.user_id == user_id
        ).all()
        
        return self._build_profile_response(user, profile, auth_providers)
    
    def create_from_apple(self, apple_data: AppleUserData) -> UserProfileModel:
        """Create user profile from Apple data."""
        user_id = f"apple_{apple_data.apple_user_id}"
        
        provider_data = {
            "email": apple_data.email,
            "name": apple_data.name,
            "given_name": apple_data.given_name,
            "family_name": apple_data.family_name,
            "metadata": apple_data.dict()
        }
        
        user, profile = self.get_or_create_user_with_profile(
            user_id=user_id,
            auth_provider=AuthProvider.APPLE,
            provider_data=provider_data
        )
        
        auth_providers = self.db.query(UserAuthProvider).filter(
            UserAuthProvider.user_id == user_id
        ).all()
        
        return self._build_profile_response(user, profile, auth_providers)
    
    def update_activity(
        self, 
        user_id: str, 
        activity_type: str, 
        activity_data: Dict[str, Any] = None,
        source_platform: str = "telegram"
    ) -> None:
        """Record user activity."""
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                source_platform=source_platform,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(activity)
            
            # Update last_active_at in profile
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                profile.last_active_at = datetime.utcnow()
                
                # Update activity counters
                if activity_type == "search":
                    profile.total_searches += 1
                elif activity_type in ["save_content", "save_url", "save_text", "save_file"]:
                    profile.total_items += 1
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating activity for {user_id}: {str(e)}")
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        try:
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                return {
                    "total_items": 0,
                    "total_searches": 0,
                    "days_active": 0,
                    "last_active": None,
                    "created_at": None
                }
            
            # Calculate days active
            if profile.created_at:
                days_since_creation = (datetime.utcnow() - profile.created_at).days
                # Get unique active days from activity log
                unique_days = self.db.query(
                    func.date(UserActivity.timestamp)
                ).filter(
                    UserActivity.user_id == user_id
                ).distinct().count()
                
                days_active = min(unique_days, days_since_creation + 1)
            else:
                days_active = 0
            
            return {
                "total_items": profile.total_items,
                "total_searches": profile.total_searches,
                "days_active": days_active,
                "last_active": profile.last_active_at,
                "created_at": profile.created_at,
                "is_premium": profile.is_premium,
                "primary_language": profile.primary_language
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for {user_id}: {str(e)}")
            return {}
    
    def _populate_profile_from_provider(
        self, 
        profile: UserProfile, 
        provider: AuthProvider, 
        provider_data: Dict[str, Any]
    ) -> None:
        """Populate profile from provider data."""
        if provider == AuthProvider.TELEGRAM:
            profile.first_name = provider_data.get("first_name")
            profile.last_name = provider_data.get("last_name")
            profile.username = provider_data.get("username")
            
            # Map Telegram language code to our enum
            lang_code = provider_data.get("language_code", "en")
            if lang_code in [e.value for e in LanguageCode]:
                profile.primary_language = lang_code
            
            # Set display name
            if profile.first_name:
                display_name = profile.first_name
                if profile.last_name:
                    display_name += f" {profile.last_name}"
                profile.display_name = display_name
        
        elif provider == AuthProvider.GOOGLE:
            profile.email = provider_data.get("email")
            profile.first_name = provider_data.get("given_name")
            profile.last_name = provider_data.get("family_name")
            profile.display_name = provider_data.get("name")
            profile.avatar_url = provider_data.get("picture")
            profile.is_verified = provider_data.get("verified_email", False)
            
            # Map Google locale to language
            locale = provider_data.get("locale", "en")
            if locale and len(locale) >= 2:
                lang_code = locale[:2].lower()
                if lang_code in [e.value for e in LanguageCode]:
                    profile.primary_language = lang_code
        
        elif provider == AuthProvider.APPLE:
            profile.email = provider_data.get("email")
            profile.first_name = provider_data.get("given_name")
            profile.last_name = provider_data.get("family_name")
            profile.display_name = provider_data.get("name")
    
    def _update_auth_provider(
        self, 
        user_id: str, 
        provider: AuthProvider, 
        provider_data: Dict[str, Any]
    ) -> None:
        """Update or create auth provider record."""
        provider_user_id = self._extract_provider_user_id(provider, provider_data)
        
        # Check if provider already exists
        auth_provider = self.db.query(UserAuthProvider).filter(
            UserAuthProvider.user_id == user_id,
            UserAuthProvider.provider == provider.value
        ).first()
        
        if not auth_provider:
            # Create new auth provider
            auth_provider = UserAuthProvider(
                user_id=user_id,
                provider=provider.value,
                provider_user_id=provider_user_id,
                provider_username=provider_data.get("username"),
                provider_email=provider_data.get("email"),
                is_primary=True,  # First provider is primary
                created_at=datetime.utcnow(),
                provider_metadata=provider_data.get("metadata", {})
            )
            self.db.add(auth_provider)
        else:
            # Update existing
            auth_provider.last_used_at = datetime.utcnow()
            auth_provider.provider_metadata = provider_data.get("metadata", {})
    
    def _extract_provider_user_id(self, provider: AuthProvider, provider_data: Dict[str, Any]) -> str:
        """Extract provider user ID from provider data."""
        if provider == AuthProvider.TELEGRAM:
            return str(provider_data.get("telegram_user_id", ""))
        elif provider == AuthProvider.GOOGLE:
            return provider_data.get("google_user_id", "")
        elif provider == AuthProvider.APPLE:
            return provider_data.get("apple_user_id", "")
        else:
            return ""
    
    def _build_profile_response(
        self, 
        user: User, 
        profile: UserProfile, 
        auth_providers: List[UserAuthProvider]
    ) -> UserProfileModel:
        """Build complete profile response."""
        from app.models.user_profile import AuthProviderInfo
        
        # Convert auth providers
        provider_info = []
        for auth_provider in auth_providers:
            provider_info.append(AuthProviderInfo(
                provider=auth_provider.provider,
                provider_user_id=auth_provider.provider_user_id,
                provider_username=auth_provider.provider_username,
                provider_email=auth_provider.provider_email,
                is_primary=auth_provider.is_primary,
                created_at=auth_provider.created_at,
                last_used_at=auth_provider.last_used_at,
                metadata=auth_provider.provider_metadata or {}
            ))
        
        # Convert preferences
        preferences = UserPreferences()
        if profile.preferences:
            try:
                preferences = UserPreferences(**profile.preferences)
            except Exception as e:
                logger.warning(f"Error parsing preferences for user {user.id}: {e}")
        
        return UserProfileModel(
            user_id=user.id,
            display_name=profile.display_name,
            first_name=profile.first_name,
            last_name=profile.last_name,
            username=profile.username,
            email=profile.email,
            avatar_url=profile.avatar_url,
            country_code=profile.country_code,
            timezone=profile.timezone,
            primary_language=profile.primary_language or "en",
            secondary_languages=profile.secondary_languages or [],
            auth_providers=provider_info,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            last_active_at=profile.last_active_at,
            preferences=preferences,
            is_active=profile.is_active,
            is_verified=profile.is_verified,
            is_premium=profile.is_premium,
            total_items=profile.total_items,
            total_searches=profile.total_searches,
            days_active=profile.days_active
        ) 