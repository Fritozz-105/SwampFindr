"""Shared listing helper utilities."""
from datetime import datetime

from app.database import get_units_collection


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
        if isinstance(unit.get("availability"), datetime):
            unit["availability"] = unit["availability"].isoformat()
        lid = unit["listing_id"]
        units_by_listing.setdefault(lid, []).append(unit)

    for listing in listings:
        listing["units"] = units_by_listing.get(listing["listing_id"], [])

    return listings
