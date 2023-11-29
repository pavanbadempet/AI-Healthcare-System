import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def mock_agent_env():
    # Patch the Global 'llm' OBJECT directly, not the class
    with patch("backend.agent.rag") as mock_rag, \
         patch("backend.agent.llm") as mock_llm_instance: # This patches the already-instantiated object
        
        mock_llm_instance.invoke_with_tools.return_value = AIMessage(content="Mocked AI Response")
        
        yield {
            "rag": mock_rag,
            "gemini": mock_llm_instance
        }

def test_retrieve_node(mock_agent_env):
    from backend.agent import retrieve_node 
    # ... rest same ...
    state = {
        "messages": [HumanMessage(content="Check my history")],
        "user_id": "test_user",
        "user_profile": "Profile data",
        "retrieved_context": "",
        "available_reports": ""
    }
    mock_agent_env["rag"].search_similar_records.return_value = ["Rec1", "Rec2"]
    result = retrieve_node(state)
    assert mock_agent_env["rag"].search_similar_records.called
    assert "Rec1\n\nRec2" in result["retrieved_context"]

def test_generate_node(mock_agent_env):
    from backend.agent import generate_node as call_model
    
    state = {
        "messages": [HumanMessage(content="Hello")],
        "user_id": "test_user",
        "user_profile": "Profile",
        "retrieved_context": "Context",
        "available_reports": "Reports",
        "board_discussion": "None", 
        "past_conversation_memory": "None"
    }
    
    result = call_model(state)
         
    mock_instance = mock_agent_env["gemini"]
    assert mock_instance.invoke_with_tools.called
    assert isinstance(result["messages"][-1], AIMessage)
    assert result["messages"][-1].content == "Mocked AI Response"
