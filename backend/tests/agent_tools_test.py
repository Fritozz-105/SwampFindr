from app.agents.tools import (
    decode_coordinates,
    closest_bus_stops,
    get_crimes_nearby,
    semantic_search,
    suggest_listing,
    swipe_on_listing,
    update_preference_embedding
)

UF_LATITUDE = 29.6516
UF_LONGITUDE = -82.3248

# --------------------- Test decode coordinates tool --------------------------------------
def test_decode_uf():
    result = decode_coordinates.invoke({'location' : 'University of Florida'})
    assert result['success'] is True
    assert 29.0 < result['lat'] < 30.0
    assert -83.0 < result["lng"] < -82.0


def test_decode_butler_plaza():
    result = decode_coordinates.invoke({"location": "Butler Plaza Gainesville FL"})
    assert result["success"] is True


def test_decode_uf_health():
    result = decode_coordinates.invoke({"location": "UF Health Shands Hospital Gainesville"})
    assert result["success"] is True


def test_decode_empty_string():
    result = decode_coordinates.invoke({"location": ""})
    assert result["success"] is False
    assert "error" in result


def test_decode_whitespace():
    result = decode_coordinates.invoke({"location": "   "})
    assert result["success"] is False


def test_decode_fake_place():
    result = decode_coordinates.invoke({"location": "xyzxyzxyz_fake_place_99999"})
    assert result["success"] is False


# --------------------- Test Bus Stops tool --------------------------------------
def test_bus_stops_uf_campus():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 800})
    assert "stops" in result
    assert "count" in result


def test_bus_stops_downtown():
    result = closest_bus_stops.invoke({"lat": 29.6520, "lng": -82.3250, "radius_m": 500})
    assert "stops" in result
    assert 'count' in result


def test_bus_stops_large_radius():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 5000})
    assert "stops" in result
    assert result["count"] >= 0


def test_bus_stops_default_radius():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE})
    assert "stops" in result
    assert 'count' in result


def test_bus_stops_tiny_radius_empty():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 1})
    assert result["stops"] == []
    assert 'count' in result
    assert result['count'] == 0


def test_bus_stops_invalid_lat():
    result = closest_bus_stops.invoke({"lat": 999, "lng": UF_LONGITUDE})
    assert "error" in result

def test_bus_stops_invalid_lng():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": 999})
    assert "error" in result

def test_bus_stops_radius_too_large():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 99999})
    assert "error" in result


def test_bus_stops_have_distance_field():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 1000})
    if result["count"] > 0:
        assert "distance_m" in result["stops"][0]


def test_bus_stops_sorted_by_distance():
    result = closest_bus_stops.invoke({"lat": UF_LATITUDE, "lng": UF_LONGITUDE, "radius_m": 2000})
    if result["count"] > 1:
        distances = [s["distance_m"] for s in result["stops"]]
        assert distances == sorted(distances)

