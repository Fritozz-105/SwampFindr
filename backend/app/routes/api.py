"""API endpoints for listings."""
from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
import sys
sys.path.append('..')  # Allow import from parent directory
from models import ListingModel, UnitModel
from app.utils.pydantic_to_restx import pydantic_to_restx_model
from app.database import get_listings_collection, get_units_collection

api = Namespace('listings', description='Apartment listings operations')

# Convert Pydantic models to Flask-RESTX models for Swagger
listing_model = pydantic_to_restx_model(api, ListingModel, 'Listing')
unit_model = pydantic_to_restx_model(api, UnitModel, 'Unit')

# API response wrapper models
listing_response = api.model('ListingResponse', {
    'success': fields.Boolean(description='Success status'),
    'data': fields.List(fields.Nested(listing_model)),
    'count': fields.Integer(description='Number of listings'),
})

unit_response = api.model('UnitResponse', {
    'success': fields.Boolean(description='Success status'),
    'data': fields.List(fields.Nested(unit_model)),
    'count': fields.Integer(description='Number of units'),
})


@api.route('/')
class ListingList(Resource):
    """Listing collection endpoint."""
    
    @api.doc('list_listings')
    @api.marshal_with(listing_response)
    @api.doc(params={
        'city': 'Filter by city',
        'sqftMin': 'Minimum square footage'
    })
    def get(self):
        """Get all listings with optional filters."""
        try:
            listings_collection = get_listings_collection()
            
            # Build query filter
            query = {}
            
            # Filter by city
            city = request.args.get('city')
            if city:
                query['city'] = {'$regex': city, '$options': 'i'}
            
            # Filter by minimum square footage
            sqft_min = request.args.get('sqftMin', type=int)
            if sqft_min is not None:
                query['sqft_min'] = {'$gte': sqft_min}
            
            # Filter by maximum square footage
            # Fetch listings from MongoDB
            listings = list(listings_collection.find(query).limit(100))
            
            # Convert ObjectId to string for JSON serialization
            for listing in listings:
                listing['_id'] = str(listing['_id'])
            
            return {
                'success': True,
                'data': listings,
                'count': len(listings)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'count': 0
            }, 500
    



@api.route('/<string:listing_id>')
@api.param('listing_id', 'The listing identifier')
class Listing(Resource):
    """Individual listing endpoint."""
    
    @api.doc('get_listing')
    @api.response(404, 'Listing not found')
    def get(self, listing_id):
        """Get a specific listing by ID."""
        try:
            listings_collection = get_listings_collection()
            units_collection = get_units_collection()
            
            # Find listing by listing_id
            listing = listings_collection.find_one({'listing_id': listing_id})
            
            if not listing:
                return {
                    'success': False,
                    'error': 'Listing not found'
                }, 404
            
            # Get associated units
            units = list(units_collection.find({'listing_id': listing_id}))
            
            # Convert ObjectId to string
            listing['_id'] = str(listing['_id'])
            for unit in units:
                unit['_id'] = str(unit['_id'])
            
            listing['units'] = units
            
            return {
                'success': True,
                'data': listing
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500