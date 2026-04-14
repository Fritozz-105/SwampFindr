"""Shared listing helper utilities."""
from datetime import datetime

from app.database import get_units_collection


def _serialize_datetimes(doc: dict) -> dict:
    """Convert any datetime values in a document to ISO strings for JSON safety."""
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc


def attach_units(listings: list) -> list:
    """Attach units from the Units collection to each listing (mutates in place)."""
    if not listings:
        return listings

    listing_ids = [listing["listing_id"] for listing in listings]
    units_collection = get_units_collection()
    all_units = list(units_collection.find(
        {"listing_id": {"$in": listing_ids}},
        {"_id": 0},
    ))

    units_by_listing: dict = {}
    for unit in all_units:
        _serialize_datetimes(unit)
        lid = unit["listing_id"]
        units_by_listing.setdefault(lid, []).append(unit)

    for listing in listings:
        _serialize_datetimes(listing)
        listing["units"] = units_by_listing.get(listing["listing_id"], [])

    return listings
