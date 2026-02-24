"""Profile API endpoints."""
import logging

from flask import request, g
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

from app.auth import require_auth
from app.models.profile import OnboardingRequest
from app.services.profile_service import (
  create_or_update_profile,
  get_profile_by_user_id,
  generate_preference_embedding,
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


@profiles.route("/onboarding")
class Onboarding(Resource):
    @profiles.expect(onboarding_request_model)
    @profiles.doc(security="Bearer")
    @require_auth
    def post(self):
        """Submit onboarding data, creates profile and generates embedding."""
        try:
            data = OnboardingRequest(**request.json)
        except ValidationError as e:
            return {"success": False, "error": e.errors()}, 400

        if data.price_max < data.price_min:
            return {"success": False, "error": "price_max must be >= price_min"}, 400

        profile = create_or_update_profile(g.user_id, data)

        # Generate embedding in the background, don't block onboarding
        generate_preference_embedding(g.user_id, profile)

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


@profiles.route("/status")
class ProfileStatus(Resource):
    @profiles.doc(security="Bearer")
    @require_auth
    def get(self):
        """Lightweight check: has the user completed onboarding?"""
        profile = get_profile_by_user_id(g.user_id)
        completed = bool(profile and profile.get("onboarding_completed"))

        return {"success": True, "onboarding_completed": completed}
