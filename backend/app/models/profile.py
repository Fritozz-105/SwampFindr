"""Profile and user preferences models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone


class UserPreferences(BaseModel):
    """Housing preferences for recommendation matching."""

    bedrooms: int = Field(ge=0, le=6, default=1)
    bathrooms: int = Field(ge=1, le=6, default=1)
    price_min: int = Field(ge=0, default=500)
    price_max: int = Field(ge=0, default=2000)
    distance_from_campus: str = Field(default="any")
    roommates: int = Field(ge=0, le=10, default=0)
    amenities: List[str] = Field(default_factory=list)
    excerpt: str = Field(max_length=200, default="")


class ProfileModel(BaseModel):
    """Full user profile stored in MongoDB."""

    user_id: str
    username: str = Field(min_length=2, max_length=30)
    phone: str = Field(default="")
    avatar_url: Optional[str] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    favorites: List[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    pinecone_record_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OnboardingRequest(BaseModel):
    """Flat validation model for the onboarding API request body."""

    username: str = Field(min_length=2, max_length=30)
    phone: Optional[str] = ""
    bedrooms: int = Field(ge=0, le=6, default=1)
    bathrooms: int = Field(ge=1, le=6, default=1)
    price_min: int = Field(ge=0, default=500)
    price_max: int = Field(ge=0, default=2000)
    distance_from_campus: str = Field(default="any")
    roommates: int = Field(ge=0, le=10, default=0)
    amenities: List[str] = Field(default_factory=list)
    excerpt: str = Field(max_length=200, default="")


class ProfileUpdateRequest(BaseModel):
    """Partial update for profile fields."""

    username: Optional[str] = Field(None, min_length=2, max_length=30)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class PreferencesUpdateRequest(BaseModel):
    """Full replacement of user preferences."""

    bedrooms: int = Field(ge=0, le=6, default=1)
    bathrooms: int = Field(ge=1, le=6, default=1)
    price_min: int = Field(ge=0, default=500)
    price_max: int = Field(ge=0, default=2000)
    distance_from_campus: str = Field(default="any")
    roommates: int = Field(ge=0, le=10, default=0)
    amenities: List[str] = Field(default_factory=list)
    excerpt: str = Field(max_length=200, default="")
