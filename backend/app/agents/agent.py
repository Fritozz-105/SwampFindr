from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.checkpoint.memory import InMemorySaver
import os
import httpx
from dotenv import load_dotenv

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import get_tools as tools
from app.agents.user_context import set_current_user_id, reset_current_user_id

import time


load_dotenv()

model = ChatOpenAI(
    model = "gpt-4o-mini",
    temperature = 0.1,
    max_tokens = 512,
    timeout=30,
    api_key = os.getenv("OPENAI_API_KEY")
)


agent = create_agent(
    model,
    tools=tools(),
    system_prompt=SYSTEM_PROMPT,
    checkpointer = InMemorySaver(), # replace with prod db
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
def run_agent(user_query: str, user_id: str | None = None, thread_id: str | None = None) -> dict:
    res_thread_id = thread_id or (f"user:{user_id}" if user_id else "default")
    config = {"configurable": {"thread_id": res_thread_id}}
    tkn = set_current_user_id(user_id)
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            config=config
        )
    except Exception as e:
        if _is_timeout_error(e):
            return {"error": "Request timed out, please try again"}
        return {"error": f"Agent error: {e}"}
    finally:
        reset_current_user_id(tkn)

    return {"response": response["messages"][-1].content}


# Stream the agent responses
def run_agent_stream(user_query: str, user_id: str | None = None, thread_id: str | None = None):
    res_thread_id = thread_id or (f"user:{user_id}" if user_id else "default")
    config = {"configurable": {"thread_id": res_thread_id}}
    tkn = set_current_user_id(user_id)
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
        for chunk in run_agent_stream(query, user_id="pytest-user-1", thread_id=thread_id):
            print(chunk, end="", flush=True)
            time.sleep(0.01)
        print("\n")
