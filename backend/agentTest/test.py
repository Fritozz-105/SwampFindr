import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import logging
from app.agents.user_context import set_user_for_thread, clear_user_for_thread
from app.services.conversation_service import get_user_id_for_thread
from deepeval.metrics import ToolCorrectnessMetric, ArgumentCorrectnessMetric
from deepeval.tracing import observe
from langchain_core.messages import HumanMessage
from app.agents.agent import agent
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, ToolCall
from app.services.conversation_service import create_thread_for_user,touch_thread
tool_correctness = ToolCorrectnessMetric()
argument_correctness = ArgumentCorrectnessMetric()
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
def run_agent(user_query: str, thread_id: str):
    """Run the agent and return the final response (no streaming).

    Returns either the agent response object or a dict with an error.
    """
    configdict = {"configurable": {"thread_id": thread_id}}
    user_id = get_user_id_for_thread(thread_id)
    if user_id:
        set_user_for_thread(thread_id, user_id)

    try:
        response = agent.invoke({"messages": [HumanMessage(content=user_query)]}, config=configdict)
    except Exception as e:
        logging.error(f"Error running agent: {e}")
        response = {"type": "error", "message": str(e)}
    finally:
        clear_user_for_thread(thread_id)

    return response
def extract_tools_and_last_ai(data):
    msgs = data.get("messages", [])
    tools = []
    for m in msgs:
        tc = m.get("tool_calls") if isinstance(m, dict) else getattr(m, "tool_calls", None)
        if tc:
            tools.extend(tc if isinstance(tc, list) else [tc])

    last_ai = None
    for m in reversed(msgs):
        if isinstance(m, dict):
            if "usage_metadata" in m or "response_metadata" in m or m.get("type") == "AIMessage" or m.get("role") == "assistant":
                last_ai = m.get("content")
                break
        else:
            if getattr(m, "usage_metadata", None) is not None or type(m).__name__ == "AIMessage" or getattr(m, "response_metadata", None) is not None:
                last_ai = getattr(m, "content", None)
                break

    # normalize tool names
    tool_names = []
    for t in tools:
        if isinstance(t, dict):
            tool_names.append(t.get("name"))
        else:
            tool_names.append(getattr(t, "name", None))
    return tool_names, last_ai



#input and test class
inputs = [
    ("What apartments are best for me based on my profile?",1),
    ("What apartments are best for me that is near marston library by 10 minute bus ride?",0),
    ("What apartments are best for me that is near Walmart by 10 minute car ride?",0),
    ("What are the bus routes for the apartments you suggested based on my preferences?",1), 
    ("Can you fetch the 4 best apartments for me and return their contact information?",2)
]
test_cases = []
user_id = os.getenv("USER_ID", "test-user-id")
for input,tClass in inputs:
    thread = create_thread_for_user(user_id)
    response = run_agent(input, thread)
    print(response)
    touch_thread(user_id, thread)
    tools_used, actual_response = extract_tools_and_last_ai(response)
    if tClass == 0:
        test_cases.append(LLMTestCase(
            input=input,
            expected_tools=[ToolCall(name="suggest_listing"),ToolCall(name="resolve_destination")],
            tools_called=tools_used,
            actual_output=actual_response,
        ))
    elif tClass == 1:
        test_cases.append(LLMTestCase(
            input=input,
            expected_tools=[ToolCall(name="suggest_listing")],
            tools_called=tools_used,
            actual_output=actual_response,
        ))
    elif tClass == 2:
        test_cases.append(LLMTestCase(
            input=input,
            expected_tools=[ToolCall(name="suggest_listing"),ToolCall(name="get_contact_info")],
            tools_called=tools_used,
            actual_output=actual_response,
        ))

print(evaluate(test_cases=test_cases,metrics=[tool_correctness, argument_correctness]))
