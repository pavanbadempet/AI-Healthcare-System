import asyncio
import logging
import operator
import os
from typing import Annotated, List, TypedDict

import requests
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

# All AI inference goes through core_ai — never call providers directly.
from . import core_ai
from .prompt_registry import get_prompt

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load keys
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AI_GENERATION_FAILURE_MESSAGE = "AI is temporarily unavailable. Please try again shortly."
SEARCH_FAILURE_MESSAGE = "Search temporarily unavailable."
SEARCH_UPSTREAM_ERROR_MESSAGE = "Search service returned an error."
SUPPORTED_ANALYSIS_AREAS = {
    "heart": ("heart", "Heart disease structured prediction"),
    "cardiac": ("heart", "Heart disease structured prediction"),
    "diabetes": ("diabetes", "Diabetes structured prediction"),
    "glucose": ("diabetes", "Diabetes structured prediction"),
    "liver": ("liver", "Liver disease structured prediction"),
    "kidney": ("kidney", "Kidney disease structured prediction"),
    "renal": ("kidney", "Kidney disease structured prediction"),
    "lung": ("lungs", "Lung health structured prediction"),
    "lungs": ("lungs", "Lung health structured prediction"),
}


def build_external_research_query(query: str) -> str:
    """Build a non-identifying query for external medical literature search."""
    query_lower = _coerce_context(query).lower()
    terms = ["clinical research"]

    if any(word in query_lower for word in ["latest", "news", "2024", "2025", "2026"]):
        terms.insert(0, "latest")
    if "treatment" in query_lower:
        terms.append("treatment guidelines")
    if "study" in query_lower or "research" in query_lower:
        terms.append("medical studies")

    matched_areas = []
    seen = set()
    for keyword, (area, _label) in SUPPORTED_ANALYSIS_AREAS.items():
        if keyword in query_lower and area not in seen:
            matched_areas.append(area)
            seen.add(area)

    if matched_areas:
        terms.extend(matched_areas)
    else:
        terms.append("healthcare")

    return " ".join(terms)


# ── core_ai-backed LLM Wrapper ────────────────────────────────────────
# Wraps the multi-tier AI engine (Ollama → Gemini → Cloud) in a
# LangChain-compatible .invoke() interface for the LangGraph agent.

class CoreAIWrapper:
    """LangChain-compatible wrapper around core_ai multi-tier inference."""

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        full_prompt = ""
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "System" if isinstance(msg, SystemMessage) else "AI"
            full_prompt += f"{role}: {msg.content}\n\n"

        try:
            # Run async generate in sync context
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

            if loop and loop.is_running():
                # We're inside an async context — use a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, core_ai.generate(full_prompt)).result()
            else:
                result = asyncio.run(core_ai.generate(full_prompt))

            if result:
                return AIMessage(content=result)
            return AIMessage(content="AI is temporarily unavailable. Please try again shortly.")

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Quota" in err_str:
                return AIMessage(content="⚠️ **Quota Exceeded.** Please wait a moment or configure a local Ollama model for unlimited free inference.")
            logger.error("AI generation failed")
            return AIMessage(content=AI_GENERATION_FAILURE_MESSAGE)


# Global instance — uses multi-tier inference automatically
llm = CoreAIWrapper()

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
            return SEARCH_UPSTREAM_ERROR_MESSAGE
    except Exception:
        return SEARCH_FAILURE_MESSAGE

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
    logger.info("Researching healthcare topic")
    results = tavily_search(build_external_research_query(query))
    return {"tavily_results": results}


def _coerce_context(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compact_context(value: object, *, limit: int = 700) -> str:
    text = " ".join(_coerce_context(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_clinical_analysis_context(state: AgentState) -> str:
    """Build deterministic clinical analysis from already-scoped agent context."""
    messages = state.get("messages", [])
    latest_message = messages[-1].content if messages else ""
    available_reports = _compact_context(state.get("available_reports"))
    rag_memories = _compact_context(state.get("rag_memories"), limit=500)
    combined_text = f"{latest_message} {available_reports} {rag_memories}".lower()

    matched = []
    seen = set()
    for keyword, (area, label) in SUPPORTED_ANALYSIS_AREAS.items():
        if keyword in combined_text and area not in seen:
            matched.append((area, label))
            seen.add(area)

    lines = []
    if available_reports or rag_memories:
        lines.append("Relevant patient context:")
        if available_reports:
            lines.append(f"- Recent records: {available_reports}")
        if rag_memories:
            lines.append(f"- Related memory: {rag_memories}")
    else:
        lines.append("No prior scoped health records were provided for this analysis request.")

    if matched:
        model_labels = ", ".join(label for _, label in matched)
        lines.append(f"Applicable structured prediction areas: {model_labels}.")
    else:
        lines.append(
            "No supported prediction area was clearly identified from the request or scoped records."
        )

    lines.append(
        "Do not produce a numeric risk score from chat text alone; ask the user to use "
        "the validated structured prediction form before giving a model-based risk estimate."
    )
    lines.append(
        "Frame the answer as educational support, mention uncertainty, and recommend a "
        "qualified clinician for diagnosis, treatment, or urgent symptoms."
    )
    return "\n".join(lines)


def analyst_node(state: AgentState):
    """Builds deterministic clinical analysis context from scoped records."""
    return {"analysis_results": build_clinical_analysis_context(state)}

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
    Uses version-controlled prompt from prompt_registry.
    """
    messages = state['messages']
    profile = state.get("user_profile", "Unknown")
    medical_history = state.get("available_reports", "")
    rag_context = state.get("rag_memories", "")
    web_data = state.get("tavily_results", "")
    analysis_context = state.get("analysis_results", "")
    conv_count = state.get("conversation_count", 1)

    # Determine conversation phase for engagement style
    if conv_count <= 2:
        engagement_style = "WELCOMING: This is a new or early conversation. Be warm and build rapport."
    elif conv_count <= 5:
        engagement_style = "ENGAGED: User is actively chatting. Reference their previous messages in this session."
    else:
        engagement_style = "DEEP SESSION: Long conversation. Summarize key points discussed and offer next steps."

    # Use version-controlled prompt from the registry
    system_prompt = get_prompt("chat_system").format(
        user_profile=profile,
        medical_history=medical_history,
        rag_context=rag_context,
        analysis_context=analysis_context if analysis_context else "N/A",
        web_context=web_data if web_data else "N/A",
        engagement_style=engagement_style,
    )

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
workflow.add_node("analyst", analyst_node)
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
