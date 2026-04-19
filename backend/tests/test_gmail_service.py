import os
from urllib.parse import urlparse, parse_qs
from unittest.mock import MagicMock, patch

from flask import Flask

from app.services import gmail_service


def _app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    return app


@patch.dict(
    os.environ,
    {
        "GOOGLE_OAUTH_CLIENT_ID": "client-id",
        "GOOGLE_OAUTH_CLIENT_SECRET": "client-secret",
        "GOOGLE_GMAIL_REDIRECT_URI": "http://localhost:8080/api/v1/emailing/google/callback",
    },
    clear=False,
)
def test_create_google_connect_url_contains_expected_params():
    app = _app()
    with app.app_context():
        url = gmail_service.create_google_connect_url("user-123")

    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"
    assert params["client_id"] == ["client-id"]
    assert params["redirect_uri"] == ["http://localhost:8080/api/v1/emailing/google/callback"]
    assert params["response_type"] == ["code"]
    assert "state" in params
    assert params["access_type"] == ["offline"]


@patch.dict(
    os.environ,
    {
        "GOOGLE_OAUTH_CLIENT_ID": "client-id",
        "GOOGLE_OAUTH_CLIENT_SECRET": "client-secret",
        "GOOGLE_GMAIL_REDIRECT_URI": "http://localhost:8080/api/v1/emailing/google/callback",
    },
    clear=False,
)
@patch("app.services.gmail_service.requests.get")
@patch("app.services.gmail_service.requests.post")
@patch("app.services.gmail_service.get_gmail_auth_collection")
def test_complete_google_oauth_enables_emailing(
    mock_collection_fn,
    mock_post,
    mock_get,
):
    app = _app()
    collection = MagicMock()
    collection.find_one.return_value = None
    mock_collection_fn.return_value = collection

    token_response = MagicMock()
    token_response.raise_for_status.return_value = None
    token_response.json.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "scope": "https://www.googleapis.com/auth/gmail.send",
    }
    mock_post.return_value = token_response

    userinfo_response = MagicMock()
    userinfo_response.raise_for_status.return_value = None
    userinfo_response.json.return_value = {"email": "user@gmail.com"}
    mock_get.return_value = userinfo_response

    with app.app_context():
        state = gmail_service._get_oauth_serializer().dumps({"user_id": "supabase-user-id"})
        result = gmail_service.complete_google_oauth(code="oauth-code", state=state)

    assert result["enabled"] is True
    assert result["google_email"] == "user@gmail.com"
    assert collection.update_one.called

    update_doc = collection.update_one.call_args.args[1]
    assert update_doc["$set"]["enabled"] is True
    assert update_doc["$set"]["refresh_token"] == "refresh-token"


@patch.dict(
    os.environ,
    {
        "GOOGLE_OAUTH_CLIENT_ID": "client-id",
        "GOOGLE_OAUTH_CLIENT_SECRET": "client-secret",
    },
    clear=False,
)
@patch("app.services.gmail_service.requests.post")
@patch("app.services.gmail_service.get_gmail_auth_collection")
def test_send_email_on_behalf_sends_gmail_message(
    mock_collection_fn,
    mock_post,
):
    collection = MagicMock()
    collection.find_one.return_value = {
        "user_id": "user-1",
        "enabled": True,
        "google_email": "sender@gmail.com",
        "refresh_token": "refresh-token",
    }
    mock_collection_fn.return_value = collection

    refresh_response = MagicMock()
    refresh_response.raise_for_status.return_value = None
    refresh_response.json.return_value = {"access_token": "access-token"}

    send_response = MagicMock()
    send_response.raise_for_status.return_value = None
    send_response.json.return_value = {"id": "gmail-message-id", "threadId": "gmail-thread-id"}

    mock_post.side_effect = [refresh_response, send_response]

    result = gmail_service.send_email_on_behalf(
        user_id="user-1",
        to_address="leasing@example.com",
        email_content="Hello, I want to schedule a tour.",
        subject="Tour request",
    )

    assert result["success"] is True
    assert result["id"] == "gmail-message-id"
    assert mock_post.call_count == 2


@patch("app.services.gmail_service.get_gmail_auth_collection")
def test_send_email_on_behalf_requires_enabled_google_auth(mock_collection_fn):
    collection = MagicMock()
    collection.find_one.return_value = None
    mock_collection_fn.return_value = collection

    try:
        gmail_service.send_email_on_behalf(
            user_id="missing-user",
            to_address="leasing@example.com",
            email_content="Hello",
        )
    except RuntimeError as exc:
        assert "not enabled" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when Gmail is not enabled")
