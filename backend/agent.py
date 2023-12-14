from typing import TypedDict, Annotated, List, Union, Any, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
import google.generativeai as genai
import operator
import logging
import requests
import json
import os
from dotenv import load_dotenv

# Import our internals
from . import rag
from .ml_service import ml_service

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load keys
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found. AI features disabled.")
    GOOGLE_API_KEY = "dummy"

# --- 1. Custom Gemini Wrapper ---
class CustomGeminiWrapper:
    def __init__(self, model_name: str, api_key: str):
        self.api_key = api_key
        if api_key != "dummy":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        else:
            self.model = None
    
    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        if self.model is None:
            return AIMessage(content="AI Unavailable.")
            
        full_prompt = ""
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "System" if isinstance(msg, SystemMessage) else "AI"
            full_prompt += f"{role}: {msg.content}\n\n"
            
        try:
            response = self.model.generate_content(full_prompt)
            return AIMessage(content=response.text)
        except Exception as e:
            return AIMessage(content=f"Error: {str(e)}")

llm = CustomGeminiWrapper("gemini-2.0-flash", GOOGLE_API_KEY)

# --- 2. State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: int
    user_profile: str     # Short bio from DB (age, gender)
    psych_profile: str    # Long term memory from DB
    
    # Internal Scratchpad
    tavily_results: str
    analysis_results: str
    next_step: str        # 'research', 'analyze', 'respond', 'off_topic'

# --- 3. Tools ---

def tavily_search(query: str):
    """Real-time web search for medical breakthroughs."""
    if not TAVILY_API_KEY:
        return "Tavily Key Missing."
    
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",     # Deep search
            "topic": "general",
            "include_answer": True,
            "max_results": 3
        }
        headers = {'content-type': 'application/json'}
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return f"Answer: {data.get('answer', '')}\nSources: {[r['url'] for r in data.get('results', [])]}"
        else:
            return f"Search Error: {resp.text}"
    except Exception as e:
        return f"Search Exception: {str(e)}"

# --- 4. Nodes ---

def supervisor_node(state: AgentState):
    """
    The Brain. Decides if we need Web Search, Data Analysis, or just a Response.
    Also handles OFF-TOPIC Guardrail.
    """
    messages = state['messages']
    last_msg = messages[-1].content.lower()

    # GUARDRAIL: Domain Check
    forbidden = ["president", "politics", "movie", "song", "joke", "code", "python", "finance"]
    if any(x in last_msg for x in forbidden):
        return {"next_step": "off_topic"}

    # ROUTING LOGIC
    # Heuristics for speed (saving LLM calls for routing)
    if any(w in last_msg for w in ["latest", "news", "treatment", "research", "study", "2024", "2025"]):
        return {"next_step": "research"}
    
    if any(w in last_msg for w in ["predict", "risk", "chance", "probability", "analyze"]):
        return {"next_step": "analyze"}

    return {"next_step": "respond"}

def research_node(state: AgentState):
    """The Researcher Agent."""
    query = state['messages'][-1].content
    logger.info(f"🔎 Researching: {query}")
    results = tavily_search(query)
    return {"tavily_results": results}

def analyst_node(state: AgentState):
    """The Analyst Agent (Access to ML)."""
    # In a full super-agent, this would parse arguments and call ml_service.
    # For now, we simulate the 'Board' recognizing the need for tools.
    return {"analysis_results": "ML Models (Heart, Diabetes, Liver) are available for invocation."}

def profiler_node(state: AgentState):
    """
    The Memory System. 
    Updates the 'psych_profile' in the DB based on the interaction.
    (In a real app, this runs async after response, here we mock it or update state).
    """
    # We don't actually write to DB in this turn to avoid latency, 
    # but we acknowledge the memory update potential.
    return {} 

def generation_node(state: AgentState):
    """The Dr. AI Persona."""
    messages = state['messages']
    profile = state.get("user_profile", "Unknown")
    psych = state.get("psych_profile", "No long-term memory yet.")
    web_data = state.get("tavily_results", "")
    
    system_prompt = f"""You are 'Dr. AI', the world's most advanced Personal Healthcare Agent.
    
    USER DATA:
    - Profile: {profile}
    - Long-Term Memory: {psych}
    
    REAL-TIME KNOWLEDGE (Tavily):
    {web_data}
    
    INSTRUCTIONS:
    1. **Personalize**: Use the memory (psych_profile) to tailor your tone.
    2. **Evidence**: If you have Web Data, cite it.
    3. **Guardrails**: If the user asked off-topic, refuse.
    4. **Safety**: 
       - "MEDICAL EMERGENCY" -> Tell them to call 112/108.
       - Disclaimer: You are an AI, not a doctor.
       
    Be concise, warm, and hyper-intelligent.
    """
    
    final_msgs = [SystemMessage(content=system_prompt)] + messages
    response = llm.invoke(final_msgs)
    return {"messages": [response]}

def guardrail_node(state: AgentState):
    return {"messages": [AIMessage(content="I apologize, but I am specialized strictly in Healthcare. I cannot assist with that topic.")]}

# --- 5. Graph ---
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", research_node)
workflow.add_node("analyst", analyst_node) # placeholder for tool calling
workflow.add_node("generate", generation_node)
workflow.add_node("guardrail", guardrail_node)

# Edges
def route_step(state):
    return state['next_step']

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    route_step,
    {
        "research": "researcher",
        "analyze": "generate", # For now, let Generate handle tool prompts or just chat
        "respond": "generate",
        "off_topic": "guardrail"
    }
)

workflow.add_edge("researcher", "generate")
workflow.add_edge("analyst", "generate")
workflow.add_edge("guardrail", END)
workflow.add_edge("generate", END)

medical_agent = workflow.compile()
