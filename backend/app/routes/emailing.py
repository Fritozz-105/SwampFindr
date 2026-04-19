"""Gmail OAuth and email-enablement routes."""
from flask import g, request, redirect
from flask_restx import Namespace, Resource, fields
from requests import RequestException

from app.auth import require_auth
from app.services.gmail_service import (
    get_gmail_status,
    create_google_connect_url,
    complete_google_oauth,
    disconnect_google_emailing,
    build_success_redirect_url,
    build_error_redirect_url,
)

emailing = Namespace("emailing", description="Email enablement and OAuth operations")

gmail_status_response = emailing.model("GmailStatusResponse", {
    "success": fields.Boolean,
    "enabled": fields.Boolean,
    "google_email": fields.String,
    "connected_at": fields.String,
})

gmail_connect_response = emailing.model("GmailConnectResponse", {
    "success": fields.Boolean,
    "auth_url": fields.String,
})


@emailing.route("/google/status")
class GmailStatus(Resource):
    @emailing.doc(security="Bearer")
    @emailing.marshal_with(gmail_status_response)
    @require_auth
    def get(self):
        status = get_gmail_status(g.user_id)
        return {"success": True, **status}, 200


@emailing.route("/google/connect")
class GmailConnect(Resource):
    @emailing.doc(security="Bearer")
    @emailing.marshal_with(gmail_connect_response)
    @require_auth
    def post(self):
        auth_url = create_google_connect_url(g.user_id)
        return {"success": True, "auth_url": auth_url}, 200


@emailing.route("/google/disconnect")
class GmailDisconnect(Resource):
    @emailing.doc(security="Bearer")
    @require_auth
    def delete(self):
        disconnected = disconnect_google_emailing(g.user_id)
        return {"success": True, "disconnected": disconnected}, 200


@emailing.route("/google/callback")
class GmailCallback(Resource):
    def get(self):
        oauth_error = request.args.get("error", "").strip()
        code = request.args.get("code", "").strip()
        state = request.args.get("state", "").strip()

        if oauth_error:
            return redirect(build_error_redirect_url(oauth_error))
        if not code or not state:
            return redirect(build_error_redirect_url("missing_code_or_state"))

        try:
            complete_google_oauth(code=code, state=state)
        except (ValueError, RuntimeError, RequestException):
            return redirect(build_error_redirect_url("oauth_exchange_failed"))

        return redirect(build_success_redirect_url())
