from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.agents.agent import run_agent
from app.auth import require_auth

agent = Namespace('agent', description='Agent-based apartment search operations')


query_model = agent.model('Query', {
    'query': fields.String(required=True, description='User query for apartment search'),
})


response_model = agent.model('Response', {
    'response': fields.String(description='Agent response'),
})


@agent.route('/')
class AgentChat(Resource):
    """Agent chat endpoint."""
    @agent.expect(query_model)
    @agent.marshal_with(response_model)
    @agent.doc(security="Bearer")
    @require_auth
    def post(self):
        """Handle user query and generate agent response."""
        data = request.json
        if not data or not data.get('query'):
            agent.abort(400, 'Query is required')
        result = run_agent(data.get('query'), user_id=g.user_id)
        return result, 200

