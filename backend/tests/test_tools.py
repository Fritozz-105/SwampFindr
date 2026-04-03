import pytest
import os
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from app.agents import tools

# Load environment variables from .env file
load_dotenv()


class TestGetDistanceToLocation:
    """Test suite for get_distance_to_location tool."""

    def test_get_distance_to_location_success(self):
        """Test successful distance calculation with valid addresses."""
        # Call the tool with real addresses
        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "Walmart, Gainesville, FL",
            "mode": "driving"
        })

        # Assertions - verify result is valid, not specific values
        assert result["success"] is True
        assert isinstance(result["distance_km"], (int, float))
        assert result["distance_km"] > 0
        assert isinstance(result["distance_miles"], (int, float))
        assert result["distance_miles"] > 0
        assert isinstance(result["duration_minutes"], (int, float))
        assert result["duration_minutes"] > 0
        assert isinstance(result["duration_hours"], (int, float))
        assert result["mode"] == "driving"
        assert isinstance(result["duration_formatted"], str)

    def test_get_distance_to_location_transit_mode(self):
        """Test distance calculation with transit mode."""
        # Call the tool with real addresses
        result = tools.get_distance_to_location.invoke({
            "apartment_address": "456 Oak Ave, Gainesville, FL",
            "destination": "Downtown, Gainesville, FL",
            "mode": "transit"
        })

        # Assertions - verify result is valid, not specific values
        assert result["success"] is True
        assert isinstance(result["distance_km"], (int, float))
        assert result["distance_km"] > 0
        assert isinstance(result["duration_minutes"], (int, float))
        assert result["duration_minutes"] > 0
        assert result["mode"] == "transit"

    def test_get_distance_to_location_walking_mode(self):
        """Test distance calculation with walking mode."""
        # Call the tool with real addresses
        result = tools.get_distance_to_location.invoke({
            "apartment_address": "789 Pine St, Gainesville, FL",
            "destination": "UF Campus, Gainesville, FL",
            "mode": "walking"
        })

        # Assertions - verify result is valid, not specific values
        assert result["success"] is True
        assert isinstance(result["distance_km"], (int, float))
        assert result["distance_km"] > 0
        assert isinstance(result["duration_minutes"], (int, float))
        assert result["duration_minutes"] > 0
        assert result["mode"] == "walking"

    def test_get_distance_to_location_missing_api_key(self):
        """Test error handling when API key is not set."""
        # Ensure API key is not set
        with patch.dict(os.environ, {}, clear=True):
            result = tools.get_distance_to_location.invoke({
                "apartment_address": "123 Main St, Gainesville, FL",
                "destination": "Walmart, Gainesville, FL"
            })

            assert result["success"] is False
            assert "API key" in result["error"]

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    def test_get_distance_to_location_invalid_mode(self):
        """Test error handling with invalid travel mode."""
        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "Walmart, Gainesville, FL",
            "mode": "invalid_mode"
        })

        assert result["success"] is False
        assert "Invalid mode" in result["error"]

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    def test_get_distance_to_location_empty_address(self):
        """Test error handling with empty apartment address."""
        result = tools.get_distance_to_location.invoke({
            "apartment_address": "",
            "destination": "Walmart, Gainesville, FL"
        })

        assert result["success"] is False
        assert "Apartment address" in result["error"]

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    def test_get_distance_to_location_empty_destination(self):
        """Test error handling with empty destination."""
        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": ""
        })

        assert result["success"] is False
        assert "Destination" in result["error"]

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.httpx.Client")
    def test_get_distance_to_location_api_error(self, mock_http_client):
        """Test error handling when Google Maps API returns an error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ZERO_RESULTS",
            "error_message": "No route found"
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response

        mock_http_client.return_value = mock_client_instance

        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "Walmart, Gainesville, FL"
        })

        assert result["success"] is False
        assert "No route found" in result["error"]

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.httpx.Client")
    def test_get_distance_to_location_connection_timeout(self, mock_http_client):
        """Test error handling when connection times out."""
        import httpx

        mock_http_client.side_effect = httpx.ConnectTimeout("Connection timed out")

        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "Walmart, Gainesville, FL"
        })

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.resolve_destination")
    def test_get_distance_to_location_with_place_name(self, mock_resolve, mock_http_client):
        """Test distance calculation with a general place name destination."""
        mock_resolve.return_value = {
            "success": True,
            "formatted_address": "1234 SW 14th St, Gainesville, FL 32608",
            "placeholder": "Walmart",
            "lat": 29.6595,
            "lng": -82.3332,
            "name": "Walmart"
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "origin_addresses": ["123 Main St, Gainesville, FL"],
            "destination_addresses": ["1234 SW 14th St, Gainesville, FL 32608"],
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {"value": 5000},
                    "duration": {"value": 600}
                }]
            }]
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "Walmart",
            "mode": "driving"
        })

        assert result["success"] is True
        assert mock_resolve.called
        assert result["resolved_destination"] == "1234 SW 14th St, Gainesville, FL 32608"

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.resolve_destination")
    def test_get_distance_to_location_with_full_address(self, mock_resolve, mock_http_client):
        """Test distance calculation with a full address destination (no resolution needed)."""
        # When destination has street number, resolve_destination should NOT be called
        mock_resolve.return_value = {"success": False, "error": "Not called for full addresses"}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "origin_addresses": ["123 Main St, Gainesville, FL"],
            "destination_addresses": ["567 Oak Ave, Gainesville, FL"],
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {"value": 3000},
                    "duration": {"value": 480}
                }]
            }]
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "567 Oak Ave, Gainesville, FL",
            "mode": "driving"
        })

        assert result["success"] is True
        assert not mock_resolve.called  # Resolution not called for full address
        assert result["resolved_destination"] == "567 Oak Ave, Gainesville, FL"

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.resolve_destination")
    def test_get_distance_to_location_places_api_fallback_to_nominatim(self, mock_resolve, mock_http_client):
        """Test fallback to Nominatim when Places API fails."""
        mock_resolve.return_value = {
            "success": False,
            "error": "Google Places API found no results"
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "origin_addresses": ["123 Main St, Gainesville, FL"],
            "destination_addresses": ["Walmart, Gainesville, FL"],
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {"value": 6000},
                    "duration": {"value": 720}
                }]
            }]
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "Walmart",
            "mode": "driving"
        })

        assert result["success"] is True
        assert "Nominatim fallback" in result.get("resolved_via", "")

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.resolve_destination")
    def test_get_distance_to_location_places_api_fallback_no_result(self, mock_resolve, mock_http_client):
        """Test error when both Places API and Nominatim fail."""
        mock_resolve.return_value = {
            "success": False,
            "error": "Could not resolve destination"
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ZERO_RESULTS",
            "error_message": "No results found"
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.get_distance_to_location.invoke({
            "apartment_address": "123 Main St, Gainesville, FL",
            "destination": "NonExistentPlace12345",
            "mode": "driving"
        })

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.httpx.Client")
    def test_resolve_destination_success(self, mock_http_client):
        """Test resolve_destination tool with successful resolution."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "candidates": [{
                "formatted_address": "1234 SW 14th St, Gainesville, FL 32608",
                "name": "Walmart Supercenter",
                "geometry": {
                    "location": {
                        "lat": 29.6595,
                        "lng": -82.3332
                    }
                }
            }]
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.resolve_destination.invoke({
            "placeholder": "Walmart",
            "location_bias": "Gainesville, FL"
        })

        assert result["success"] is True
        assert result["formatted_address"] == "1234 SW 14th St, Gainesville, FL 32608"
        assert result["name"] == "Walmart Supercenter"

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.httpx.Client")
    def test_resolve_destination_no_results(self, mock_http_client):
        """Test resolve_destination when no results found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ZERO_RESULTS",
            "candidates": []
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.resolve_destination.invoke({
            "placeholder": "NonExistentPlace12345"
        })

        assert result["success"] is False
        assert "no results" in result["error"].lower()

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.httpx.Client")
    def test_get_distances_batch_success(self, mock_http_client):
        """Test batch distance calculation with multiple origins."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "origin_addresses": [
                "123 Main St, Gainesville, FL",
                "456 Oak Ave, Gainesville, FL"
            ],
            "destination_addresses": ["Walmart, Gainesville, FL"],
            "rows": [{
                "elements": [
                    {
                        "status": "OK",
                        "distance": {"value": 5000},
                        "duration": {"value": 600}
                    },
                    {
                        "status": "OK",
                        "distance": {"value": 8000},
                        "duration": {"value": 900}
                    }
                ]
            }]
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.get_distances_batch.invoke({
            "origins": [
                "123 Main St, Gainesville, FL",
                "456 Oak Ave, Gainesville, FL"
            ],
            "destination": "Walmart, Gainesville, FL",
            "mode": "driving"
        })

        assert result["success"] is True
        assert result["origin_count"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["distance_km"] == 5.0
        assert result["results"][1]["distance_km"] == 8.0

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.httpx.Client")
    def test_get_distances_batch_empty_origins(self, mock_http_client):
        """Test batch distance calculation with empty origins list."""
        result = tools.get_distances_batch.invoke({
            "origins": [],
            "destination": "Walmart, Gainesville, FL"
        })

        assert result["success"] is False
        assert "must contain at least one address" in result["error"]

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_api_key"})
    @patch("app.agents.tools.httpx.Client")
    def test_get_distances_batch_all_fail(self, mock_http_client):
        """Test batch distance calculation when all routes fail."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{
                "elements": [
                    {"status": "NOT_FOUND", "errors": [{"message": "Destination not found"}]},
                    {"status": "NOT_FOUND", "errors": [{"message": "Destination not found"}]}
                ]
            }]
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_client_instance

        result = tools.get_distances_batch.invoke({
            "origins": [
                "123 Main St, Gainesville, FL",
                "456 Oak Ave, Gainesville, FL"
            ],
            "destination": "NonExistentPlace12345",
            "mode": "driving"
        })

        assert result["success"] is False
        assert "No routes found" in result["error"]
