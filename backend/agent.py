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

# Gemini Wrapper

class CustomGeminiWrapper:
    def __init__(self, model_name: str, api_key: str):
        self.api_key = api_key
        self.model_name = model_name
        self.model = None

    def _get_model(self):
        if self.model:
            return self.model
            
        if self.api_key == "dummy":
            return None
            
        try:
            # Configure only when needed
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            return self.model
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    
    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        model = self._get_model()
        if model is None:
            return AIMessage(content="AI Unavailable.")
            
        full_prompt = ""
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "System" if isinstance(msg, SystemMessage) else "AI"
            full_prompt += f"{role}: {msg.content}\n\n"
            
        try:
            response = model.generate_content(full_prompt)
            return AIMessage(content=response.text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Quota exceeded" in err_str:
                return AIMessage(content="⚠️ **Daily Quota Exceeded.**\nYou are using the Free Tier of Google Gemini. Please wait a minute or ensure you are using a 'Flash' model.\n(The system has been updated to auto-select Flash for you now).")
            return AIMessage(content=f"Error: {str(e)}")

# --- Dynamic Model Selection ---
def get_best_available_model(api_key: str):
    """
    Dynamically checks available models.
    STRICTLY prefers Flash models for Free Tier reliability.
    """
    if api_key == "dummy": return "dummy-model"
    
    try:
        genai.configure(api_key=api_key)
        all_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                all_models.append(m.name)
        
        logger.info(f"Available Gemini Models: {all_models}")
        
        # 1. Look for explicit Flash models (Reliable Free Tier)
        flash_models = [m for m in all_models if "flash" in m.lower()]
        for m in flash_models:
            # Prefer 1.5 flash
            if "1.5" in m:
                logger.info(f"Selected Flash Model: {m}")
                return m
        
        # If any flash found (e.g. 1.0 or 2.0)
        if flash_models:
            logger.info(f"Selected Fallback Flash Model: {flash_models[0]}")
            return flash_models[0]

        # 2. Only if NO Flash exists, try Pro
        pro_models = [m for m in all_models if "pro" in m.lower()]
        if pro_models:
             return pro_models[0]
             
        # 3. Fallback to anything
        if all_models:
            return all_models[0]
            
    except Exception as e:
        logger.error(f"Model discovery failed: {e}")
        
    return "models/gemini-1.5-flash" # Safe default

# Global instance with dynamic selection
selected_model = get_best_available_model(GOOGLE_API_KEY)
llm = CustomGeminiWrapper(selected_model, GOOGLE_API_KEY)

# --- 2. State Definition ---
class AgentState(TypedDict, total=False):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: int
    user_profile: str          # Short bio from DB (age, gender)
    psych_profile: str         # Long term memory from DB
    available_reports: str     # Medical history context
    rag_memories: str          # Semantic memory from vector store (RAG)
    conversation_count: int    # Number of messages for engagement style
    
    # Internal Scratchpad
    tavily_results: str
    analysis_results: str
    next_step: str             # 'research', 'analyze', 'respond', 'off_topic'

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
    Decides if we need Web Search, Data Analysis, or just a Response.
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
    """Executes general web search."""
    query = state['messages'][-1].content
    logger.info(f"🔎 Researching: {query}")
    results = tavily_search(query)
    return {"tavily_results": results}

def analyst_node(state: AgentState):
    """Verifies access to ML tools."""
    # In a full super-agent, this would parse arguments and call ml_service.
    # For now, we simulate the 'Board' recognizing the need for tools.
    return {"analysis_results": "ML Models (Heart, Diabetes, Liver) are available for invocation."}

def profiler_node(state: AgentState):
    """
    Updates the 'psych_profile' in the DB based on the interaction.
    (In a real app, this runs async after response, here we mock it or update state).
    """
    # We don't actually write to DB in this turn to avoid latency, 
    # but we acknowledge the memory update potential.
    return {} 

def generation_node(state: AgentState):
    """
    Generates highly personalized responses using all available context.
    Features: Memory recall, proactive suggestions, empathy, follow-ups.
    """
    messages = state['messages']
    profile = state.get("user_profile", "Unknown")
    medical_history = state.get("available_reports", "")
    rag_context = state.get("rag_memories", "")
    web_data = state.get("tavily_results", "")
    conv_count = state.get("conversation_count", 1)
    
    # Determine conversation phase for engagement style
    if conv_count <= 2:
        engagement_style = "WELCOMING: This is a new or early conversation. Be warm and build rapport."
    elif conv_count <= 5:
        engagement_style = "ENGAGED: User is actively chatting. Reference their previous messages in this session."
    else:
        engagement_style = "DEEP SESSION: Long conversation. Summarize key points discussed and offer next steps."
    
    system_prompt = f"""Act as a helpful medical assistant.
    
    User Profile:
    {profile}

    Medical History:
    {medical_history}

    Past Interactions:
    {rag_context}

    Web Context:
    {web_data if web_data else "N/A"}

    Instructions:
    - Personalize responses using the user's name and history.
    - Be supportive and pragmatic.
    - Suggest relevant health tips or follow-up topics.
    - Safety: If symptoms are severe (chest pain, stroke signs), advise calling emergency services immediately.
    - Disclaimer: Always clarify you are an assistant, not a doctor.
    - Keep responses concise and readable.
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
    return state.get('next_step', 'respond')

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    route_step,
    {
        "research": "researcher",
        "analyze": "analyst",
        "respond": "generate",
        "off_topic": "guardrail"
    }
)

workflow.add_edge("researcher", "generate")
workflow.add_edge("analyst", "generate")
workflow.add_edge("guardrail", END)
workflow.add_edge("generate", END)

medical_agent = workflow.compile()
