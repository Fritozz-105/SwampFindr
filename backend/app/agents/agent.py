from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from backend.app.agents.prompts import SYSTEM_PROMPT
from backend.app.agents.tools import get_tools as tools
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


def run_agent(user_query: str, thread_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": thread_id}}

    response = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config=config
    )

    return {"response": response["messages"][-1].content}

