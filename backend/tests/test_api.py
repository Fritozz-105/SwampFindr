"""Tests for API endpoints."""
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_listings_endpoint(client):
    """Test listings endpoint returns 200."""
    response = client.get('/api/v1/listings/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data
    assert 'data' in data