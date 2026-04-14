"""Application configuration."""
import os
from datetime import timedelta

_DEFAULT_SECRET = 'dev-secret-key-change-in-production'


class Config:
    """Base configuration."""

    # Flask Config
    SECRET_KEY = os.getenv('SECRET_KEY', _DEFAULT_SECRET)
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # API Config
    API_TITLE = 'SwampFindr API'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = '/api'
    OPENAPI_SWAGGER_UI_PATH = '/docs'
    OPENAPI_SWAGGER_UI_URL = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

    # CORS Config
    CORS_HEADERS = 'Content-Type'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
