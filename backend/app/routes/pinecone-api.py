from flask import request
from flask_restx import Namespace, Resource, fields
from backend.app.services.pinecone_service import upsert_record, query_records

api = Namespace("pinecone", description="Pinecone API")

upsert_model = api.model('UpsertRequest', {
    'chunk_text': fields.String(required=True, description='Text to embed'),
    'category': fields.String(required=True, description='Category of the record'),
})

query_model = api.model('QueryRequest', {
    'query_text': fields.String(required=True, description='Text to use as query'),
    'namespace': fields.String(required=True, description='Namespace to search in'),
    'top_k': fields.Integer(default=5, description='k nearest matches'),
})

upsert_response = api.model('UpsertResponse', {
    'id': fields.String(description='Generated record ID'),
    'status': fields.String(description='Status message'),
})

@api.route('/upsert')
class Upsert(Resource):
    @api.expect(upsert_model)
    @api.marshal_with(upsert_response)
    def post(self):
        """Upsert an embedding to the main namespace"""
        return {"id": upsert_record(request.json["chunk_text"], request.json["category"]), "status": "Upserted successfully!"}


@api.route('/upsert-test')
class UpsertTest(Resource):
    @api.expect(upsert_model)
    @api.marshal_with(upsert_response)
    def post(self):
        """Upsert a record into the test namespace."""
        return {"id": upsert_record(request.json["chunk_text"], request.json["category"], ns="test"), "status": "Upserted successfully!"}


@api.route('/query')
class Query(Resource):
    @api.expect(query_model)
    def post(self):
        """Query database for similar records"""
        return {"results": query_records(request.json["query_text"], request.json["namespace"], request.json.get("top_k", 3))}