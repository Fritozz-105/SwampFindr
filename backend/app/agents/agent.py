from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import os
import httpx
import ast
import json
import logging
from dotenv import load_dotenv
from deepeval.tracing import observe, update_current_span, update_current_trace
from deepeval.test_case import ToolCall
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
    logging.getLogger(__name__).warning("OPENAI_API_KEY not set. Using Ollama (llama3-groq-tool-use:latest).")
    model = ChatOllama(
        model="llama3-groq-tool-use:latest",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.1,
        num_predict=2048,
    )

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
    for msg in messages:
        if getattr(msg, "type", None) != "ai":
            continue

        reasoning = _as_text(getattr(msg, "content", ""))
        for call in getattr(msg, "tool_calls", []) or []:
            if not isinstance(call, dict):
                continue

            call_id = str(call.get("id") or "")
            if not call_id:
                continue

            tool_requests_by_id[call_id] = {
                "name": str(call.get("name") or "unknown_tool"),
                "reasoning": reasoning or None,
                "input_parameters": _normalize_tool_args(call.get("args")),
            }

    tool_calls: list[ToolCall] = []
    for msg in messages:
        if getattr(msg, "type", None) != "tool":
            continue

        tool_call_id = str(getattr(msg, "tool_call_id", "") or "")
        request = tool_requests_by_id.get(tool_call_id, {})
        tool_name = str(getattr(msg, "name", "") or request.get("name") or "unknown_tool")

        parsed_output = _parse_tool_content(getattr(msg, "content", None))
        output = parsed_output if parsed_output is not None else _as_text(getattr(msg, "content", ""))

        tool_calls.append(
            ToolCall(
                name=tool_name,
                reasoning=request.get("reasoning"),
                input_parameters=request.get("input_parameters"),
                output=output,
            )
        )

    return tool_calls


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
    pending_listings: list = []
    for m in state.values["messages"]:
        if m.type == "tool":
            parsed = _parse_tool_content(m.content)
            if isinstance(parsed, dict) and parsed.get("success") and "listings" in parsed:
                pending_listings.extend(parsed["listings"])
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
    tkn = set_current_user_id(get_user_id_for_thread(thread_id))
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
        reset_current_user_id(tkn)

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
        import logging
        logging.getLogger(__name__).error("Stream error for thread %s: %s", thread_id, e, exc_info=True)
        yield "[error: something went wrong]"
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
        run_agent(user_query=query, thread_id=thread_id)
        print("\n")
