import os
from types import SimpleNamespace

os.environ.setdefault("CONFIDENT_TRACE_VERBOSE", "0")
os.environ.setdefault("CONFIDENT_TRACE_FLUSH", "0")

from deepeval.test_case import ToolCall

from app.agents.agent import _extract_reasoning_steps, _extract_tool_calls
from app.agents import agent as agent_module


def test_extract_reasoning_steps_collects_ai_messages():
    messages = [
        SimpleNamespace(type="human", content="Find me a 2/2"),
        SimpleNamespace(type="ai", content="I'll look up matching listings."),
        SimpleNamespace(type="ai", content=[{"type": "text", "text": "Here are your best options."}]),
    ]

    assert _extract_reasoning_steps(messages) == [
        "I'll look up matching listings.",
        "Here are your best options.",
    ]


def test_extract_tool_calls_captures_name_args_reasoning_and_output():
    messages = [
        SimpleNamespace(
            type="ai",
            content="I should call semantic search first.",
            tool_calls=[
                {
                    "id": "call_1",
                    "name": "semantic_search",
                    "args": {"query": "pet friendly near campus"},
                }
            ],
        ),
        SimpleNamespace(
            type="tool",
            name="semantic_search",
            tool_call_id="call_1",
            content='{"success": true, "listings": []}',
        ),
    ]

    tool_calls = _extract_tool_calls(messages)

    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call.name == "semantic_search"
    assert tool_call.reasoning == "I should call semantic search first."
    assert tool_call.input_parameters == {"query": "pet friendly near campus"}
    assert tool_call.output == {"success": True, "listings": []}


def test_run_agent_updates_deepeval_trace(monkeypatch):
    fake_tool_calls = [ToolCall(name="semantic_search")]
    fake_messages = [SimpleNamespace(type="ai", content="Here is your answer.")]
    trace_updates: list[dict] = []

    monkeypatch.setattr(agent_module, "get_user_id_for_thread", lambda _: "user-1")
    monkeypatch.setattr(agent_module, "set_current_user_id", lambda _: "token")
    monkeypatch.setattr(agent_module, "reset_current_user_id", lambda _: None)
    monkeypatch.setattr(
        agent_module,
        "_invoke_agent_with_trace",
        lambda *_: (
            fake_messages,
            "Here is your answer.",
            ["Reasoned about the request."],
            fake_tool_calls,
        ),
    )
    monkeypatch.setattr(agent_module, "update_current_trace", lambda **kwargs: trace_updates.append(kwargs))

    result = agent_module.run_agent("Find me an apartment", "thread-1")

    assert result["success"] is True
    assert result["response"] == "Here is your answer."
    assert trace_updates
    assert trace_updates[-1]["tools_called"] == fake_tool_calls
