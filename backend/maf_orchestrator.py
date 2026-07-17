import json
import logging
import time
from typing import Any, Mapping, Sequence

from agent_framework import BaseChatClient, ChatResponse, Message

logger = logging.getLogger(__name__)


class CoreAIChatClient(BaseChatClient):
    """
    A custom ChatClient for Microsoft Agent Framework (MAF) that routes
    all model inferences safely through our unified core_ai module.
    """

    def __init__(self, model_id: str = "gemini-1.5-pro", **kwargs: Any):
        super().__init__(**kwargs)
        self.model_id = model_id

    async def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> ChatResponse:
        if stream:
            raise NotImplementedError("Streaming is not supported for CoreAIChatClient")

        # Translate MAF messages to core_ai messages
        formatted_messages = []
        system_instruction = ""
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.text
            elif msg.role in ("user", "assistant"):
                formatted_messages.append({"role": msg.role, "content": msg.text})
            else:
                formatted_messages.append({"role": "user", "content": msg.text})

        # Call core_ai.chat
        from backend.core_ai import chat as core_ai_chat

        reply_text = await core_ai_chat(
            messages=formatted_messages,
            system=system_instruction,
            model=self.model_id,
        )

        response_message = Message(role="assistant", contents=[reply_text])
        return ChatResponse(messages=[response_message])

    def service_url(self) -> str:
        return "local://core_ai"


async def run_maf_billing_audit(soap_note: str) -> dict:
    """
    Runs the clinical billing audit using Microsoft Agent Framework (MAF).
    """
    start_time = time.time()
    if not soap_note or not soap_note.strip():
        return {"error": "SOAP note is empty."}

    client = CoreAIChatClient()
    agent = client.as_agent(
        name="ClinicalBillingAuditAgent",
        instructions="You are an expert clinical billing auditor specializing in HIPAA compliance, ICD-10/CPT coding, and claims denial mitigation.",
    )

    from backend.prompt_registry import get_prompt

    prompt = get_prompt("clinical_billing_audit").format(soap_note=soap_note)

    # Run the MAF agent
    result = await agent.run(prompt)
    raw_output = result.text

    duration = round(time.time() - start_time, 2)

    # Estimating tokens: 1 token approx 4 characters
    input_tokens = len(prompt) // 4
    output_tokens = len(raw_output) // 4
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.30
    estimated_cost = round(input_cost + output_cost, 6)

    try:
        # Clean raw output from any markdown block formatting
        clean_str = raw_output.strip()
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        if clean_str.endswith("```"):
            clean_str = clean_str[:-3]
        clean_str = clean_str.strip()

        structured_report = json.loads(clean_str)
        return {
            "telemetry": {
                "duration": duration,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": estimated_cost,
            },
            "data": structured_report,
        }
    except Exception as e:
        logger.warning("Failed to parse billing audit output as JSON: %s", e)
        fallback = {
            "icd10_codes": [],
            "cpt_codes": [],
            "denial_risk": "HIGH",
            "warnings": [f"Failed to parse structured audit report: {str(e)}"],
            "recommendations": ["Review clinical note manually; model output was not valid JSON."],
        }
        return {
            "telemetry": {
                "duration": duration,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": estimated_cost,
            },
            "data": fallback,
        }


async def run_maf_handoff_audit(soap_note: str) -> dict:
    """
    Runs a multi-agent claim audit using MAF's SequentialBuilder orchestration.
    """
    start_time = time.time()
    if not soap_note or not soap_note.strip():
        return {"error": "SOAP note is empty."}

    client = CoreAIChatClient()

    billing_agent = client.as_agent(
        id="ClinicalBillingAgent",
        name="ClinicalBillingAgent",
        instructions="You are a clinical billing compliance auditor. Recommend ICD-10 and CPT codes based on the SOAP note.",
        require_per_service_call_history_persistence=True,
    )

    safety_agent = client.as_agent(
        id="SafetyComplianceAgent",
        name="SafetyComplianceAgent",
        instructions="You are a clinical safety and compliance supervisor. Double-check all recommended codes and SOAP notes for safety, confidentiality, or mismatches. Write a brief safety audit summary and conclude with 'AUDIT COMPLETE'.",
        require_per_service_call_history_persistence=True,
    )

    from agent_framework.orchestrations import SequentialBuilder

    workflow = (
        SequentialBuilder(
            participants=[billing_agent, safety_agent],
            intermediate_output_from="all_other"
        )
        .build()
    )


    # Run the sequential workflow
    run_result = await workflow.run(soap_note)

    duration = round(time.time() - start_time, 2)

    # Extract conversation events
    conversation_steps = []
    total_chars_in = len(soap_note)
    total_chars_out = 0

    for event in run_result:
        if event.type == "output" or event.type == "intermediate":
            resp = event.data
            # In MAF sequential workflow, the response is typically wrapped in AgentExecutorResponse
            # let's extract text safely
            if hasattr(resp, "text"):
                text_content = resp.text
            elif hasattr(resp, "messages") and resp.messages:
                text_content = "".join(msg.text for msg in resp.messages)
            else:
                text_content = str(resp)

            total_chars_out += len(text_content)

            # Identify agent based on class or ID
            agent_id = getattr(resp, "agent_id", "Agent") or "Agent"
            if not agent_id or agent_id == "Agent":
                # Fallback to identify based on order
                agent_id = "ClinicalBillingAgent" if len(conversation_steps) == 0 else "SafetyComplianceAgent"

            conversation_steps.append({
                "agent": agent_id,
                "text": text_content
            })

    # Telemetry estimation
    input_tokens = total_chars_in // 4
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
        "steps": conversation_steps,
    }


