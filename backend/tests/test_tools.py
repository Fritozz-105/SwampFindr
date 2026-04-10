import pytest
import os
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from app.agents import tools
from app.agents.tools import (
    decode_coordinates,
    closest_bus_stops,
    get_crimes_nearby,
    semantic_search,
    suggest_listing,
    swipe_on_listing,
    update_preference_embedding
)
import httpx
# Load environment variables from .env file
load_dotenv()

UF_LATITUDE = 29.6516
UF_LONGITUDE = -82.3248


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


class TestDecodeCoordinates:
    '''Tests decode_coordinates tool'''
    def test_decode_uf(self):
        result = decode_coordinates.invoke({'location' : 'University of Florida'})
        assert result['success'] is True
        assert 29.0 < result['lat'] < 30.0
        assert -83.0 < result["lng"] < -82.0


    def test_decode_butler_plaza(self):
        result = decode_coordinates.invoke({"location": "Butler Plaza Gainesville FL"})
        assert result["success"] is True


    def test_decode_uf_health(self):
        result = decode_coordinates.invoke({"location": "UF Health Shands Hospital Gainesville"})
        assert result["success"] is True


    def test_decode_empty_string(self):
        result = decode_coordinates.invoke({"location": ""})
        assert result["success"] is False
        assert "error" in result


    def test_decode_whitespace(self):
        result = decode_coordinates.invoke({"location": "   "})
        assert result["success"] is False


    def test_decode_fake_place(self):
        result = decode_coordinates.invoke({"location": "xyzxyzxyz_fake_place_99999"})
        assert result["success"] is False


class TestBusStops:
    '''Tests closest_bus_stops tool'''
    def test_bus_stops_uf_campus(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 800})
        assert "stops" in result
        assert "count" in result


    def test_bus_stops_downtown(self):
        result = closest_bus_stops.invoke({"lat": 29.6520, "lng": -82.3250, "radius_m": 500})
        assert "stops" in result
        assert 'count' in result


    def test_bus_stops_large_radius(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 5000})
        assert "stops" in result
        assert result["count"] >= 0


    def test_bus_stops_default_radius(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE})
        assert "stops" in result
        assert 'count' in result


    def test_bus_stops_tiny_radius_empty(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 1})
        assert result["stops"] == []
        assert 'count' in result
        assert result['count'] == 0


    def test_bus_stops_invalid_lat(self):
        result = closest_bus_stops.invoke({"lat": 999, "lng": UF_LONGITUDE})
        assert "error" in result


    def test_bus_stops_invalid_lng(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": 999})
        assert "error" in result


    def test_bus_stops_radius_too_large(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 99999})
        assert "error" in result


    def test_bus_stops_have_distance_field(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 1000})
        if result["count"] > 0:
            assert "distance_m" in result["stops"][0]


    def test_bus_stops_sorted_by_distance(self):
        result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 2000})
        if result["count"] > 1:
            distances = [s["distance_m"] for s in result["stops"]]
            assert distances == sorted(distances)


