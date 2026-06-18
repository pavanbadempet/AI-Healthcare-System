"""
Extended tests for backend/agent.py to increase coverage.
Tests CoreAIWrapper, tavily_search, supervisor routing, and guardrail node.
"""
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.agent import (
    CoreAIWrapper,
    analyst_node,
    build_clinical_analysis_context,
    guardrail_node,
    profiler_node,
    research_node,
    supervisor_node,
    tavily_search,
)


class TestCoreAIWrapper:
    """Tests for the CoreAIWrapper class (replaced CustomGeminiWrapper)."""

    def test_invoke_success(self):
        """Test successful invocation via core_ai."""
        wrapper = CoreAIWrapper()

        with patch("backend.agent.core_ai") as mock_core:
            # Make generate return a coroutine
            async def fake_generate(prompt):
                return "Test response"
            mock_core.generate = fake_generate

            result = wrapper.invoke([
                SystemMessage(content="System prompt"),
                HumanMessage(content="User message"),
                AIMessage(content="Previous AI message")
            ])

            assert isinstance(result, AIMessage)
            assert result.content == "Test response"

    def test_invoke_empty_response(self):
        """Test handling of empty AI response."""
        wrapper = CoreAIWrapper()

        with patch("backend.agent.core_ai") as mock_core:
            async def fake_generate(prompt):
                return ""
            mock_core.generate = fake_generate

            result = wrapper.invoke([HumanMessage(content="Hello")])

            assert isinstance(result, AIMessage)
            assert "unavailable" in result.content.lower()

    def test_invoke_exception(self, caplog):
        """Test error handling during invocation."""
        wrapper = CoreAIWrapper()
        sensitive_error = "API timeout patient_name=Sensitive User token=ai-secret"
        caplog.set_level("ERROR", logger="backend.agent")

        with patch("backend.agent.core_ai") as mock_core:
            async def fake_generate(prompt):
                raise Exception(sensitive_error)
            mock_core.generate = fake_generate

            result = wrapper.invoke([HumanMessage(content="Test")])

            assert isinstance(result, AIMessage)
            assert result.content == "AI is temporarily unavailable. Please try again shortly."
            assert sensitive_error not in result.content
            assert "Sensitive User" not in result.content
            assert "ai-secret" not in result.content
            assert sensitive_error not in caplog.text
            assert "Sensitive User" not in caplog.text
            assert "ai-secret" not in caplog.text

    def test_invoke_quota_exceeded(self):
        """Test quota exceeded error handling."""
        wrapper = CoreAIWrapper()

        with patch("backend.agent.core_ai") as mock_core:
            async def fake_generate(prompt):
                raise Exception("429 Quota exceeded")
            mock_core.generate = fake_generate

            result = wrapper.invoke([HumanMessage(content="Test")])

            assert isinstance(result, AIMessage)
            assert "Quota" in result.content


