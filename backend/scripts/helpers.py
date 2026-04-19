def extract_amenities_description(listing_data):
    """
    Extract all amenity text from listing details as a simple string.
    """
    description_parts = []

    # Extract from details field
    if 'details' in listing_data and listing_data['details']:
        for detail_group in listing_data['details']:
            if 'text' in detail_group and isinstance(detail_group['text'], list):
                for item in detail_group['text']:
                    cleaned_item = item.strip().rstrip('*')
                    if cleaned_item:
                        description_parts.append(cleaned_item)
    # Join all parts with comma space
    description = ", ".join(description_parts)
    return description


from typing import Optional, Dict, List
from app.database.mongo import get_listings_collection

def get_listings_email(listing_id: str) -> Optional[str]:
    """
    Get the contact email for a specific listing by listing_id.

    Args:
        listing_id: The listing_id to look up

    Returns:
        str: The email address if found, None otherwise
    """
    collection = get_listings_collection()
    listing = collection.find_one({"listing_id": listing_id})

    if listing:
        return listing.get("email")
    return None


def get_listings_emails(listing_ids: List[str]) -> Dict[str, Optional[str]]:
    """
    Get contact emails for multiple listings.

    Args:
        listing_ids: List of listing_id values to look up

    Returns:
        dict: Mapping of listing_id to email (or None if not found)
    """
    if not listing_ids:
        return {}

    collection = get_listings_collection()

    # Query all listings at once
    query = {"listing_id": {"$in": listing_ids}}
    listings = collection.find(query)

    # Build mapping
    emails = {}
    for listing in listings:
        listing_id = listing.get("listing_id")
        email = listing.get("email")
        if listing_id:
            emails[listing_id] = email

    return emails
