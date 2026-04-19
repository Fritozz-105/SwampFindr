"""Gmail OAuth + send-email service helpers."""
import base64
import os
from datetime import datetime, timezone
from email.message import EmailMessage
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

import requests
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.database import get_gmail_auth_collection

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
DEFAULT_SETTINGS_REDIRECT_URL = "http://localhost:3000/settings"
DEFAULT_OAUTH_SCOPES = (
    "https://www.googleapis.com/auth/gmail.send "
    "https://www.googleapis.com/auth/userinfo.email "
    "openid"
)
OAUTH_STATE_SALT = "gmail-oauth-state"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required for Gmail OAuth")
    return value


def _get_scopes() -> str:
    return os.getenv("GOOGLE_GMAIL_SCOPES", DEFAULT_OAUTH_SCOPES).strip()


def _get_oauth_serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config.get("SECRET_KEY", "").strip()
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be configured for OAuth state signing")
    return URLSafeTimedSerializer(secret_key, salt=OAUTH_STATE_SALT)


def _build_redirect_url(result: str, reason: str | None = None) -> str:
    base = os.getenv("GOOGLE_GMAIL_SETTINGS_REDIRECT_URL", DEFAULT_SETTINGS_REDIRECT_URL).strip()
    parsed = urlparse(base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["gmail"] = result
    if reason:
        query["reason"] = reason
    return urlunparse(parsed._replace(query=urlencode(query)))


def build_success_redirect_url() -> str:
    return _build_redirect_url("connected")


def build_error_redirect_url(reason: str) -> str:
    return _build_redirect_url("error", reason=reason)


def get_gmail_status(user_id: str) -> dict:
    doc = get_gmail_auth_collection().find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        return {"enabled": False, "google_email": None, "connected_at": None}

    connected_at = doc.get("connected_at")
    if isinstance(connected_at, datetime):
        connected_at = connected_at.isoformat()

    return {
        "enabled": bool(doc.get("enabled", False)),
        "google_email": doc.get("google_email"),
        "connected_at": connected_at,
    }


def create_google_connect_url(user_id: str) -> str:
    client_id = _require_env("GOOGLE_OAUTH_CLIENT_ID")
    redirect_uri = _require_env("GOOGLE_GMAIL_REDIRECT_URI")

    serializer = _get_oauth_serializer()
    state = serializer.dumps({"user_id": user_id})

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _get_scopes(),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _exchange_auth_code(code: str) -> dict:
    token_resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": _require_env("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": _require_env("GOOGLE_OAUTH_CLIENT_SECRET"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": _require_env("GOOGLE_GMAIL_REDIRECT_URI"),
        },
        timeout=20,
    )
    token_resp.raise_for_status()
    return token_resp.json()


def _fetch_google_email(access_token: str) -> str:
    userinfo_resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    userinfo_resp.raise_for_status()
    email = userinfo_resp.json().get("email", "").strip()
    if not email:
        raise RuntimeError("Google account email was not returned by userinfo endpoint")
    return email


def complete_google_oauth(code: str, state: str) -> dict:
    serializer = _get_oauth_serializer()
    try:
        payload = serializer.loads(state, max_age=600)
    except (SignatureExpired, BadSignature) as e:
        raise ValueError("OAuth state is invalid or expired") from e

    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
        raise ValueError("OAuth state missing user_id")

    token_data = _exchange_auth_code(code)
    access_token = token_data.get("access_token", "").strip()
    if not access_token:
        raise RuntimeError("Google token exchange did not return access_token")

    collection = get_gmail_auth_collection()
    existing = collection.find_one({"user_id": user_id}, {"refresh_token": 1, "_id": 0}) or {}
    refresh_token = token_data.get("refresh_token", "").strip() or existing.get("refresh_token", "")
    if not refresh_token:
        raise RuntimeError("Google token exchange did not return refresh_token")

    google_email = _fetch_google_email(access_token)
    now = datetime.now(timezone.utc)
    collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "enabled": True,
                "google_email": google_email,
                "refresh_token": refresh_token,
                "scopes": token_data.get("scope", _get_scopes()),
                "connected_at": now,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    return {"user_id": user_id, "enabled": True, "google_email": google_email}


def disconnect_google_emailing(user_id: str) -> bool:
    result = get_gmail_auth_collection().delete_one({"user_id": user_id})
    return result.deleted_count > 0


def _refresh_access_token(refresh_token: str) -> str:
    token_resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": _require_env("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": _require_env("GOOGLE_OAUTH_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=20,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json().get("access_token", "").strip()
    if not access_token:
        raise RuntimeError("Google refresh_token exchange did not return access_token")
    return access_token


def send_email_on_behalf(
    user_id: str,
    to_address: str,
    email_content: str,
    subject: str = "Property Tour Request",
) -> dict:
    to_address = to_address.strip()
    email_content = email_content.strip()
    if not to_address:
        raise ValueError("to_address is required")
    if not email_content:
        raise ValueError("email_content is required")

    collection = get_gmail_auth_collection()
    auth_doc = collection.find_one({"user_id": user_id, "enabled": True}, {"_id": 0})
    if not auth_doc:
        raise RuntimeError(f"Gmail emailing is not enabled for user_id={user_id}")

    refresh_token = str(auth_doc.get("refresh_token", "")).strip()
    if not refresh_token:
        raise RuntimeError(f"No Gmail refresh_token stored for user_id={user_id}")

    access_token = _refresh_access_token(refresh_token)

    message = EmailMessage()
    message["To"] = to_address
    message["Subject"] = subject
    sender_email = str(auth_doc.get("google_email", "")).strip()
    if sender_email:
        message["From"] = sender_email
    message.set_content(email_content)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    send_resp = requests.post(
        GMAIL_SEND_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"raw": raw_message},
        timeout=20,
    )
    send_resp.raise_for_status()
    payload = send_resp.json()

    collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_used_at": datetime.now(timezone.utc)}},
    )

    return {
        "success": True,
        "id": payload.get("id"),
        "thread_id": payload.get("threadId"),
        "to": to_address,
    }
