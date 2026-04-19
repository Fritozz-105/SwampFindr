"""Gmail OAuth + send-email service helpers."""
import base64
import json
import os
from datetime import datetime, timezone
from email.message import EmailMessage
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

import requests
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.database import get_gmail_auth_collection, get_email_history_collection

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
    listing_id: str | None = None,
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

    # Store email in history
    gmail_message_id = payload.get("id", "")
    thread_id = payload.get("threadId", "")
    email_history_collection = get_email_history_collection()
    email_history_collection.insert_one({
        "user_id": user_id,
        "listing_id": listing_id,
        "gmail_message_id": gmail_message_id,
        "thread_id": thread_id,
        "to_address": to_address,
        "from_address": sender_email,
        "subject": subject,
        "message_body": email_content,
        "sent_at": datetime.now(timezone.utc),
        "message_type": "sent",
    })

    return {
        "success": True,
        "id": gmail_message_id,
        "thread_id": thread_id,
        "to": to_address,
    }


def get_email_thread(user_id: str, thread_id: str) -> dict:
    """
    Fetch the complete email thread from Gmail for a given thread_id.
    Parses all messages in the thread and returns them in chronological order.
    
    Args:
        user_id: The Supabase user ID
        thread_id: Gmail thread ID to fetch
        
    Returns:
        Dict with 'success', 'messages' (list of email dicts), or 'error'
    """
    try:
        collection = get_gmail_auth_collection()
        auth_doc = collection.find_one({"user_id": user_id, "enabled": True}, {"_id": 0})
        if not auth_doc:
            return {"success": False, "error": f"Gmail emailing is not enabled for user_id={user_id}"}

        refresh_token = str(auth_doc.get("refresh_token", "")).strip()
        if not refresh_token:
            return {"success": False, "error": f"No Gmail refresh_token stored for user_id={user_id}"}

        access_token = _refresh_access_token(refresh_token)

        # Fetch the thread from Gmail API
        thread_url = f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}"
        thread_resp = requests.get(
            thread_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        thread_resp.raise_for_status()
        thread_data = thread_resp.json()

        messages = []
        for msg_header in thread_data.get("messages", []):
            msg_id = msg_header.get("id")
            msg_thread_id = msg_header.get("threadId")

            # Fetch full message details
            msg_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
            msg_resp = requests.get(
                msg_url,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"format": "full"},
                timeout=20,
            )
            msg_resp.raise_for_status()
            msg_data = msg_resp.json()

            # Parse headers
            headers = {}
            for header in msg_data.get("payload", {}).get("headers", []):
                headers[header["name"].lower()] = header["value"]

            # Extract body (handle multipart)
            body = _extract_message_body(msg_data.get("payload", {}))

            messages.append({
                "message_id": msg_id,
                "thread_id": msg_thread_id,
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
                "body": body,
                "internal_date_ms": msg_data.get("internalDate", ""),
            })

        return {
            "success": True,
            "thread_id": thread_id,
            "message_count": len(messages),
            "messages": messages,
        }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("get_email_thread error: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


def _extract_message_body(payload: dict) -> str:
    """Extract the email body from Gmail payload (handles both plain and multipart)."""
    if "parts" in payload:
        # Multipart message - find the text/plain part
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        # Fallback to first part if no plain text found
        if payload["parts"]:
            data = payload["parts"][0].get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    else:
        # Simple message
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return ""


def get_tour_request_history(user_id: str, listing_id: str | None = None) -> dict:
    """
    Get all tour request emails sent by a user, optionally filtered by listing_id.
    
    Args:
        user_id: The Supabase user ID
        listing_id: Optional listing ID to filter by
        
    Returns:
        Dict with 'success' and 'emails' (list of email history docs)
    """
    try:
        email_history_collection = get_email_history_collection()
        query = {"user_id": user_id, "message_type": "sent"}
        if listing_id:
            query["listing_id"] = listing_id

        emails = list(email_history_collection.find(query, {"_id": 0}).sort("sent_at", -1))

        return {
            "success": True,
            "count": len(emails),
            "emails": emails,
        }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("get_tour_request_history error: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


def send_email_reply_to_thread(user_id: str, thread_id: str, reply_content: str) -> dict:
    """
    Send a reply to a specific email thread.
    Constructs a reply message that references the thread (In-Reply-To header).
    
    Args:
        user_id: The Supabase user ID
        thread_id: Gmail thread ID to reply to
        reply_content: The reply message content
        
    Returns:
        Dict with 'success', message_id, thread_id, or 'error'
    """
    reply_content = reply_content.strip()
    if not reply_content:
        return {"success": False, "error": "reply_content is required"}

    try:
        collection = get_gmail_auth_collection()
        auth_doc = collection.find_one({"user_id": user_id, "enabled": True}, {"_id": 0})
        if not auth_doc:
            return {"success": False, "error": f"Gmail emailing is not enabled for user_id={user_id}"}

        refresh_token = str(auth_doc.get("refresh_token", "")).strip()
        if not refresh_token:
            return {"success": False, "error": f"No Gmail refresh_token stored for user_id={user_id}"}

        access_token = _refresh_access_token(refresh_token)

        # Fetch thread to get latest message info
        thread_url = f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}"
        thread_resp = requests.get(
            thread_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        thread_resp.raise_for_status()
        thread_data = thread_resp.json()

        messages = thread_data.get("messages", [])
        if not messages:
            return {"success": False, "error": f"Thread {thread_id} has no messages"}

        # Get latest message to extract headers
        latest_msg = messages[-1]
        latest_msg_id = latest_msg.get("id")

        # Fetch full message to get headers
        msg_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{latest_msg_id}"
        msg_resp = requests.get(
            msg_url,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"format": "full"},
            timeout=20,
        )
        msg_resp.raise_for_status()
        msg_data = msg_resp.json()

        # Parse headers
        headers = {}
        for header in msg_data.get("payload", {}).get("headers", []):
            headers[header["name"].lower()] = header["value"]

        # Build reply message
        message = EmailMessage()
        message["To"] = headers.get("from", "")  # Reply to sender
        message["Subject"] = f"Re: {headers.get('subject', '')}"
        message["In-Reply-To"] = latest_msg_id
        message["References"] = latest_msg_id
        
        sender_email = str(auth_doc.get("google_email", "")).strip()
        if sender_email:
            message["From"] = sender_email
        
        message.set_content(reply_content)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send reply via Gmail API
        send_resp = requests.post(
            GMAIL_SEND_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw_message, "threadId": thread_id},
            timeout=20,
        )
        send_resp.raise_for_status()
        payload = send_resp.json()

        gmail_message_id = payload.get("id", "")
        returned_thread_id = payload.get("threadId", thread_id)

        # Store reply in email history
        email_history_collection = get_email_history_collection()
        email_history_collection.insert_one({
            "user_id": user_id,
            "thread_id": returned_thread_id,
            "gmail_message_id": gmail_message_id,
            "to_address": headers.get("from", ""),
            "from_address": sender_email,
            "subject": f"Re: {headers.get('subject', '')}",
            "message_body": reply_content,
            "sent_at": datetime.now(timezone.utc),
            "message_type": "sent_reply",
        })

        # Update Gmail auth last_used_at
        collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_used_at": datetime.now(timezone.utc)}},
        )

        return {
            "success": True,
            "id": gmail_message_id,
            "thread_id": returned_thread_id,
        }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("send_email_reply_to_thread error: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


def get_all_tour_email_threads(user_id: str) -> dict:
    """
    Get all tour request email threads for a user with latest info from each thread.
    Useful for showing user all active conversations about property tours.
    
    Args:
        user_id: The Supabase user ID
        
    Returns:
        Dict with 'success', 'threads' (list with thread info and latest message preview)
    """
    try:
        email_history_collection = get_email_history_collection()
        
        # Get all unique threads (get latest message from each thread)
        pipeline = [
            {"$match": {"user_id": user_id, "message_type": {"$in": ["sent", "sent_reply"]}}},
            {"$sort": {"sent_at": -1}},
            {"$group": {
                "_id": "$thread_id",
                "thread_id": {"$first": "$thread_id"},
                "to_address": {"$first": "$to_address"},
                "listing_id": {"$first": "$listing_id"},
                "subject": {"$first": "$subject"},
                "latest_message": {"$first": "$message_body"},
                "last_sent_at": {"$first": "$sent_at"},
                "message_count": {"$sum": 1},
            }},
            {"$sort": {"last_sent_at": -1}},
        ]
        
        threads = list(email_history_collection.aggregate(pipeline))
        
        return {
            "success": True,
            "thread_count": len(threads),
            "threads": threads,
        }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("get_all_tour_email_threads error: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}
