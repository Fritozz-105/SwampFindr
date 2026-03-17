from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.agents.agent import run_agent
from app.auth import require_auth

agent = Namespace('agent', description='Agent-based apartment search operations')


query_model = agent.model('Query', {
    'query': fields.String(required=True, description='User query for apartment search'),
})


response_model = agent.model('Response', {
    'success': fields.Boolean(description='If agent run succeeded'),
    'response': fields.String(description='Agent response'),
    'error': fields.String(description='Error message when request fails'),
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
        if result.get("success"):
            return result, 200

        error = result.get("error", "")
        if "timed out" in error.lower():
            return result, 504
        return result, 502

