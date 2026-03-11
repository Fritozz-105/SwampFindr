"""API routes initialization."""
from flask import Blueprint
from flask_restx import Api
from app.routes.api import api as api_namespace
from app.routes.agent import agent
from app.routes.vectordb import vectordb
from app.routes.profiles import profiles
from app.routes.recommendations import recommendations


# Create main blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize Flask-RESTX API with Swagger documentation
api = Api(
    api_bp,
    title='SwampFindr API',
    version='1.0',
    description='REST API for SwampFindr - Agent-based apartment search application',
    doc='/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Enter: Bearer <your_supabase_token>',
        }
    },
)

# Add namespaces
api.add_namespace(api_namespace, path='/listings')
api.add_namespace(agent, path="/chat")
api.add_namespace(vectordb, path="/pinecone")
api.add_namespace(profiles, path="/profiles")
api.add_namespace(recommendations, path="/recommendations")


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(api_bp)
