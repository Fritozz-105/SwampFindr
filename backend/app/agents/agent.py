from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import HumanMessage, trim_messages
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import os
import httpx
import ast
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from deepeval.tracing import observe, update_current_span, update_current_trace
from deepeval.test_case import ToolCall
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import get_tools as tools
from app.agents.user_context import set_user_for_thread, clear_user_for_thread
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
        timeout=30,
        api_key=openai_api_key,
        base_url=openai_base_url,
    )
else:
    logging.getLogger(__name__).warning("OPENAI_API_KEY not set. Using Ollama (llama3-groq-tool-use:latest).")
    model = ChatOllama(
        model="qwen3.5:latest",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.1,
        num_predict=2048,
    )

MAX_HISTORY_TOKENS = 100_000


class TrimHistoryMiddleware(AgentMiddleware):
    """Trim conversation history before each model call to stay within context limits. This issue was responsible for erroring out."""

    def wrap_model_call(self, request, handler):
        request.messages = trim_messages(
            request.messages,
            max_tokens=MAX_HISTORY_TOKENS,
            token_counter="approximate",
            strategy="last",
            include_system=True,
            allow_partial=False,
        )
        return handler(request)


_checkpointer=None

def _get_checkpointer():
    """Lazily initialize checkpointer"""
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    try:
        _checkpointer = MongoDBSaver(
            client=get_mongo_client(),
            db_name="UserData",
        )
    except Exception as e:
        _checkpointer = InMemorySaver()

    return _checkpointer

