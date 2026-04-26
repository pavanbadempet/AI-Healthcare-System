"""
Extended tests for backend/agent.py to increase coverage.
Tests CoreAIWrapper, tavily_search, supervisor routing, and guardrail node.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.agent import (
    CoreAIWrapper, 
    tavily_search, 
    supervisor_node, 
    guardrail_node,
    analyst_node,
    profiler_node
)


class TestCoreAIWrapper:
    """Tests for the CoreAIWrapper class (replaced CustomGeminiWrapper)."""
    
    def test_invoke_success(self):
        """Test successful invocation via core_ai."""
        wrapper = CoreAIWrapper()
        
        with patch("backend.agent.core_ai") as mock_core:
            # Make generate return a coroutine
            import asyncio
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
            import asyncio
            async def fake_generate(prompt):
                return ""
            mock_core.generate = fake_generate
            
            result = wrapper.invoke([HumanMessage(content="Hello")])
            
            assert isinstance(result, AIMessage)
            assert "unavailable" in result.content.lower()
    
    def test_invoke_exception(self):
        """Test error handling during invocation."""
        wrapper = CoreAIWrapper()
        
        with patch("backend.agent.core_ai") as mock_core:
            import asyncio
            async def fake_generate(prompt):
                raise Exception("API timeout")
            mock_core.generate = fake_generate
            
            result = wrapper.invoke([HumanMessage(content="Test")])
            
            assert isinstance(result, AIMessage)
            assert "Error" in result.content or "error" in result.content.lower()
    
    def test_invoke_quota_exceeded(self):
        """Test quota exceeded error handling."""
        wrapper = CoreAIWrapper()
        
        with patch("backend.agent.core_ai") as mock_core:
            import asyncio
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
            assert "http://example.com" in result
    
    def test_tavily_api_error(self):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch("backend.agent.TAVILY_API_KEY", "test-key"), \
             patch("backend.agent.requests.post", return_value=mock_response):
            
            result = tavily_search("query")
            
            assert "Search Error" in result
    
    def test_tavily_exception(self):
        """Test handling of request exceptions."""
        with patch("backend.agent.TAVILY_API_KEY", "test-key"), \
             patch("backend.agent.requests.post", side_effect=Exception("Network error")):
            
            result = tavily_search("query")
            
            assert "Exception" in result


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
    
    def test_guardrail_node(self):
        """Test guardrail node returns appropriate message."""
        state = {"messages": [HumanMessage(content="politics")]}
        result = guardrail_node(state)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "Healthcare" in result["messages"][0].content
    
    def test_analyst_node(self):
        """Test analyst node returns ML tool availability."""
        state = {"messages": [HumanMessage(content="analyze")]}
        result = analyst_node(state)
        
        assert "analysis_results" in result
        assert "ML Models" in result["analysis_results"]
    
    def test_profiler_node(self):
        """Test profiler node returns empty dict."""
        state = {"messages": [HumanMessage(content="hello")]}
        result = profiler_node(state)
        
        assert result == {}
