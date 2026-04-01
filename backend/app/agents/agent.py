from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import os
import httpx
import time
import ast
import json
import re
from dotenv import load_dotenv
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import get_tools as tools
from app.agents.user_context import set_current_user_id, reset_current_user_id
from app.database.mongo import get_mongo_client
from app.services.conversation_service import get_user_id_for_thread
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver

load_dotenv()

openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
openai_base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None # make base_url empty in .env then it will use OPENAI url
if openai_api_key:
    model = ChatOpenAI(
        model="gpt-oss-120b",
        temperature=0.1,
        max_tokens=2048,
        timeout=30,
        api_key=openai_api_key,
        base_url=openai_base_url,
    )
else:
    print("OPENAI_API_KEY not set. Using Ollama (llama3-groq-tool-use:latest).")
    model = ChatOllama(
        model="llama3-groq-tool-use:latest",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.1,
        num_predict=2048,
    )

try:
    checkpointer = MongoDBSaver(
        client=get_mongo_client(),
        db_name="UserData",
    )
except Exception as e:
    print(f"MongoDB checkpointer initialization failed: {e}. Falling back to in-memory checkpointer.")
    checkpointer = InMemorySaver()

agent = create_agent(
    model,
    tools=tools(),
    system_prompt=SYSTEM_PROMPT,
    checkpointer =checkpointer,
)


def _is_timeout_error(error: Exception) -> bool:
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return True
    current = error
    while current:
        if "timeout" in current.__class__.__name__.lower():
            return True
        current = current.__cause__
    return False


def _as_text(content) -> str:
    """Normalize the agent response into str format"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts).strip()
    return str(content or "")

# next 3 functions are tools to return listings in agent chat
def _python_repr_to_json(s: str) -> str:
    """Best-effort conversion of a Python repr string to valid JSON."""
    s = re.sub(r'datetime\.datetime\([^)]*\)', 'null', s)
    s = re.sub(r"ObjectId\(['\"]([^'\"]*)['\"\)]\)", r'"\1"', s)
    s = re.sub(r'\bTrue\b', 'true', s)
    s = re.sub(r'\bFalse\b', 'false', s)
    s = re.sub(r'\bNone\b', 'null', s)
    s = s.replace("'", '"')
    return s


def _parse_tool_content(raw) -> dict | list | None:
    """Parse tool message content that may be a dict, JSON string, or Python repr string."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        result = ast.literal_eval(raw)
        if isinstance(result, (dict, list)):
            return result
    except (ValueError, SyntaxError):
        pass
    try:
        return json.loads(_python_repr_to_json(raw))
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _extract_listings(messages: list) -> list:
    """Extract listing data from ToolMessage objects after the last user message."""
    # Only look at messages from the current turn (after the last human/user message)
    last_human_idx = -1
    for i, m in enumerate(messages):
        if m.type in ("human",):
            last_human_idx = i
    recent = messages[last_human_idx + 1:] if last_human_idx >= 0 else messages

    listings = []
    for m in recent:
        if m.type != "tool":
            continue
        content = _parse_tool_content(m.content)
        if isinstance(content, dict) and content.get("success") and "listings" in content:
            listings.extend(content["listings"])
    return listings


# Return thread history
def get_history(thread_id: str) -> list:
    config = {"configurable": {"thread_id": thread_id}}
    state  = agent.get_state(config)
    if not state or not state.values.get("messages"):
        return []
    role_map = {
        "human":  "user",
        "ai": "assistant",
        "system": "system",
    }
    history = []
    for m in state.values["messages"]:
        if m.type in ("tool",):
            continue
        content = m.content
        if not content:
            continue
        history.append({
            "role":    role_map.get(m.type, m.type),
            "content": content,
        })
    return history


# Simple invocation of the agent
def run_agent(user_query: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    tkn = set_current_user_id(get_user_id_for_thread(thread_id))
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            config=config
        )
    except Exception as e:
        if _is_timeout_error(e):
            return {
                "success" : False,
                "response" : "",
                "listings" : [],
                "error" : "Request timed out",
                "error_type" : 'timeout',
                "thread_id" : thread_id,
            }
        return {
            "success" : False,
            "response" : "",
            "listings" : [],
            "error" : f"Agent error | {e}",
            "error_type" : type(e).__name__,
            "thread_id" : thread_id,
        }
    finally:
        reset_current_user_id(tkn)

    msgs = response.get('messages', [])
    if not msgs:
        return {
            "success" : False,
            "response" : "",
            "listings" : [],
            "error" : "No messages received",
            "error_type" : "Empty payload",
            "thread_id" : thread_id,
        }
    return {
        "success" : True,
        "response" : _as_text(msgs[-1].content),
        "listings" : _extract_listings(msgs),
        "error" : None,
        "error_type" : None,
        "thread_id" : thread_id,
    }


# Stream the agent responses
def run_agent_stream(user_query: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    tkn = set_current_user_id(get_user_id_for_thread(thread_id))
    try:
        for chunk, metadata in agent.stream(
            {"messages": [HumanMessage(content=user_query)]},
            config=config,
            stream_mode="messages"
        ):
            if chunk.type == "AIMessageChunk" and chunk.content:
                yield chunk.content
    except Exception as e:
        if _is_timeout_error(e):
            yield "[error: timed out]"
            return
        yield f"[error: {e}]"
    finally:
        reset_current_user_id(tkn)


if __name__ == "__main__":
    thread_id = "test-1"
    print("Agent started... Type 'QUIT' to exit.\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        print("Agent: ", end="", flush=True)
        for chunk in run_agent_stream(query, thread_id=thread_id):
            print(chunk, end="", flush=True)
            time.sleep(0.01)
        print("\n")
