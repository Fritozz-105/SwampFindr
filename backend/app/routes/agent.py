from flask import request, jsonify
from flask_restx import Namespace, Resource, fields


agent = Namespace('agent', description='Agent-based apartment search operations')

query_model = agent.model('Query', {
    'query': fields.String(required=True, description='User query for apartment search'),
})

@agent.route('/')
class AgentChat(Resource):
    """Agent chat endpoint."""
    
    @agent.doc('agent_chat')
    @agent.marshal_with(query_model)
    @agent.response(200, 'Agent response generated successfully')
    def post(self):
        """Handle user query and generate agent response."""
        data = request.json
        user_query = data.get('query')
        return {'query': user_query}, 200