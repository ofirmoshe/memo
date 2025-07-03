"""
User Profile API Endpoints
Provides REST API for user profile management.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.db.database import get_db
from app.services.user_profile_service import UserProfileService
from app.models.user_profile import (
    UserProfile, CreateUserProfileRequest, UpdateUserProfileRequest,
    TelegramUserData, GoogleUserData, AppleUserData, AuthProvider
)

router = APIRouter(prefix="/api/v1/user", tags=["user-profile"])

def get_user_profile_service() -> UserProfileService:
    """Get user profile service instance."""
    return UserProfileService()

@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Get user profile by user ID."""
    try:
        with service:
            profile = service.get_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")

@router.post("/profile", response_model=UserProfile)
async def create_user_profile(
    request: CreateUserProfileRequest,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Create a new user profile."""
    try:
        with service:
            user, profile = service.get_or_create_user_with_profile(
                user_id=request.user_id,
                auth_provider=request.auth_provider,
                provider_data={
                    "display_name": request.display_name,
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "username": request.username,
                    "email": request.email,
                    "avatar_url": request.avatar_url,
                    "country_code": request.country_code,
                    "timezone": request.timezone,
                    "primary_language": request.primary_language,
                    "metadata": request.provider_metadata
                }
            )
            
            # Return full profile
            return service.get_profile(request.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")

@router.put("/profile/{user_id}", response_model=UserProfile)
async def update_user_profile(
    user_id: str,
    request: UpdateUserProfileRequest,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Update user profile."""
    try:
        with service:
            # Check if profile exists
            existing_profile = service.get_profile(user_id)
            if not existing_profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Update profile
            service.update_profile(user_id, request)
            
            # Return updated profile
            return service.get_profile(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

@router.post("/profile/telegram", response_model=UserProfile)
async def create_profile_from_telegram(
    telegram_data: TelegramUserData,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Create or update user profile from Telegram user data."""
    try:
        with service:
            return service.create_from_telegram(telegram_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Telegram profile: {str(e)}")

@router.post("/profile/google", response_model=UserProfile)
async def create_profile_from_google(
    google_data: GoogleUserData,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Create or update user profile from Google user data."""
    try:
        with service:
            return service.create_from_google(google_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Google profile: {str(e)}")

@router.post("/profile/apple", response_model=UserProfile)
async def create_profile_from_apple(
    apple_data: AppleUserData,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Create or update user profile from Apple user data."""
    try:
        with service:
            return service.create_from_apple(apple_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Apple profile: {str(e)}")

@router.post("/activity/{user_id}")
async def record_user_activity(
    user_id: str,
    activity_type: str,
    activity_data: Optional[Dict[str, Any]] = None,
    source_platform: str = "api",
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Record user activity."""
    try:
        with service:
            service.update_activity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                source_platform=source_platform
            )
            return {"message": "Activity recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording activity: {str(e)}")

@router.get("/stats/{user_id}")
async def get_user_stats(
    user_id: str,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Get comprehensive user statistics."""
    try:
        with service:
            stats = service.get_user_stats(user_id)
            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

@router.delete("/profile/{user_id}")
async def delete_user_profile(
    user_id: str,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Delete user profile (soft delete by setting is_active=False)."""
    try:
        with service:
            # Check if profile exists
            profile = service.get_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Soft delete by updating is_active
            update_request = UpdateUserProfileRequest(is_active=False)
            service.update_profile(user_id, update_request)
            
            return {"message": "User profile deactivated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating profile: {str(e)}")

# Utility endpoints for mobile app integration

@router.get("/profile/{user_id}/auth-providers")
async def get_user_auth_providers(
    user_id: str,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Get user's authentication providers."""
    try:
        with service:
            profile = service.get_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            return {
                "user_id": user_id,
                "auth_providers": profile.auth_providers
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving auth providers: {str(e)}")

@router.post("/profile/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: Dict[str, Any],
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Update user preferences."""
    try:
        with service:
            # Get current profile
            profile = service.get_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Update only preferences
            from app.models.user_profile import UserPreferences
            try:
                updated_preferences = UserPreferences(**preferences)
                update_request = UpdateUserProfileRequest(preferences=updated_preferences)
                service.update_profile(user_id, update_request)
                
                return {"message": "Preferences updated successfully"}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid preferences: {str(e)}")
                
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")

@router.get("/profile/{user_id}/summary")
async def get_user_profile_summary(
    user_id: str,
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Get user profile summary (minimal info for UI)."""
    try:
        with service:
            profile = service.get_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            return {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "username": profile.username,
                "avatar_url": profile.avatar_url,
                "primary_language": profile.primary_language,
                "is_premium": profile.is_premium,
                "total_items": profile.total_items,
                "total_searches": profile.total_searches,
                "last_active_at": profile.last_active_at,
                "auth_providers": [{"provider": ap.provider, "is_primary": ap.is_primary} for ap in profile.auth_providers]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile summary: {str(e)}")

# Batch operations for efficient mobile app syncing

@router.post("/profiles/batch")
async def batch_update_profiles(
    updates: Dict[str, UpdateUserProfileRequest],
    service: UserProfileService = Depends(get_user_profile_service)
):
    """Batch update multiple user profiles."""
    try:
        results = {}
        with service:
            for user_id, update_data in updates.items():
                try:
                    service.update_profile(user_id, update_data)
                    results[user_id] = {"status": "success"}
                except Exception as e:
                    results[user_id] = {"status": "error", "message": str(e)}
            
            return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch update: {str(e)}") 