from flask import request, g
from flask_restx import Namespace, Resource, fields, marshal
from app.agents.agent import run_agent
from app.auth import require_auth
from app.extensions import limiter
from app.services.conversation_service import (
    create_thread_for_user,
    touch_thread,
    user_owns_thread,
)

agent = Namespace('agent', description='Agent-based apartment search operations')

MAX_QUERY_LENGTH = 2000


query_model = agent.model('Query', {
    'query': fields.String(required=True, description='User query for apartment search'),
    'thread_id': fields.String(required=False, description='Existing thread id; omit to create new conversation'),
})


response_model = agent.model('Response', {
    'success': fields.Boolean(description='If agent run succeeded'),
    'response': fields.String(description='Agent response'),
    'thread_id': fields.String(description='Conversation thread id used for this response'),
    'is_new_thread': fields.Boolean(description='Whether a new thread was created for this request'),
    'listings': fields.List(fields.Raw, description='Listing objects from agent tool calls'),
    'error': fields.String(description='Error message when request fails'),
    'error_type': fields.String(description='Error category'),
})


@agent.route('/')
class AgentChat(Resource):
    """Agent chat endpoint."""
    decorators = [limiter.limit("10/minute")]

    @agent.expect(query_model)
    @agent.doc(security="Bearer")
    @agent.marshal_with(response_model)
    @require_auth
    def post(self):
        """Handle user query and generate agent response."""
        data = request.json
        if not data or not data.get('query'):
            return {
                'success': False,
                'response': "",
                "error": "Query parameter is missing",
                "error_type": "Missing field",
                "thread_id": None,
                "is_new_thread": False,
                "listings": [],
            }, 400

        if len(data['query']) > MAX_QUERY_LENGTH:
            return {
                'success': False,
                'response': "",
                "error": f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters",
                "error_type": "Invalid input",
                "thread_id": None,
                "is_new_thread": False,
                "listings": [],
            }, 400

        provided_thread_id = data.get('thread_id')
        is_new_thread = False

        if provided_thread_id:
            if not user_owns_thread(g.user_id, provided_thread_id):
                return {
                    'success': False,
                    'response': "",
                    'error': 'thread_id not found for user',
                    'error_type': 'Invalid thread',
                    'thread_id': provided_thread_id,
                    'is_new_thread': False,
                    'listings': [],
                }, 403
            thread_id = provided_thread_id
        else:
            thread = create_thread_for_user(g.user_id)
            thread_id = thread['thread_id']
            is_new_thread = True

        result = run_agent(data.get('query'), thread_id=thread_id)
        if result.get('error'):
            result['thread_id'] = thread_id
            result['is_new_thread'] = is_new_thread
            if result.get('error_type') == 'timeout':
                return result, 504
            return {
                'success': False,
                'response': "",
                'error': result['error'],
                'error_type': result.get('error_type'),
                'thread_id': thread_id,
                'is_new_thread': is_new_thread,
                'listings': [],
            }, 502

        touch_thread(g.user_id, thread_id)
        result['thread_id'] = thread_id
        result['is_new_thread'] = is_new_thread
        return result, 200

