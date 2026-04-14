"""Flask application factory."""
from flask import Flask
from flask_cors import CORS
from app.config import Config, _DEFAULT_SECRET
from app.extensions import limiter
from app.routes import register_blueprints
from app.database import init_db, close_db
import atexit
import os


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.debug and app.config.get("SECRET_KEY") == _DEFAULT_SECRET:
        raise RuntimeError(
            "SECRET_KEY is set to the default insecure value. "
            "Set the SECRET_KEY environment variable before deploying to production."
        )

    if not os.getenv("SUPABASE_URL", "").strip():
        raise RuntimeError(
            "SUPABASE_URL is not set. Auth will not work without it."
        )

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize rate limiter
    limiter.init_app(app)

    # Initialize MongoDB connection
    init_db(app)

    # Register cleanup on shutdown
    atexit.register(lambda: close_db())

    # Register blueprints
    register_blueprints(app)

    return app
