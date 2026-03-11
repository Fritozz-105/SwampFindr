"""Profile API endpoints."""
import logging
import threading

from flask import request, g
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

from app.auth import require_auth
from app.models.profile import (
    OnboardingRequest,
    ProfileUpdateRequest,
    PreferencesUpdateRequest,
)
from app.database import get_listings_collection
from app.services.profile_service import (
    create_or_update_profile,
    get_profile_by_user_id,
    generate_preference_embedding,
    update_profile,
    update_preferences,
    toggle_favorite,
    get_favorites,
)

logger = logging.getLogger(__name__)

profiles = Namespace("profiles", description="User profile operations")

# Swagger Models for request/response validation and documentation

preferences_model = profiles.model("UserPreferences", {
    "bedrooms": fields.Integer(default=1),
    "bathrooms": fields.Integer(default=1),
    "price_min": fields.Integer(default=500),
    "price_max": fields.Integer(default=2000),
    "distance_from_campus": fields.String(default="any"),
    "roommates": fields.Integer(default=0),
    "amenities": fields.List(fields.String, default=[]),
    "excerpt": fields.String(default=""),
})

onboarding_request_model = profiles.model("OnboardingRequest", {
    "username": fields.String(required=True, description="2-30 characters"),
    "phone": fields.String(default=""),
    "bedrooms": fields.Integer(default=1),
    "bathrooms": fields.Integer(default=1),
    "price_min": fields.Integer(default=500),
    "price_max": fields.Integer(default=2000),
    "distance_from_campus": fields.String(default="any"),
    "roommates": fields.Integer(default=0),
    "amenities": fields.List(fields.String, default=[]),
    "excerpt": fields.String(default="", description="Max 200 characters"),
})

profile_response_model = profiles.model("ProfileResponse", {
    "success": fields.Boolean,
    "data": fields.Raw,
})

status_response_model = profiles.model("StatusResponse", {
    "success": fields.Boolean,
    "onboarding_completed": fields.Boolean,
})

profile_update_model = profiles.model("ProfileUpdateRequest", {
    "username": fields.String(description="2-30 characters"),
    "phone": fields.String(),
    "avatar_url": fields.String(),
})

preferences_update_model = profiles.model("PreferencesUpdateRequest", {
    "bedrooms": fields.Integer(default=1),
    "bathrooms": fields.Integer(default=1),
    "price_min": fields.Integer(default=500),
    "price_max": fields.Integer(default=2000),
    "distance_from_campus": fields.String(default="any"),
    "roommates": fields.Integer(default=0),
    "amenities": fields.List(fields.String, default=[]),
    "excerpt": fields.String(default="", description="Max 200 characters"),
})


@profiles.route("/onboarding")
class Onboarding(Resource):
    @profiles.expect(onboarding_request_model)
    @profiles.doc(security="Bearer")
    @require_auth
    def post(self):
        """Submit onboarding data, creates profile and generates embedding."""
        if not request.json:
            return {"success": False, "error": "Request body must be JSON"}, 400

        try:
            data = OnboardingRequest(**request.json)
        except ValidationError as e:
            return {"success": False, "error": e.errors()}, 400

        if data.price_max < data.price_min:
            return {"success": False, "error": "price_max must be >= price_min"}, 400

        profile = create_or_update_profile(g.user_id, data)

        # Generate embedding in the background, don't block onboarding
        threading.Thread(
            target=generate_preference_embedding,
            args=(g.user_id, profile),
            daemon=True,
        ).start()

        return {"success": True, "data": profile}, 201


@profiles.route("/me")
class ProfileMe(Resource):
    @profiles.doc(security="Bearer")
    @require_auth
    def get(self):
        """Get the current user's full profile."""
        profile = get_profile_by_user_id(g.user_id)
        if not profile:
            return {"success": False, "error": "Profile not found"}, 404

        return {"success": True, "data": profile}

    @profiles.expect(profile_update_model)
    @profiles.doc(security="Bearer")
    @require_auth
    def patch(self):
        """Update profile fields (username, phone, avatar_url)."""
        if not request.json:
            return {"success": False, "error": "Request body must be JSON"}, 400

        try:
            data = ProfileUpdateRequest(**request.json)
        except ValidationError as e:
            return {"success": False, "error": e.errors()}, 400

        profile = update_profile(g.user_id, data)
        if not profile:
            return {"success": False, "error": "Profile not found"}, 404

        return {"success": True, "data": profile}


@profiles.route("/me/preferences")
class ProfilePreferences(Resource):
    @profiles.expect(preferences_update_model)
    @profiles.doc(security="Bearer")
    @require_auth
    def put(self):
        """Replace all preferences and regenerate embedding."""
        if not request.json:
            return {"success": False, "error": "Request body must be JSON"}, 400

        try:
            data = PreferencesUpdateRequest(**request.json)
        except ValidationError as e:
            return {"success": False, "error": e.errors()}, 400

        if data.price_max < data.price_min:
            return {"success": False, "error": "price_max must be >= price_min"}, 400

        profile = update_preferences(g.user_id, data)
        if not profile:
            return {"success": False, "error": "Profile not found"}, 404

        return {"success": True, "data": profile}


favorite_request_model = profiles.model("FavoriteRequest", {
    "listing_id": fields.String(required=True, description="Listing ID to toggle"),
})

favorite_response_model = profiles.model("FavoriteResponse", {
    "success": fields.Boolean,
    "action": fields.String(description="'added' or 'removed'"),
    "favorites": fields.List(fields.String),
})

favorites_list_model = profiles.model("FavoritesListResponse", {
    "success": fields.Boolean,
    "data": fields.List(fields.String),
    "count": fields.Integer,
})


@profiles.route("/me/favorites")
class ProfileFavorites(Resource):
    @profiles.expect(favorite_request_model)
    @profiles.doc(security="Bearer")
    @require_auth
    def post(self):
        """Toggle a listing in the user's favorites."""
        if not request.json or "listing_id" not in request.json:
            return {"success": False, "error": "listing_id is required"}, 400

        listing_id = request.json["listing_id"]

        # Validate listing exists
        listing = get_listings_collection().find_one({"listing_id": listing_id})
        if not listing:
            return {"success": False, "error": "Listing not found"}, 404

        result = toggle_favorite(g.user_id, listing_id)
        if result is None:
            return {"success": False, "error": "Profile not found"}, 404

        return {
            "success": True,
            "action": result["action"],
            "favorites": result["favorites"],
        }

    @profiles.doc(security="Bearer")
    @require_auth
    def get(self):
        """Get the current user's favorites list."""
        favorites = get_favorites(g.user_id)
        return {"success": True, "data": favorites, "count": len(favorites)}


@profiles.route("/status")
class ProfileStatus(Resource):
    @profiles.doc(security="Bearer")
    @require_auth
    def get(self):
        """Lightweight check: has the user completed onboarding?"""
        profile = get_profile_by_user_id(g.user_id)
        completed = bool(profile and profile.get("onboarding_completed"))

        return {"success": True, "onboarding_completed": completed}
