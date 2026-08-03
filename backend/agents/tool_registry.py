"""
AI Healthcare System — Agentic AI Tool Registry.

Provides a typed, introspectable registry of tools that autonomous clinical agents
can dynamically discover, bind, and invoke at runtime. Supports both native Rust
PyO3 tools and pure-Python tools with JSON Schema metadata.
"""

from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentToolSchema(BaseModel):
    """Describes a single tool an agent can invoke."""
    name: str
    description: str
    parameter_schema: Dict[str, Any] = Field(default_factory=dict)
    return_type: str = "Any"
    is_rust_native: bool = False


class AgentToolRegistry:
    """
    Central registry of all tools available to autonomous agents.

    Agents query the registry at planning time to discover available actions,
    then bind and invoke them during the ReAct execution loop.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, AgentToolSchema] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        parameter_schema: Optional[Dict[str, Any]] = None,
        return_type: str = "Any",
        is_rust_native: bool = False,
    ) -> None:
        """Register a callable tool with its schema."""
        self._tools[name] = func
        self._schemas[name] = AgentToolSchema(
            name=name,
            description=description,
            parameter_schema=parameter_schema or {},
            return_type=return_type,
            is_rust_native=is_rust_native,
        )

    def invoke(self, name: str, **kwargs: Any) -> Any:
        """Invoke a registered tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry. Available: {list(self._tools.keys())}")
        return self._tools[name](**kwargs)

    def list_tools(self) -> List[AgentToolSchema]:
        """Return schemas of all registered tools for agent planning."""
        return list(self._schemas.values())

    def get_schema(self, name: str) -> Optional[AgentToolSchema]:
        """Return schema for a specific tool."""
        return self._schemas.get(name)

    @property
    def tool_count(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)


# ---------------------------------------------------------------------------
# Global singleton — agents import and use this instance
# ---------------------------------------------------------------------------
agent_tool_registry = AgentToolRegistry()

# ---------------------------------------------------------------------------
# Pre-register Rust-backed clinical tools (with Python fallbacks)
# ---------------------------------------------------------------------------
from backend.sota_rust_engine_layer import sota_rust_engine_layer_engine

agent_tool_registry.register(
    name="compute_egfr",
    func=sota_rust_engine_layer_engine.compute_rust_egfr,
    description="Calculate CKD-EPI 2021 eGFR using Rust PyO3 engine.",
    parameter_schema={"serum_creatinine": "float", "age": "float", "is_female": "bool"},
    return_type="float",
    is_rust_native=True,
)

agent_tool_registry.register(
    name="redact_phi",
    func=sota_rust_engine_layer_engine.redact_phi_text_rust,
    description="Redact PII/PHI (SSNs, emails) from clinical text using Rust SIMD regex.",
    parameter_schema={"text": "str"},
    return_type="str",
    is_rust_native=True,
)

agent_tool_registry.register(
    name="hash_password",
    func=sota_rust_engine_layer_engine.hash_password_rust,
    description="Hash a password using Rust-native bcrypt.",
    parameter_schema={"password": "str"},
    return_type="str",
    is_rust_native=True,
)

agent_tool_registry.register(
    name="aggregate_fedavg",
    func=sota_rust_engine_layer_engine.aggregate_fedavg_rust,
    description="Aggregate federated learning gradients using Rust SIMD FedAvg.",
    parameter_schema={"gradients": "List[List[float]]", "weights": "List[float]"},
    return_type="List[float]",
    is_rust_native=True,
)
