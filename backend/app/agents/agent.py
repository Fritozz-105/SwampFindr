from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import get_tools as tools
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()


model = ChatOpenAI(
    model = "gpt-4o-mini",
    temperature = 0.1,
    max_tokens = 256,
    timeout=30,
    api_key = os.getenv("OPENAI_API_KEY")
)


agent = create_agent(
    model,
    tools=tools(),
    system_prompt=SYSTEM_PROMPT,
    checkpointer = InMemorySaver(), # replace with prod db
)


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
def run_agent(user_query: str, thread_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            config=config
        )
    except TimeoutError:
        return {"error": "Request timed out, please try again"}
    except Exception as e:
        return {"error": f"Agent error: {e}"}

    return {"response": response["messages"][-1].content}


# Stream the agent responses
def run_agent_stream(user_query: str, thread_id: str = "default"):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        for chunk in agent.stream(
            {"messages": [HumanMessage(content=user_query)]},
            config=config,
            stream_mode="values"
        ):
            yield chunk["messages"][-1].content
    except TimeoutError:
        return {"error": "Request timed out, please try again"}
    except Exception as e:
        return {"error": f"Agent error: {e}"}


if __name__ == "__main__":
    thread_id = "test-1"
    print("Agent started... Type 'QUIT' to exit.\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        response = run_agent(query, thread_id=thread_id)
        print(f"Agent: {response.get('response') or response.get('error')}\n")
