"""Embed all MongoDB listings into Pinecone for vector similarity search."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.database.mongo import get_listings_collection
from app.services.pinecone_service import upsert_record


def build_embedding_text(listing: dict) -> str:
  """Build embedding text from a listing document matching user preference format."""
  beds_min = listing.get("beds_min", "?")
  beds_max = listing.get("beds_max", "?")
  baths_min = listing.get("baths_min", "?")
  baths_max = listing.get("baths_max", "?")
  city = listing.get("city", "Unknown")
  price_min = listing.get("list_price_min", "?")
  price_max = listing.get("list_price_max", "?")
  sqft_min = listing.get("sqft_min", "?")
  sqft_max = listing.get("sqft_max", "?")
  details = listing.get("details", "")
  cats = "yes" if listing.get("cats") else "no"
  dogs = "yes" if listing.get("dogs") else "no"

  return (
    f"{beds_min}-{beds_max} bedroom, {baths_min}-{baths_max} bathroom "
    f"apartment in {city}. ${price_min}-${price_max}/month. "
    f"{sqft_min}-{sqft_max} sqft. {details}. "
    f"Pets: cats {cats}, dogs {dogs}."
  )


def embed_all_listings():
  """Fetch all listings from MongoDB and upsert embeddings into Pinecone."""
  collection = get_listings_collection()
  listings = list(collection.find({}))
  total = len(listings)

  if total == 0:
    print("No listings found in MongoDB.")
    return

  print(f"Embedding {total} listings...")

  for i, listing in enumerate(listings, 1):
    listing_id = listing.get("listing_id")
    if not listing_id:
      print(f"  Skipping listing {i}/{total}: no listing_id")
      continue

    text = build_embedding_text(listing)
    try:
      upsert_record(
        chunk_text=text,
        category="listing",
        ns="main",
        listing_id=listing_id,
      )
      print(f"Embedded {i}/{total}: {listing_id}")
    except Exception as e:
      print(f"Failed {i}/{total}: {listing_id} — {e}")

  print(f"Done. Processed {total} listings.")


if __name__ == "__main__":
  embed_all_listings()
