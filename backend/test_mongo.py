"""Flask dev server that mocks Pinecone, LangChain, and OpenAI.

Use this instead of run.py when you don't have API keys for external services.
Only requires the MongoDB URI env var.

Run from backend/:  uv run python test_mongo.py
"""

import os
import sys
from unittest.mock import MagicMock
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Mock every external service module BEFORE importing anything from `app`.
# The import chain: app → app.routes → app.routes.agent → app.agents.agent
#   → langchain, langchain_openai, pinecone, app.agents.tools
# All of these fail without API keys, so we intercept them here.
# ---------------------------------------------------------------------------

for mod_name in [
    "pinecone",
    "langchain",
    "langchain.agents",
    "langchain_openai",
    "langchain_core",
    "langchain_core.tools",
    "langchain_core.tools.convert",
    "langchain_core.tools.structured",
]:
    sys.modules[mod_name] = MagicMock()

# Mock app-level modules that depend on those externals
sys.modules["app.agents"] = MagicMock()
sys.modules["app.agents.agent"] = MagicMock()
sys.modules["app.agents.tools"] = MagicMock()
sys.modules["app.agents.prompts"] = MagicMock()
sys.modules["app.services.pinecone_service"] = MagicMock()

# Now safe to import app
from app import create_app  # noqa: E402
from app.config import config_by_name  # noqa: E402

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_by_name.get(config_name, config_by_name["default"]))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    print(f"\n  Running with mocked externals (Pinecone, LangChain, OpenAI)")
    print(f"  Agent/vector endpoints will return mock responses\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
