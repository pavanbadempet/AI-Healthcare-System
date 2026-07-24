from backend.agents.agent_interop_adapter import UniversalAgentInteropAdapter, run_agent_interop_pipeline


def test_universal_agent_interop_adapter():
    adapter = UniversalAgentInteropAdapter()
    msg = {"sender": "Supervisor", "recipient": "RAG", "content": {"query": "vitals"}}
    res = adapter.normalize_agent_message(msg, source_framework="CrewAI")
    assert res.framework_origin == "CrewAI"
    assert res.sender_agent == "Supervisor"
    assert res.mcp_tool_schema["jsonrpc"] == "2.0"


def test_run_agent_interop_pipeline_helper():
    info = run_agent_interop_pipeline()
    assert info["mcp_compliant"] is True
    assert info["framework"] == "LangGraph"
