import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Import nodes from the actual agent file
from backend.agent import research_node, generation_node

@pytest.fixture
def mock_agent_env():
    # Patch the Global 'llm' OBJECT and 'tavily_search' function
    with patch("backend.agent.tavily_search") as mock_tavily, \
         patch("backend.agent.llm") as mock_llm_instance: 
        
        mock_llm_instance.invoke.return_value = AIMessage(content="Mocked AI Response")
        
        yield {
            "tavily": mock_tavily,
            "gemini": mock_llm_instance
        }

def test_research_node(mock_agent_env):
    state = {
        "messages": [HumanMessage(content="New treatment for diabetes")]
    }
    
    mock_agent_env["tavily"].return_value = "Answer: Metformin\nSources: ['url1']"
    
    result = research_node(state)
    
    assert mock_agent_env["tavily"].called
    assert "Metformin" in result["tavily_results"]

def test_generation_node(mock_agent_env):
    state = {
        "messages": [HumanMessage(content="Hello")],
        "user_id": 123,
        "user_profile": "Male, 30",
        "psych_profile": "Friendly",
        "tavily_results": "Some web info",
        "analysis_results": "None"
    }
    
    result = generation_node(state)
         
    mock_instance = mock_agent_env["gemini"]
    assert mock_instance.invoke.called
    assert isinstance(result["messages"][-1], AIMessage)
    assert result["messages"][-1].content == "Mocked AI Response"
