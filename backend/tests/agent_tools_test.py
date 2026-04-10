# tests/agent_tools_test.py
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock
import httpx
import os

load_dotenv()

from app.agents.tools import (
    decode_coordinates,
    closest_bus_stops,
    get_crimes_nearby,
    semantic_search,
    suggest_listing,
    swipe_on_listing,
    update_preference_embedding
)
from pymongo import MongoClient

UF_LATITUDE = 29.6516
UF_LONGITUDE = -82.3248


def get_mongo_client():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI not set in .env file")
    return MongoClient(uri)


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