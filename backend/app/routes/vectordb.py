from flask import request
from flask_restx import Namespace, Resource, fields
from app.services.pinecone_service import upsert_record, query_records
from app.auth import require_auth


vectordb = Namespace("vectordb", description="Pinecone API")


upsert_model = vectordb.model('UpsertRequest', {
    'chunk_text': fields.String(required=True, description='Text to embed'),
    'category': fields.String(required=True, description='Category of the record'),
})


query_model = vectordb.model('QueryRequest', {
    'query_text': fields.String(required=True, description='Text to use as query'),
    'namespace': fields.String(required=True, description='Namespace to search in'),
    'top_k': fields.Integer(default=5, description='k nearest matches'),
})


upsert_response =  vectordb.model('UpsertResponse', {
    'id': fields.String(description='Generated record ID'),
    'status': fields.String(description='Status message'),
})


@vectordb.route('/upsert')
class Upsert(Resource):
    @vectordb.expect(upsert_model)
    @vectordb.marshal_with(upsert_response)
    @vectordb.doc(security="Bearer")
    @require_auth
    def post(self):
        """Upsert an embedding to the main namespace"""
        return {"id": upsert_record(request.json["chunk_text"], request.json["category"]), "status": "Upserted successfully!"}


@vectordb.route('/upsert-test')
class UpsertTest(Resource):
    @vectordb.expect(upsert_model)
    @vectordb.marshal_with(upsert_response)
    @vectordb.doc(security="Bearer")
    @require_auth
    def post(self):
        """Upsert a record into the test namespace."""
        return {"id": upsert_record(request.json["chunk_text"], request.json["category"], ns="test"), "status": "Upserted successfully!"}


@vectordb.route('/query')
class Query(Resource):
    @vectordb.expect(query_model)
    @vectordb.doc(security="Bearer")
    @require_auth
    def post(self):
        """Query database for similar records"""
        return {"results": query_records(request.json["query_text"], request.json["namespace"], request.json.get("top_k", 3))}