agent = create_agent(
    model,
    tools=tools(),
    system_prompt=SYSTEM_PROMPT,
    middleware=[TrimHistoryMiddleware()],
    checkpointer =_get_checkpointer(),
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
    return None


def _normalize_tool_args(raw) -> dict | None:
    if isinstance(raw, dict):
        return raw
    parsed = _parse_tool_content(raw)
    if isinstance(parsed, dict):
        return parsed
    if raw is None:
        return None
    return {"value": raw}


def _extract_reasoning_steps(messages: list) -> list[str]:
    steps: list[str] = []
    for msg in messages:
        if getattr(msg, "type", None) != "ai":
            continue
        text = _as_text(getattr(msg, "content", ""))
        if text:
            steps.append(text)
    return steps


def _extract_tool_calls(messages: list) -> list[ToolCall]:
    tool_requests_by_id: dict[str, dict] = {}
    ordered_requests: list[dict] = []
    for msg in messages:
        if getattr(msg, "type", None) != "ai":
            continue

        reasoning = _as_text(getattr(msg, "content", ""))
        for call in getattr(msg, "tool_calls", []) or []:
            if not isinstance(call, dict):
                continue

            call_id = str(call.get("id") or "")
            request = {
                "id": call_id or None,
                "name": str(call.get("name") or "unknown_tool"),
                "reasoning": reasoning or None,
                "input_parameters": _normalize_tool_args(call.get("args")),
            }
            ordered_requests.append(request)

            if call_id:
                tool_requests_by_id[call_id] = request

    tool_outputs_by_id: dict[str, object] = {}
    unmatched_tool_outputs_by_name: dict[str, list[object]] = {}
    orphan_outputs: list[tuple[str, object]] = []
    for msg in messages:
        if getattr(msg, "type", None) != "tool":
            continue

        tool_call_id = str(getattr(msg, "tool_call_id", "") or "")
        request = tool_requests_by_id.get(tool_call_id, {})
        tool_name = str(getattr(msg, "name", "") or request.get("name") or "unknown_tool")

        parsed_output = _parse_tool_content(getattr(msg, "content", None))
        output = parsed_output if parsed_output is not None else _as_text(getattr(msg, "content", ""))

        if tool_call_id:
            tool_outputs_by_id[tool_call_id] = output
            continue

        if tool_name and tool_name != "unknown_tool":
            unmatched_tool_outputs_by_name.setdefault(tool_name, []).append(output)
            continue

        orphan_outputs.append((tool_name, output))

    tool_calls: list[ToolCall] = []
    for request in ordered_requests:
        output = None
        req_id = request.get("id")
        req_name = request.get("name")

        if req_id and req_id in tool_outputs_by_id:
            output = tool_outputs_by_id.pop(req_id)
        elif req_name in unmatched_tool_outputs_by_name and unmatched_tool_outputs_by_name[req_name]:
            output = unmatched_tool_outputs_by_name[req_name].pop(0)

        tool_calls.append(
            ToolCall(
                name=str(req_name or "unknown_tool"),
                reasoning=request.get("reasoning"),
                input_parameters=request.get("input_parameters"),
                output=output,
            )
        )

    # Preserve tool outputs that had no matching request metadata.
    for tool_name, output in orphan_outputs:
        tool_calls.append(ToolCall(name=tool_name or "unknown_tool", output=output))

    for tool_name, outputs in unmatched_tool_outputs_by_name.items():
        for output in outputs:
            tool_calls.append(ToolCall(name=tool_name or "unknown_tool", output=output))

    for tool_call_id, output in tool_outputs_by_id.items():
        tool_calls.append(
            ToolCall(
                name="unknown_tool",
                input_parameters={"tool_call_id": tool_call_id},
                output=output,
            )
        )

    return tool_calls


def _serialize_doc(doc: dict) -> dict:
    """Make a MongoDB document JSON-serializable (ObjectId, datetime)."""
    for k, v in doc.items():
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _serialize_doc(item)
    return doc


def _extract_listings(messages: list) -> list:
    """Extract listing data from ToolMessage objects after the last user message.

    Tool responses are intentionally slim (no photos/binary data) to avoid
    blowing the LLM context window. This function re-enriches listings from
    MongoDB so the frontend gets the full data including photos.
    """
    # Only look at messages from the current turn (after the last human/user message)
    last_human_idx = -1
    for i, m in enumerate(messages):
        if m.type in ("human",):
            last_human_idx = i
    recent = messages[last_human_idx + 1:] if last_human_idx >= 0 else messages

    slim_listings = []
    for m in recent:
        if m.type != "tool":
            continue
        content = _parse_tool_content(m.content)
        if isinstance(content, dict) and content.get("success") and "listings" in content:
            slim_listings.extend(content["listings"])

    if not slim_listings:
        return []

    # Re-fetch full listings (with photos) from MongoDB
    from app.database import get_listings_collection, get_units_collection
    listing_ids = [l["listing_id"] for l in slim_listings if "listing_id" in l]
    score_map = {l["listing_id"]: l.get("match_score", 0) for l in slim_listings}

    try:
        listings_col = get_listings_collection()
        full_docs = {
            doc["listing_id"]: doc
            for doc in listings_col.find({"listing_id": {"$in": listing_ids}})
        }
        units_col = get_units_collection()
        units_by_listing: dict[str, list] = {}
        for u in units_col.find({"listing_id": {"$in": listing_ids}}):
            u["_id"] = str(u["_id"])
            units_by_listing.setdefault(u["listing_id"], []).append(u)

        listings = []
        for lid in listing_ids:
            doc = full_docs.get(lid)
            if not doc:
                continue
            doc["_id"] = str(doc["_id"])
            doc["units"] = units_by_listing.get(lid, [])
            doc["match_score"] = score_map.get(lid, 0)
            listings.append(_serialize_doc(doc))
        return listings
    except Exception:
        # Fallback to slim listings if MongoDB is unavailable
        return slim_listings


@observe(type="llm", name="agent_reasoning")
def _invoke_agent_with_trace(user_query: str, config: dict) -> tuple[list, str, list[str], list[ToolCall]]:
    response = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config=config
    )
    msgs = response.get("messages", [])
    final_response = _as_text(msgs[-1].content) if msgs else ""
    reasoning_steps = _extract_reasoning_steps(msgs)
    tool_calls = _extract_tool_calls(msgs)

    update_current_span(
        input=user_query,
        output=final_response,
        context=reasoning_steps,
        tools_called=tool_calls,
    )
    return msgs, final_response, reasoning_steps, tool_calls


MAX_HISTORY_MESSAGES = 200


