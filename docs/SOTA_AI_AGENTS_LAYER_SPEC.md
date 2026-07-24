# SOTA Multi-Agent Clinical Orchestration Specification

This document specifies the Graph-Based DAG Multi-Agent Routing, Reflexion self-critique, and Weighted Consensus Voting standards.

```
┌─────────────────────────────────────────────────────────────┐
│          Specialized Multi-Agent Expert Evaluators          │
│  - TriageAgent, PharmaAgent, DiagnosisAgent                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Weighted Expert Agent Consensus Synthesizer        │
│  - Combines domain confidence scores into unified plan      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤝 Key Multi-Agent Layer Standards

1. **Graph-Based Multi-Agent DAG Routing (`triage_agent_evaluate`, `pharma_agent_evaluate`)**:
   - Routes patient cases through specialized domain agents (Triage, Pharma, Clinical Diagnosis) concurrently.
2. **Reflexion Self-Correction Loops**:
   - Enables subagents to self-critique intermediate reasoning outputs prior to final action execution.
3. **Weighted Expert Consensus Plan Synthesizer (`synthesize_consensus_plan`)**:
   - Combines multi-agent recommendations and calculates weighted confidence metrics (`consensus_confidence`).
