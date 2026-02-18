#file that pulls listing data from the api and other sources and saves it to database. Runs as a cron job to update listings
import http.client
import json
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Add parent directory to path
from models import ListingModel, UnitModel
from langchain_ollama import OllamaLLM
from pymongo import MongoClient

load_dotenv() 

headers = {
    'x-rapidapi-key': os.getenv('RAPIDAPI_KEY'),
    'x-rapidapi-host': "realtor16.p.rapidapi.com"
}

all_listings = []

for page in range(1, 5):
    conn = http.client.HTTPSConnection("realtor16.p.rapidapi.com")
    conn.request("GET", f"/search/forrent/coordinates?latitude=29.6502711&longitude=-82.3416219&radius=15&page={page}&type=apartment", headers=headers)
    
    res = conn.getresponse()
    data = res.read()
    page_data = json.loads(data.decode("utf-8"))
    if "properties" not in page_data:
        print(f"Error fetching page {page}: {page_data}")
        raise Exception(f"API error on page {page}")
    all_listings.extend(page_data["properties"])
    conn.close()

mongo_listings = []
mongo_units = []
skip =0
#processing all_listings
for prop in all_listings:
    if not prop["units"] or not prop["description"]["sqft_max"] or not prop["description"]["sqft_min"] or not prop["description"]["baths_max"] or not prop["description"]["baths_min"] or not prop["description"]["beds_max"] or not prop["list_price_max"] or not prop["list_price_min"] or not prop["description"]["beds_min"]:
        skip+=1
        continue
    mongo_listings.append(ListingModel.from_dict(prop))
    mongo_units.extend([UnitModel.from_dict(unit,prop["listing_id"],prop["property_id"]) for unit in prop["units"]])

#Summary output
print(f"Total listings fetched: {len(all_listings)}")
print(f"Listings with complete data: {len(mongo_listings)}")
print(f"Units extracted: {len(mongo_units)}")
print(f"Listings skipped due to incomplete data: {skip}") 

print("Connecting to MongoDB and inserting data...")
client = MongoClient(os.getenv('URI'))
db = client['Property']
listings_collection = db['Listings']
units_collection = db['Units']
print("Connected to MongoDB. Clearing existing data and inserting new listings and units...")
# Clear existing data
listings_collection.delete_many({})
units_collection.delete_many({})
# Insert new data
listings_collection.insert_many([listing.model_dump() for listing in mongo_listings])
units_collection.insert_many([unit.model_dump() for unit in mongo_units])




