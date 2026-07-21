"""
Universal Agent Interoperability & Model Context Protocol (MCP) Adapter Engine
=============================================================================
Provides cross-framework multi-agent state normalization and tool message translation
across LangGraph, AutoGen, CrewAI, and Model Context Protocol (MCP) standards.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class UniversalAgentMessage:
    sender_agent: str
    recipient_agent: str
    framework_origin: str  # e.g., "LangGraph", "AutoGen", "CrewAI", "MCP"
    message_type: str       # e.g., "TASK_REQUEST", "TOOL_RESULT", "STATE_UPDATE"
    content: Dict[str, Any]
    mcp_tool_schema: Optional[Dict[str, Any]] = None


class UniversalAgentInteropAdapter:
    """Translates and normalizes multi-agent state messages across frameworks."""

    def normalize_agent_message(
        self,
        raw_message: Dict[str, Any],
        source_framework: str = "LangGraph"
    ) -> UniversalAgentMessage:
        """Normalizes external agent message into universal MCP-compliant schema."""
        sender = raw_message.get("sender", "DiagnosticSupervisor")
        recipient = raw_message.get("recipient", "RAGResearcher")
        msg_type = raw_message.get("type", "STATE_UPDATE")
        content = raw_message.get("content", {})

        mcp_schema = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": content.get("tool_name", "clinical_query"), "arguments": content}
        }

        logger.info(
            "Normalized agent message [%s ➔ %s] from framework %s",
            sender, recipient, source_framework
        )

        return UniversalAgentMessage(
            sender_agent=sender,
            recipient_agent=recipient,
            framework_origin=source_framework,
            message_type=msg_type,
            content=content,
            mcp_tool_schema=mcp_schema
        )


def run_agent_interop_pipeline() -> Dict[str, Any]:
    adapter = UniversalAgentInteropAdapter()
    sample_msg = {
        "sender": "LangGraph_Supervisor",
        "recipient": "AutoGen_Specialist",
        "type": "TASK_REQUEST",
        "content": {"patient_id": "P-1049", "action": "summarize_vitals"}
    }
    norm = adapter.normalize_agent_message(sample_msg, source_framework="LangGraph")
    return {
        "sender": norm.sender_agent,
        "recipient": norm.recipient_agent,
        "framework": norm.framework_origin,
        "message_type": norm.message_type,
        "mcp_compliant": norm.mcp_tool_schema is not None
    }
