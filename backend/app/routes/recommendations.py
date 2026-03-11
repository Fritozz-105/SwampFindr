"""Recommendation API endpoints."""
from flask import request, g
from flask_restx import Namespace, Resource, fields

from app.auth import require_auth
from app.services.recommendation_service import get_recommendations

recommendations = Namespace(
  "recommendations",
  description="Personalized listing recommendations",
)

pagination_model = recommendations.model("PaginationMeta", {
  "page": fields.Integer,
  "per_page": fields.Integer,
  "total": fields.Integer,
  "has_next": fields.Boolean,
})

recommendation_response_model = recommendations.model("RecommendationResponse", {
  "success": fields.Boolean,
  "data": fields.List(fields.Raw, description="List of listings with match_score"),
  "pagination": fields.Nested(pagination_model),
  "source": fields.String(description="'pinecone' or 'fallback'"),
})


@recommendations.route("/")
class RecommendationList(Resource):
  @recommendations.doc(security="Bearer")
  @recommendations.marshal_with(recommendation_response_model)
  @require_auth
  def get(self):
    """Get personalized listing recommendations for the current user."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if page < 1:
      page = 1
    if per_page < 1:
      per_page = 10
    if per_page > 50:
      per_page = 50

    result = get_recommendations(g.user_id, page, per_page)

    return {
      "success": True,
      "data": result["listings"],
      "pagination": result["pagination"],
      "source": result["source"],
    }