class TestTavilySearch:
    """Tests for the tavily_search function."""

    def test_tavily_no_api_key(self):
        """Test search returns error when API key missing."""
        with patch("backend.agent.TAVILY_API_KEY", None):
            result = tavily_search("test query")
            assert "Tavily Key Missing" in result

    def test_tavily_success(self):
        """Test successful search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "Test answer",
            "results": [{"url": "http://example.com"}]
        }

        with patch("backend.agent.TAVILY_API_KEY", "test-key"), \
             patch("backend.agent.requests.post", return_value=mock_response):

            result = tavily_search("diabetes treatment")

            assert "Test answer" in result
            parsed_urls = [
                urlparse(token.strip("()[]<>,\"'"))
                for token in result.split()
                if "http://" in token or "https://" in token
            ]
            assert any(
                p.scheme == "http" and p.hostname == "example.com" and (p.path in ("", "/"))
                for p in parsed_urls
            )

    def test_tavily_api_error(self):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error token=search-secret"

        with patch("backend.agent.TAVILY_API_KEY", "test-key"), \
             patch("backend.agent.requests.post", return_value=mock_response):

            result = tavily_search("query")

            assert result == "Search service returned an error."
            assert "search-secret" not in result

    def test_tavily_exception(self):
        """Test handling of request exceptions."""
        sensitive_error = "Network error token=search-secret patient_name=Sensitive User"
        with patch("backend.agent.TAVILY_API_KEY", "test-key"), \
             patch("backend.agent.requests.post", side_effect=Exception(sensitive_error)):

            result = tavily_search("query")

            assert result == "Search temporarily unavailable."
            assert sensitive_error not in result
            assert "search-secret" not in result
            assert "Sensitive User" not in result


class TestSupervisorNode:
    """Tests for the supervisor_node routing function."""

    def test_supervisor_research_route(self):
        """Test routing to research for research-related queries."""
        state = {"messages": [HumanMessage(content="latest treatment for diabetes")]}
        result = supervisor_node(state)
        assert result["next_step"] == "research"

    def test_supervisor_analyze_route(self):
        """Test routing to analyze for prediction queries."""
        state = {"messages": [HumanMessage(content="what is my risk for heart disease")]}
        result = supervisor_node(state)
        assert result["next_step"] == "analyze"

    def test_supervisor_respond_route(self):
        """Test default routing to respond."""
        state = {"messages": [HumanMessage(content="how are you doctor")]}
        result = supervisor_node(state)
        assert result["next_step"] == "respond"

    def test_supervisor_off_topic_route(self):
        """Test routing to guardrail for off-topic queries."""
        forbidden_queries = [
            "who is the president",
            "tell me about politics",
            "recommend a movie",
            "write python code",
            "what about finance"
        ]

        for query in forbidden_queries:
            state = {"messages": [HumanMessage(content=query)]}
            result = supervisor_node(state)
            assert result["next_step"] == "off_topic", f"Failed for query: {query}"


class TestOtherNodes:
    """Tests for other agent nodes."""

    def test_research_node_does_not_log_raw_patient_query(self, caplog):
        """Research routing should not write patient health text to logs."""
        sensitive_query = "latest treatment for diabetes patient_name=Sensitive User"
        caplog.set_level("INFO", logger="backend.agent")

        with patch("backend.agent.tavily_search", return_value="Answer: safe summary"):
            result = research_node({"messages": [HumanMessage(content=sensitive_query)]})

        assert result == {"tavily_results": "Answer: safe summary"}
        assert sensitive_query not in caplog.text
        assert "Sensitive User" not in caplog.text

    def test_research_node_sends_sanitized_query_to_external_search(self):
        """Research routing should not send identifiers to external search APIs."""
        sensitive_query = (
            "latest diabetes treatment patient_name=Sensitive User "
            "email=sensitive@example.com dob=1990-01-01 token=secret123"
        )

        with patch("backend.agent.tavily_search", return_value="Answer: safe summary") as search:
            result = research_node({"messages": [HumanMessage(content=sensitive_query)]})

        assert result == {"tavily_results": "Answer: safe summary"}
        sent_query = search.call_args.args[0]
        assert "diabetes" in sent_query
        assert "treatment" in sent_query
        assert "Sensitive" not in sent_query
        assert "sensitive@example.com" not in sent_query
        assert "1990-01-01" not in sent_query
        assert "secret123" not in sent_query

    def test_guardrail_node(self):
        """Test guardrail node returns appropriate message."""
        state = {"messages": [HumanMessage(content="politics")]}
        result = guardrail_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "Healthcare" in result["messages"][0].content

    def test_clinical_analysis_uses_scoped_records_and_supported_models(self):
        """Clinical analysis should summarize scoped context and applicable models."""
        state = {
            "messages": [HumanMessage(content="Analyze my heart and diabetes risk")],
            "available_reports": "History: heart:High risk, diabetes:Low risk",
            "rag_memories": "Previous diabetes checkup showed elevated glucose.",
        }

        result = build_clinical_analysis_context(state)

        assert "Relevant patient context" in result
        assert "heart" in result.lower()
        assert "diabetes" in result.lower()
        assert "validated structured prediction form" in result
        assert "ML Models (Heart, Diabetes, Liver)" not in result

    def test_clinical_analysis_handles_missing_records_conservatively(self):
        """Clinical analysis should be safe when no scoped records are available."""
        state = {"messages": [HumanMessage(content="What is my risk?")]}

        result = build_clinical_analysis_context(state)

        assert "No prior scoped health records were provided" in result
        assert "validated structured prediction form" in result

    def test_analyst_node_returns_record_aware_analysis(self):
        """Test analyst node returns scoped, record-aware analysis."""
        state = {
            "messages": [HumanMessage(content="analyze my liver risk")],
            "available_reports": "History: liver:Needs follow-up",
        }
        result = analyst_node(state)

        assert "analysis_results" in result
        assert "liver" in result["analysis_results"].lower()
        assert "ML Models (Heart, Diabetes, Liver)" not in result["analysis_results"]

    def test_profiler_node(self):
        """Test profiler node returns empty dict."""
        state = {"messages": [HumanMessage(content="hello")]}
        result = profiler_node(state)

        assert result == {}
