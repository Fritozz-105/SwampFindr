from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.agents.agent import run_agent
from app.auth import require_auth

agent = Namespace('agent', description='Agent-based apartment search operations')


query_model = agent.model('Query', {
    'query': fields.String(required=True, description='User query for apartment search'),
    'thread_id': fields.String(require=False, description='Thread ID'),
})


response_model = agent.model('Response', {
    'success': fields.Boolean(description='If agent run succeeded'),
    'response': fields.String(description='Agent response'),
    'error': fields.String(description='Error message when request fails'),
    'error_type': fields.String(description='Error category'),
    'thread_id': fields.String(description='Chat thread ID'),
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
            return {
                'success': False,
                'response': "",
                "error" : "Query parameter is missing" ,
                "error_type" : "Missing field",
                "thread_id" : None
            }, 400
        result = run_agent(data.get('query'), g.user_id, data.get('thread_id'))
        if result.get("success"):
            return result, 200

        if result.get('error_type') == 'timeout':
            return result, 504
        return result, 502

