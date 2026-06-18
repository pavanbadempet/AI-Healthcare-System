"""
Tests for agent.py — medical agent routing, node logic, and CoreAIWrapper.

Covers: supervisor routing, off-topic guardrail, research routing,
analyst node, build_clinical_analysis_context, build_external_research_query,
generation_node prompt assembly, guardrail_node, CoreAIWrapper invoke paths.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.agent import (
    AgentState,
    CoreAIWrapper,
    _coerce_context,
    _compact_context,
    analyst_node,
    build_clinical_analysis_context,
    build_external_research_query,
    generation_node,
    guardrail_node,
    research_node,
    supervisor_node,
    tavily_search,
)

# ── _coerce_context / _compact_context ───────────────────────────────────────

def test_coerce_context_none_returns_empty():
    assert _coerce_context(None) == ""


def test_coerce_context_string_strips():
    assert _coerce_context("  hello  ") == "hello"


def test_coerce_context_non_string_converts():
    assert _coerce_context(42) == "42"


def test_compact_context_short_text_unchanged():
    text = "short text"
    assert _compact_context(text, limit=100) == text


def test_compact_context_long_text_truncated():
    text = "word " * 300  # 1500 chars
    result = _compact_context(text, limit=100)
    assert len(result) <= 100
    assert result.endswith("...")


def test_compact_context_none_returns_empty():
    assert _compact_context(None) == ""


# ── build_external_research_query ────────────────────────────────────────────

def test_build_external_research_query_includes_clinical_research():
    q = build_external_research_query("What is the latest diabetes treatment?")
    assert "clinical research" in q


def test_build_external_research_query_adds_diabetes_keyword():
    q = build_external_research_query("My diabetes glucose is high")
    assert "diabetes" in q


def test_build_external_research_query_adds_heart_keyword():
    q = build_external_research_query("heart disease symptoms")
    assert "heart" in q


def test_build_external_research_query_adds_latest_for_news_query():
    q = build_external_research_query("latest news on kidney research 2025")
    assert "latest" in q


def test_build_external_research_query_adds_treatment_guidelines():
    q = build_external_research_query("lung cancer treatment options")
    assert "treatment guidelines" in q


def test_build_external_research_query_defaults_to_healthcare():
    q = build_external_research_query("general health information")
    assert "healthcare" in q


def test_build_external_research_query_no_user_pii():
    """Query must not leak user messages verbatim."""
    user_msg = "My patient ID is 12345 and I have diabetes"
    q = build_external_research_query(user_msg)
    assert "12345" not in q
    assert "patient ID" not in q


# ── supervisor_node routing ───────────────────────────────────────────────────

def _state_with_message(content: str) -> AgentState:
    return {"messages": [HumanMessage(content=content)]}


def test_supervisor_routes_research_for_latest():
    state = _state_with_message("What are the latest diabetes treatments?")
    result = supervisor_node(state)
    assert result["next_step"] == "research"


def test_supervisor_routes_research_for_study():
    state = _state_with_message("Is there a study on kidney disease?")
    result = supervisor_node(state)
    assert result["next_step"] == "research"


def test_supervisor_routes_analyze_for_predict():
    state = _state_with_message("What is my risk of heart disease? predict")
    result = supervisor_node(state)
    assert result["next_step"] == "analyze"


def test_supervisor_routes_analyze_for_probability():
    state = _state_with_message("What is the probability of diabetes?")
    result = supervisor_node(state)
    assert result["next_step"] == "analyze"


def test_supervisor_routes_respond_for_general_health():
    state = _state_with_message("How can I improve my health?")
    result = supervisor_node(state)
    assert result["next_step"] == "respond"


def test_supervisor_routes_off_topic_for_politics():
    state = _state_with_message("Who is the president of the country?")
    result = supervisor_node(state)
    assert result["next_step"] == "off_topic"


def test_supervisor_routes_off_topic_for_movie():
    state = _state_with_message("What is the best movie this year?")
    result = supervisor_node(state)
    assert result["next_step"] == "off_topic"


def test_supervisor_routes_off_topic_for_code():
    state = _state_with_message("Write me a python script")
    result = supervisor_node(state)
    assert result["next_step"] == "off_topic"


def test_supervisor_routes_off_topic_for_joke():
    state = _state_with_message("Tell me a joke")
    result = supervisor_node(state)
    assert result["next_step"] == "off_topic"


# ── guardrail_node ────────────────────────────────────────────────────────────

def test_guardrail_node_returns_off_topic_message():
    state = _state_with_message("irrelevant")
    result = guardrail_node(state)
    assert len(result["messages"]) == 1
    assert "Healthcare" in result["messages"][0].content
    assert isinstance(result["messages"][0], AIMessage)


# ── analyst_node / build_clinical_analysis_context ───────────────────────────

def test_analyst_node_returns_analysis_results():
    state: AgentState = {
        "messages": [HumanMessage(content="My heart result shows high risk")],
        "available_reports": "Heart: High Risk",
        "rag_memories": "",
    }
    result = analyst_node(state)
    assert "analysis_results" in result
    assert isinstance(result["analysis_results"], str)


def test_build_clinical_analysis_context_includes_heart_area():
    state: AgentState = {
        "messages": [HumanMessage(content="My cardiac test shows issues")],
        "available_reports": "Heart: Detected",
        "rag_memories": "",
    }
    ctx = build_clinical_analysis_context(state)
    assert "heart" in ctx.lower() or "Heart disease" in ctx


def test_build_clinical_analysis_context_includes_diabetes_area():
    state: AgentState = {
        "messages": [HumanMessage(content="My glucose is high")],
        "available_reports": "",
        "rag_memories": "glucose 180",
    }
    ctx = build_clinical_analysis_context(state)
    assert "diabetes" in ctx.lower()


def test_build_clinical_analysis_context_no_match_says_not_identified():
    state: AgentState = {
        "messages": [HumanMessage(content="How are you?")],
        "available_reports": "",
        "rag_memories": "",
    }
    ctx = build_clinical_analysis_context(state)
    assert "No supported prediction area" in ctx


def test_build_clinical_analysis_context_no_records_says_so():
    state: AgentState = {
        "messages": [HumanMessage(content="diabetes check")],
        "available_reports": "",
        "rag_memories": "",
    }
    ctx = build_clinical_analysis_context(state)
    assert "No prior scoped health records" in ctx


def test_build_clinical_analysis_context_includes_clinician_recommendation():
    state: AgentState = {
        "messages": [HumanMessage(content="what is my risk")],
        "available_reports": "Heart: Low Risk",
        "rag_memories": "",
    }
    ctx = build_clinical_analysis_context(state)
    assert "clinician" in ctx.lower()


def test_build_clinical_analysis_context_deduplicates_areas():
    """heart + cardiac both map to 'heart' — should appear only once."""
    state: AgentState = {
        "messages": [HumanMessage(content="cardiac heart disease")],
        "available_reports": "cardiac issue",
        "rag_memories": "heart problem",
    }
    ctx = build_clinical_analysis_context(state)
    # Should mention "Heart disease structured prediction" only once
    assert ctx.count("Heart disease structured prediction") == 1


# ── research_node ─────────────────────────────────────────────────────────────

def test_research_node_returns_tavily_results():
    state = _state_with_message("latest diabetes research")
    with patch("backend.agent.tavily_search", return_value="Tavily: diabetes guidelines updated"):
        result = research_node(state)
    assert result["tavily_results"] == "Tavily: diabetes guidelines updated"


# ── tavily_search ─────────────────────────────────────────────────────────────

def test_tavily_search_returns_missing_key_message_when_no_api_key():
    with patch("backend.agent.TAVILY_API_KEY", None):
        result = tavily_search("diabetes")
    assert "Missing" in result or "missing" in result.lower()


def test_tavily_search_returns_failure_on_exception():
    with patch("backend.agent.TAVILY_API_KEY", "fake-key"), \
         patch("backend.agent.requests.post", side_effect=Exception("network error")):
        result = tavily_search("heart disease")
    assert result == "Search temporarily unavailable."


def test_tavily_search_returns_upstream_error_on_bad_status():
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch("backend.agent.TAVILY_API_KEY", "fake-key"), \
         patch("backend.agent.requests.post", return_value=mock_resp):
        result = tavily_search("kidney")
    assert result == "Search service returned an error."


def test_tavily_search_returns_answer_on_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "answer": "Diabetes can be managed with diet.",
        "results": [{"url": "https://health.gov/diabetes"}],
    }

    with patch("backend.agent.TAVILY_API_KEY", "fake-key"), \
         patch("backend.agent.requests.post", return_value=mock_resp):
        result = tavily_search("diabetes management")
    assert "Diabetes can be managed" in result


# ── CoreAIWrapper ─────────────────────────────────────────────────────────────

def test_core_ai_wrapper_returns_ai_message():
    wrapper = CoreAIWrapper()
    with patch("backend.agent.core_ai.generate", new=AsyncMock(return_value="Generated text")):
        result = wrapper.invoke([HumanMessage(content="Hello")])
    assert isinstance(result, AIMessage)
    assert result.content == "Generated text"


def test_core_ai_wrapper_returns_fallback_on_empty_response():
    wrapper = CoreAIWrapper()
    with patch("backend.agent.core_ai.generate", new=AsyncMock(return_value="")):
        result = wrapper.invoke([HumanMessage(content="test")])
    assert isinstance(result, AIMessage)
    assert "unavailable" in result.content.lower()


def test_core_ai_wrapper_returns_quota_message_on_429():
    wrapper = CoreAIWrapper()
    with patch("backend.agent.core_ai.generate", new=AsyncMock(side_effect=Exception("429 quota exceeded"))):
        result = wrapper.invoke([HumanMessage(content="test")])
    assert "Quota" in result.content or "quota" in result.content.lower()


def test_core_ai_wrapper_returns_failure_message_on_generic_exception():
    wrapper = CoreAIWrapper()
    with patch("backend.agent.core_ai.generate", new=AsyncMock(side_effect=Exception("some error"))):
        result = wrapper.invoke([HumanMessage(content="test")])
    assert result.content == "AI is temporarily unavailable. Please try again shortly."


# ── generation_node ───────────────────────────────────────────────────────────

def test_generation_node_uses_welcoming_style_for_new_conversation():
    state: AgentState = {
        "messages": [HumanMessage(content="Hi")],
        "user_profile": "Jane, 35, Female",
        "available_reports": "",
        "rag_memories": "",
        "conversation_count": 1,
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Welcome! How can I help you?")

    with patch("backend.agent.llm", mock_llm):
        result = generation_node(state)

    assert len(result["messages"]) == 1
    assert isinstance(result["messages"][0], AIMessage)
    # Verify the system message passed to llm contains welcoming style
    call_args = mock_llm.invoke.call_args[0][0]
    system_msg = next(m for m in call_args if isinstance(m, SystemMessage))
    assert "WELCOMING" in system_msg.content


def test_generation_node_uses_engaged_style_for_mid_conversation():
    state: AgentState = {
        "messages": [HumanMessage(content="And what about my liver?")],
        "user_profile": "Jane, 35, Female",
        "available_reports": "",
        "rag_memories": "",
        "conversation_count": 4,
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Your liver looks fine.")

    with patch("backend.agent.llm", mock_llm):
        generation_node(state)

    call_args = mock_llm.invoke.call_args[0][0]
    system_msg = next(m for m in call_args if isinstance(m, SystemMessage))
    assert "ENGAGED" in system_msg.content


def test_generation_node_uses_deep_session_style_for_long_conversation():
    state: AgentState = {
        "messages": [HumanMessage(content="Summarize everything")],
        "user_profile": "Jane, 35, Female",
        "available_reports": "",
        "rag_memories": "",
        "conversation_count": 10,
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Here is your summary.")

    with patch("backend.agent.llm", mock_llm):
        generation_node(state)

    call_args = mock_llm.invoke.call_args[0][0]
    system_msg = next(m for m in call_args if isinstance(m, SystemMessage))
    assert "DEEP SESSION" in system_msg.content