# Return thread history (capped to prevent unbounded fetch)
def get_history(thread_id: str, limit: int = MAX_HISTORY_MESSAGES) -> list:
    config = {"configurable": {"thread_id": thread_id}}
    state  = agent.get_state(config)
    if not state or not state.values.get("messages"):
        return []
    role_map = {
        "human":  "user",
        "ai": "assistant",
        "system": "system",
    }

    # Cap the raw messages to the most recent `limit` entries
    all_messages = state.values["messages"]
    if limit > 0 and len(all_messages) > limit:
        all_messages = all_messages[-limit:]

    # First pass: collect all listing_ids from tool messages
    all_listing_ids: list[str] = []
    for m in all_messages:
        if m.type != "tool":
            continue
        parsed = _parse_tool_content(m.content)
        if isinstance(parsed, dict) and parsed.get("success") and "listings" in parsed:
            for l in parsed["listings"]:
                if "listing_id" in l:
                    all_listing_ids.append(l["listing_id"])

    # Batch-fetch full listings with photos from MongoDB
    full_listing_map: dict[str, dict] = {}
    if all_listing_ids:
        try:
            from app.database import get_listings_collection, get_units_collection
            listings_col = get_listings_collection()
            for doc in listings_col.find({"listing_id": {"$in": all_listing_ids}}):
                doc["_id"] = str(doc["_id"])
                full_listing_map[doc["listing_id"]] = _serialize_doc(doc)
            units_col = get_units_collection()
            for u in units_col.find({"listing_id": {"$in": all_listing_ids}}):
                u["_id"] = str(u["_id"])
                _serialize_doc(u)
                lid = u["listing_id"]
                if lid in full_listing_map:
                    full_listing_map[lid].setdefault("units", []).append(u)
        except Exception:
            pass

    # Second pass: build history with enriched listings
    history = []
    pending_listings: list = []
    for m in all_messages:
        if m.type == "tool":
            parsed = _parse_tool_content(m.content)
            if isinstance(parsed, dict) and parsed.get("success") and "listings" in parsed:
                for l in parsed["listings"]:
                    lid = l.get("listing_id", "")
                    enriched = full_listing_map.get(lid, l)
                    enriched["match_score"] = l.get("match_score", 0)
                    pending_listings.append(enriched)
            continue
        content = m.content
        if not content:
            continue
        entry: dict = {
            "role":    role_map.get(m.type, m.type),
            "content": content,
        }
        if pending_listings:
            entry["listings"] = pending_listings
            pending_listings = []
        history.append(entry)
    return history


# Simple invocation of the agent
@observe(type="agent", name="run_agent")
def run_agent(user_query: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    user_id = get_user_id_for_thread(thread_id)
    if user_id:
        set_user_for_thread(thread_id, user_id)
    msgs: list = []
    final_response = ""
    reasoning_steps: list[str] = []
    tool_calls: list[ToolCall] = []
    try:
        msgs, final_response, reasoning_steps, tool_calls = _invoke_agent_with_trace(user_query, config)
    except Exception as e:
        update_current_trace(
            input=user_query,
            output="",
            context=reasoning_steps,
            tools_called=tool_calls,
        )
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
            "error" : "Something went wrong. Please try again.",
            "error_type" : "internal",
            "thread_id" : thread_id,
        }
    finally:
        clear_user_for_thread(thread_id)

    if not msgs:
        update_current_trace(
            input=user_query,
            output="",
            context=reasoning_steps,
            tools_called=tool_calls,
        )
        return {
            "success" : False,
            "response" : "",
            "listings" : [],
            "error" : "No messages received",
            "error_type" : "Empty payload",
            "thread_id" : thread_id,
        }

    update_current_trace(
        input=user_query,
        output=final_response,
        context=reasoning_steps,
        tools_called=tool_calls,
    )
    return {
        "success" : True,
        "response" : final_response,
        "listings" : _extract_listings(msgs),
        "error" : None,
        "error_type" : None,
        "thread_id" : thread_id,
    }


# Stream the agent responses as structured event dicts
def run_agent_stream(user_query: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    user_id = get_user_id_for_thread(thread_id)
    if user_id:
        set_user_for_thread(thread_id, user_id)
    try:
        for chunk, metadata in agent.stream(
            {"messages": [HumanMessage(content=user_query)]},
            config=config,
            stream_mode="messages"
        ):
            if chunk.type == "AIMessageChunk" and chunk.content:
                yield {"type": "token", "content": _as_text(chunk.content)}
    except Exception as e:
        if _is_timeout_error(e):
            yield {"type": "error", "error": "Request timed out", "error_type": "timeout"}
            return
        logging.getLogger(__name__).error("Stream error for thread %s: %s", thread_id, e, exc_info=True)
        yield {"type": "error", "error": "Something went wrong. Please try again.", "error_type": "internal"}
        return
    finally:
        clear_user_for_thread(thread_id)

    # Extract listings from the final agent state
    state = agent.get_state(config)
    if state and state.values.get("messages"):
        listings = _extract_listings(state.values["messages"])
        if listings:
            yield {"type": "listings", "listings": listings}


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
        for event in run_agent_stream(query, thread_id=thread_id):
            if event["type"] == "token":
                print(event["content"], end="", flush=True)
            elif event["type"] == "listings":
                print(f"\n[{len(event['listings'])} listings found]", flush=True)
            elif event["type"] == "error":
                print(f"\n[Error: {event['error']}]", flush=True)
        print("\n")
