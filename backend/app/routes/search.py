"""Search API endpoints."""
import logging
from flask import request, g
from flask_restx import Namespace, Resource, fields

from app.auth import require_auth
from app.services.search_service import search_listings, get_recent_searches

logger = logging.getLogger(__name__)

search = Namespace(
    "search",
    description="Semantic listing search",
)

_MAX_QUERY_LENGTH = 500

search_response_model = search.model("SearchResponse", {
    "success": fields.Boolean,
    "data": fields.List(fields.Raw, description="List of listings with match_score"),
    "query": fields.String,
    "total": fields.Integer,
    "error": fields.String(description="Error message on failure"),
})

history_entry_model = search.model("SearchHistoryEntry", {
    "query": fields.String,
    "result_count": fields.Integer,
    "created_at": fields.String,
})

history_response_model = search.model("SearchHistoryResponse", {
    "success": fields.Boolean,
    "data": fields.List(fields.Nested(history_entry_model)),
})


@search.route("/")
class SearchList(Resource):
    @search.doc(security="Bearer")
    @search.marshal_with(search_response_model)
    @require_auth
    def get(self):
        """Search listings using natural language query."""
        q = request.args.get("q", "").strip()
        if not q:
            return {"success": False, "error": "Query parameter 'q' is required"}, 400

        if len(q) > _MAX_QUERY_LENGTH:
            return {"success": False, "error": f"Query exceeds maximum length of {_MAX_QUERY_LENGTH} characters"}, 400

        top_k = request.args.get("top_k", 100, type=int)
        skip_history = request.args.get("skip_history", "0") == "1"

        try:
            result = search_listings(g.user_id, q, top_k, skip_history=skip_history)
            return {
                "success": True,
                "data": result["listings"],
                "query": q,
                "total": result["total"],
            }
        except Exception as e:
            logger.exception("Search failed for user %s: %s", g.user_id, e)
            return {"success": False, "error": "Search failed. Please try again later."}, 502


@search.route("/history")
class SearchHistory(Resource):
    @search.doc(security="Bearer")
    @search.marshal_with(history_response_model)
    @require_auth
    def get(self):
        """Get recent search history for the current user."""
        history = get_recent_searches(g.user_id)
        return {
            "success": True,
            "data": history,
        }
