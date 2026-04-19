"""
Add email field to all listings in MongoDB.

This script updates the Listings collection to add a contact email
(swampfindr@gmail.com) for testing property contact features.

Usage:
    python add_email_to_listings.py
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.database.mongo import get_listings_collection


CONTACT_EMAIL = "swampfindr@gmail.com"


def add_email_to_listings():
    """
    Add email field to all listings in the Listings collection.

    Uses MongoDB's $set operator to add the email field without
    modifying other fields. Existing documents that already have an
    email field will have it overwritten.

    Returns:
        dict: Summary of operation including count of listings updated
    """
    collection = get_listings_collection()

    # Get total count of listings
    total = collection.count_documents({})

    if total == 0:
        print("No listings found in MongoDB. Nothing to update.")
        return {"status": "no_data", "count": 0}

    print(f"Found {total} listings in MongoDB.")
    print(f"Adding email: {CONTACT_EMAIL}")
    print("-" * 50)

    # Update all listings with the email field
    # Using update_many with update pipeline for efficiency
    result = collection.update_many(
        {},
        [
            {"$set": {"email": CONTACT_EMAIL}}
        ]
    )

    # Report results
    modified = result.modified_count
    matched = result.matched_count
    # mismatched_count doesn't exist in pymongo, it's always 0 for update_many with no filter
    mismatched = 0

    print(f"Updated:  {modified} listings (had no email field)")
    print(f"Matched:  {matched} listings")
    print(f"Mismatch: {mismatched} listings (not found)")

    print(f"\nTotal listings now with email field: {matched}")

    return {
        "status": "success",
        "matched": matched,
        "modified": modified,
        "mismatched": mismatched,
        "email": CONTACT_EMAIL
    }


def validate_email_field(listing: dict) -> bool:
    """
    Check if a listing document has the email field set.

    Args:
        listing: A listing document dict from MongoDB

    Returns:
        bool: True if email field exists and is set
    """
    return "email" in listing and listing.get("email") == CONTACT_EMAIL


if __name__ == "__main__":
    result = add_email_to_listings()

    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)

    if result["status"] == "success":
        print(f"Successfully added email to {result['modified']} listings.")
        print(f"All {result['matched']} listings now have email: {CONTACT_EMAIL}")
    else:
        print(f"No listings to process.")

    print("=" * 50)
