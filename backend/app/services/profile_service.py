"""Profile service — CRUD and preference embedding generation."""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import get_profiles_collection
from app.models.profile import (
    ProfileModel,
    UserPreferences,
    OnboardingRequest,
    ProfileUpdateRequest,
    PreferencesUpdateRequest,
)
from app.services.pinecone_service import upsert_record

logger = logging.getLogger(__name__)


def create_or_update_profile(user_id: str, data: OnboardingRequest) -> dict:
    """Upsert a profile in MongoDB from onboarding data."""
    collection = get_profiles_collection()
    now = datetime.now(timezone.utc)

    preferences = UserPreferences(
        bedrooms=data.bedrooms,
        bathrooms=data.bathrooms,
        price_min=data.price_min,
        price_max=data.price_max,
        distance_from_campus=data.distance_from_campus,
        roommates=data.roommates,
        amenities=data.amenities,
        excerpt=data.excerpt,
    )

    profile = ProfileModel(
        user_id=user_id,
        username=data.username,
        phone=data.phone or "",
        preferences=preferences,
        onboarding_completed=True,
        updated_at=now,
    )

    doc = profile.model_dump()
    created_at = doc.pop("created_at")

    collection.update_one(
        {"user_id": user_id},
        {"$set": doc, "$setOnInsert": {"created_at": created_at}},
        upsert=True,
    )

    return profile.model_dump(mode="json")


def get_profile_by_user_id(user_id: str) -> Optional[dict]:
    """Fetch a profile by user_id. Returns None if not found."""
    collection = get_profiles_collection()
    profile = collection.find_one({"user_id": user_id}, {"_id": 0})
    if profile:
        for key in ("created_at", "updated_at"):
            if isinstance(profile.get(key), datetime):
                profile[key] = profile[key].isoformat()
    return profile


def update_profile(user_id: str, data: ProfileUpdateRequest) -> Optional[dict]:
    """Partial update of profile fields (username, phone, avatar_url)."""
    collection = get_profiles_collection()
    updates = data.model_dump(exclude_none=True)
    if not updates:
        return get_profile_by_user_id(user_id)

    updates["updated_at"] = datetime.now(timezone.utc)
    result = collection.update_one({"user_id": user_id}, {"$set": updates})
    if result.matched_count == 0:
        return None

    return get_profile_by_user_id(user_id)


def update_preferences(user_id: str, data: PreferencesUpdateRequest) -> Optional[dict]:
    """Replace preferences subdocument and regenerate embedding."""
    collection = get_profiles_collection()
    prefs = UserPreferences(**data.model_dump())
    updates = {
        "preferences": prefs.model_dump(),
        "updated_at": datetime.now(timezone.utc),
    }
    result = collection.update_one({"user_id": user_id}, {"$set": updates})
    if result.matched_count == 0:
        return None

    profile = get_profile_by_user_id(user_id)
    if profile:
        generate_preference_embedding(user_id, profile)

    return profile


def generate_preference_embedding(user_id: str, profile: dict) -> Optional[str]:
    """Build natural-language text from preferences and upsert to Pinecone.

    Returns the Pinecone record ID on success, None on failure.
    """
    try:
        prefs = profile.get("preferences", {})
        parts = [
            f"Looking for a place with {prefs.get('bedrooms', 1)} bedroom(s)",
            f"and {prefs.get('bathrooms', 1)} bathroom(s).",
            f"Budget: ${prefs.get('price_min', 500)} to ${prefs.get('price_max', 2000)} per month.",
        ]

        distance = prefs.get("distance_from_campus", "any")
        if distance != "any":
            parts.append(f"Preferred distance from campus: {distance}.")

        roommates = prefs.get("roommates", 0)
        if roommates > 0:
            parts.append(f"Open to {roommates} roommate(s).")
        else:
            parts.append("Prefers living alone.")

        amenities = prefs.get("amenities", [])
        if amenities:
            parts.append(f"Must-have amenities: {', '.join(amenities)}.")

        excerpt = prefs.get("excerpt", "")
        if excerpt:
            parts.append(f"Additional notes: {excerpt}")

        chunk_text = " ".join(parts)
        record_id = upsert_record(chunk_text, category="user_preference", ns="user-preferences")
        logger.info("Created preference embedding %s for user %s", record_id, user_id)

        return record_id
    except Exception:
        logger.exception("Failed to generate preference embedding for user %s", user_id)

        return None
