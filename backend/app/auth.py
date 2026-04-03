"""JWT authentication middleware for Supabase tokens."""

import os
from functools import wraps

import jwt
from jwt import PyJWKClient
from flask import request, g
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

_jwk_client = None


def _get_jwk_client() -> PyJWKClient:
    """Lazy-init JWKS client so it fetches public keys from Supabase."""
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(JWKS_URL)
    return _jwk_client


def require_auth(f):
    """Decorator that verifies Supabase JWT and stores user_id in flask.g."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Missing or invalid Authorization header"}, 401

        token = auth_header[7:]  # Strip "Bearer "

        try:
            signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token has expired"}, 401
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}, 401

        g.user_id = payload["sub"]
        return f(*args, **kwargs)

    return decorated
