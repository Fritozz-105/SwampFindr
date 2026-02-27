from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from app.agents.agent import run_agent

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
    def post(self):
        """Handle user query and generate agent response."""
        data = request.json
        if not data or not data.get('query'):
            agent.abort(400, 'Query is required')
        result = run_agent(data.get('query'))
        return result, 200