class TestCrimesNearby:
    '''Tests get_crimes_nearby tool'''
    @patch('httpx.Client')
    def test_crimes_nearby_valid(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "report_date": "2024-01-15",
                "offense_date": "2024-01-15",
                "narrative": "Theft",
                "address": "123 Main St",
                "latitude": 29.6436,
                "longitude": -82.3549,
            },
            {
                "report_date": "2024-01-14",
                "offense_date": "2024-01-14",
                "narrative": "Robbery",
                "address": "456 Oak Ave",
                "latitude": 29.6450,
                "longitude": -82.3550,
            },
        ]
        mock_response.raise_for_status.return_value = None
        mock_client_class.return_value.__enter__.return_value.get.return_value = mock_response
        result = get_crimes_nearby.invoke({
            'lat' : UF_LATITUDE,
            'lng' : UF_LONGITUDE,
            'radius' : 800,
            'limit': 50
        })

        assert result['success'] is True
        assert result['count'] == 2
        assert len(result['incidents']) == 2
        assert result['radius_m'] == 800
        assert 'source' in result


    @patch('httpx.Client')
    def test_crimes_nearby_empty(self, mock_client_class):
        '''Test when no crimes are found in the area'''
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_client_class.return_value.__enter__.return_value.get.return_value = mock_response

        result = get_crimes_nearby.invoke({
            'lat' : UF_LATITUDE,
            'lng' : UF_LONGITUDE,
            'radius' : 500
        })

        assert result['success'] is True
        assert result['count'] == 0
        assert len(result['incidents']) == 0
        assert result['summary'] == {}


    def test_crimes_nearby_invalid_latitude_too_high(self):
        result = get_crimes_nearby.invoke({"lat": 100, "lng": UF_LONGITUDE})
        assert result["success"] is False
        assert "Latitude must be between -90 and 90" in result["error"]


    def test_crimes_nearby_invalid_latitude_too_low(self):
        result = get_crimes_nearby.invoke({"lat": -100, "lng": UF_LONGITUDE})
        assert result["success"] is False
        assert "Latitude must be between -90 and 90" in result["error"]


    def test_crimes_nearby_invalid_longitude_too_high(self):
        result = get_crimes_nearby.invoke({"lat": UF_LATITUDE, "lng": 200})
        assert result["success"] is False
        assert "Longitude must be between -180 and 180" in result["error"]


    def test_crimes_nearby_invalid_longitude_too_low(self):
        result = get_crimes_nearby.invoke({"lat": UF_LATITUDE, "lng": -200})
        assert result["success"] is False
        assert "Longitude must be between -180 and 180" in result["error"]


    def test_crimes_nearby_invalid_radius_negative(self):
        result = get_crimes_nearby.invoke({
            "lat": UF_LATITUDE,
            "lng": UF_LONGITUDE,
            "radius_m": -100
        })
        assert result["success"] is False
        assert "radius_m must be between 0 and 5000" in result["error"]


    def test_crimes_nearby_invalid_radius_zero(self):
        """Test rejection of zero radius."""
        result = get_crimes_nearby.invoke({
            "lat": UF_LATITUDE,
            "lng": UF_LONGITUDE,
            "radius_m": 0
        })
        assert result["success"] is False
        assert "radius_m must be between 0 and 5000" in result["error"]


    def test_crimes_nearby_invalid_radius_too_large(self):
        """Test rejection of radius > 5000m."""
        result = get_crimes_nearby.invoke({
            "lat": UF_LATITUDE,
            "lng": UF_LONGITUDE,
            "radius_m": 5001
        })
        assert result["success"] is False
        assert "radius_m must be between 0 and 5000" in result["error"]


    @patch('app.agents.tools.httpx.Client')
    def test_crimes_nearby_timeout(self, mock_client_class):
        """Test handling of connection timeout."""
        mock_client_class.return_value.__enter__.return_value.get.side_effect = httpx.ConnectTimeout("Timeout")

        result = get_crimes_nearby.invoke({
            "lat": UF_LATITUDE,
            "lng": UF_LONGITUDE
        })

        assert result["success"] is False
        assert "Connection timed out" in result["error"]


    @patch('app.agents.tools.httpx.Client')
    def test_crimes_nearby_http_error(self, mock_client_class):
        """Test handling of connection error."""
        mock_response = MagicMock()

        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            '400 Bad Request',
            request=MagicMock(),
            response=MagicMock()
        )

        mock_client_class.return_value.__enter__.return_value.get.return_value = mock_response

        result = get_crimes_nearby.invoke({
            "lat": UF_LATITUDE,
            "lng": UF_LONGITUDE
        })

        assert result["success"] is False
        assert "Crime data API returned an error" in result["error"]


    @patch('app.agents.tools.httpx.Client')
    def test_crimes_nearby_generic_exception(self, mock_client_class):
        """Test handling of generic exceptions during API call."""
        mock_client_class.return_value.__enter__.return_value.get.side_effect = Exception("Generic error")

        result = get_crimes_nearby.invoke({
            "lat": UF_LATITUDE,
            "lng": UF_LONGITUDE
        })

        assert result["success"] is False
        assert "Failed to fetch crime data" in result["error"]


    @patch('app.agents.tools.httpx.Client')
    def test_crimes_nearby_incident_format(self, mock_client_class):
        """Test that incidents are formatted right"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "report_date": "2024-01-15T14:30:00Z",
                "offense_date": "2024-01-15",
                "narrative": "Vehicle Theft",
                "address": "123 Best City Ave, Gainesville, FL",
                "latitude": 29.6436,
                "longitude": -82.3549,
            },
        ]
        mock_response.raise_for_status.return_value = None
        mock_client_class.return_value.__enter__.return_value.get.return_value = mock_response

        result = get_crimes_nearby.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE})

        assert result["success"] is True
        incident = result["incidents"][0]
        assert "date" in incident
        assert "offense" in incident
        assert "address" in incident
        assert "lat" in incident
        assert "lng" in incident
        assert incident["offense"] == "Vehicle Theft"
        assert incident["address"] == "123 Best City Ave, Gainesville, FL"
        assert incident["lat"] == 29.6436
        assert incident["lng"] == -82.3549