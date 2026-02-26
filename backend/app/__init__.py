"""Flask application factory."""
from flask import Flask
from flask_cors import CORS
from app.config import Config, _DEFAULT_SECRET
from app.routes import register_blueprints
from app.database import init_db, close_db
import atexit


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.debug and app.config.get("SECRET_KEY") == _DEFAULT_SECRET:
        raise RuntimeError(
            "SECRET_KEY is set to the default insecure value. "
            "Set the SECRET_KEY environment variable before deploying to production."
        )
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize MongoDB connection
    init_db(app)
    
    # Register cleanup on shutdown
    atexit.register(lambda: close_db())
    
    # Register blueprints
    register_blueprints(app)
    
    return app
