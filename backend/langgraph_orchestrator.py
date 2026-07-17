import logging
import time
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from backend import core_ai

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    patient_id: int
    urgency_level: str  # "LOW", "HIGH"
    triage_report: str
    safety_approved: bool



async def triage_node(state: AgentState) -> dict[str, Any]:
    """
    Analyzes symptoms and initial vitals, generating a structured triage report.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    prompt = (
        f"Analyze the following patient clinical symptoms and decide if this is a high-urgency situation: \n\n"
        f"\"{last_message}\"\n\n"
        f"Provide a brief assessment. If there are red flag symptoms (e.g. chest pain, shortness of breath, severe head injury, high fever > 103F), "
        f"flag this case as HIGH urgency. Otherwise flag as LOW urgency."
    )

    system_prompt = (
        "You are an expert clinical triage assistant. Analyze clinical reports and symptoms. "
        "Keep your output short. Do not include patient name or PII."
    )

    # Call unified core_ai.chat
    raw_response = await core_ai.chat(
        messages=[{"role": "user", "content": prompt}],
        system=system_prompt
    )

    # Determine urgency level based on LLM response content
    urgency_level = "LOW"
    upper_response = raw_response.upper()
    if "HIGH" in upper_response or "RED FLAG" in upper_response or "URGENT" in upper_response:
        urgency_level = "HIGH"

    return {
        "messages": [AIMessage(content=raw_response)],
        "urgency_level": urgency_level,
        "triage_report": raw_response,
    }


async def escalation_node(state: AgentState) -> dict[str, Any]:
    """
    Escalates high-urgency patient cases for immediate clinician attention.
    """
    triage_report = state.get("triage_report", "")

    prompt = (
        f"The patient case was flagged as HIGH urgency based on this assessment:\n\n"
        f"\"{triage_report}\"\n\n"
        f"Generate a critical alerts warning summary for the emergency nursing supervisor."
    )

    system_prompt = (
        "You are a clinical supervisor. Draft a high-priority warning summary. "
        "Explicitly state that emergency triage protocols must be initiated."
    )

    raw_response = await core_ai.chat(
        messages=[{"role": "user", "content": prompt}],
        system=system_prompt
    )

    return {
        "messages": [AIMessage(content=f"[CRITICAL ALERTS] {raw_response}")],
    }


async def compliance_check_node(state: AgentState) -> dict[str, Any]:
    """
    Validates clinical outputs for safety, privacy guidelines, and appends the medical disclaimer.
    """
    messages = state["messages"]
    full_conversation = "\n".join([f"{msg.type}: {msg.content}" for msg in messages])

    prompt = (
        f"Review the clinical conversations and recommendations for medical safety compliance:\n\n"
        f"{full_conversation}\n\n"
        f"Ensure there is no PII and that standard medical disclaimers are appended."
    )

    system_prompt = (
        "You are a clinical compliance officer. Verify safety. Append: "
        "'Disclaimer: AI-generated health advice. Consult a clinician for emergencies.'"
    )

    raw_response = await core_ai.chat(
        messages=[{"role": "user", "content": prompt}],
        system=system_prompt
    )

    return {
        "messages": [AIMessage(content=raw_response)],
        "safety_approved": True,
    }


def route_urgency(state: AgentState) -> Literal["escalation", "compliance_check"]:
    """
    Router deciding whether to escalate or go directly to compliance review.
    """
    if state.get("urgency_level") == "HIGH":
        return "escalation"
    return "compliance_check"


# Build the LangGraph Workflow
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("triage", triage_node)
workflow.add_node("escalation", escalation_node)
workflow.add_node("compliance_check", compliance_check_node)

# Add Edges
workflow.add_edge(START, "triage")

# Conditional Router
workflow.add_conditional_edges(
    "triage",
    route_urgency,
    {
        "escalation": "escalation",
        "compliance_check": "compliance_check"
    }
)

workflow.add_edge("escalation", "compliance_check")
workflow.add_edge("compliance_check", END)

# Compile Graph
compiled_graph = workflow.compile()


async def run_langgraph_triage(symptoms: str, patient_id: int = 1) -> dict[str, Any]:
    """
    Runs the stateful LangGraph clinical triage pipeline.
    """
    start_time = time.time()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=symptoms)],
        "patient_id": patient_id,
        "urgency_level": "LOW",
        "triage_report": "",
        "safety_approved": False,
    }

    # Run the compiled graph
    final_state = await compiled_graph.ainvoke(initial_state)

    duration = round(time.time() - start_time, 2)

    # Format steps for frontend/reporting
    steps = []
    total_chars_out = 0
    for idx, msg in enumerate(final_state["messages"]):
        if idx == 0:
            continue  # Skip initial human symptom message
        text_content = msg.content
        total_chars_out += len(text_content)

        # Mapping message to node name/roles
        if "[CRITICAL ALERTS]" in text_content:
            node_name = "EscalationAgent"
        elif idx == len(final_state["messages"]) - 1:
            node_name = "ComplianceAgent"
        else:
            node_name = "TriageAgent"

        steps.append({
            "node": node_name,
            "text": text_content,
        })

    # Telemetry
    input_tokens = len(symptoms) // 4
    output_tokens = total_chars_out // 4
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.30
    estimated_cost = round(input_cost + output_cost, 6)

    return {
        "telemetry": {
            "duration": duration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": estimated_cost,
        },
        "urgency_level": final_state.get("urgency_level", "LOW"),
        "safety_approved": final_state.get("safety_approved", False),
        "steps": steps,
    }
