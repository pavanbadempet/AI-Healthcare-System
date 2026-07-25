# SOTA Multi-Agent Swarm & DAG State Machine Specification

This document specifies Directed Acyclic Graph (DAG) multi-agent workflow orchestration, tool-calling safety guardrails, and plan verifier loops.

```
┌─────────────────────────────────────────────────────────────┐
│          Directed Acyclic Graph (DAG) Swarm Orchestrator    │
│  - Routes tasks across specialized clinician co-pilot agents│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Safety & Plan Verifier Reflection Guardrails       │
│  - Verifies multi-agent outputs against medical guidelines  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Key Agent Swarm Standards

1. **DAG Swarm Orchestration (`execute_clinical_agent_swarm`)**:
   - Executes multi-agent clinical decision-support workflows with tool-calling guardrails.
2. **Safety Verifier Reflection (`is_verified_safe`)**:
   - Enforces clinical verification before delivering AI recommendations to medical staff.
