"""
AI Healthcare System — Unified Data + AI Platform API Router.

Exposes REST endpoints for:
- Lakehouse SQL Query execution
- Clinical Data Catalog search & access checks
- MedFlow declarative ETL pipeline runs
- Agentic BI natural language analytics
- Spark 4.x Variant JSON shredding & Spark Connect session status
- Multi-Agent Supervisor Router & Plan-and-Execute Orchestration
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from backend.data_platform.lakehouse_sql import lakehouse_sql_engine
from backend.data_platform.data_catalog import clinical_data_catalog, AssetType
from backend.data_platform.lakeflow import medflow_orchestrator
from backend.data_platform.agentic_bi import agentic_bi_engine
from backend.data_platform.data_apps import data_ai_apps_runtime
from backend.spark_engine import spark4_variant_handler, spark_connect_manager
from backend.agents.supervisor_orchestrator import (
    supervisor_router,
    plan_and_execute_orchestrator,
    AgentCapability,
    RegisteredAgent,
)

# Seed default specialist agents into the supervisor router if empty
if supervisor_router.agent_count == 0:
    supervisor_router.register_agent(RegisteredAgent(
        agent_id="AGENT-ED-TRIAGE",
        name="Emergency Department Triage Specialist",
        capabilities=[AgentCapability.TRIAGE, AgentCapability.SAFETY],
        priority=10,
    ))
    supervisor_router.register_agent(RegisteredAgent(
        agent_id="AGENT-PHARM-SAFETY",
        name="Pharmacy Safety & Dosage Specialist",
        capabilities=[AgentCapability.PHARMACY, AgentCapability.SAFETY],
        priority=9,
    ))
    supervisor_router.register_agent(RegisteredAgent(
        agent_id="AGENT-RAD-PREREAD",
        name="Radiology Pre-Reader Agent",
        capabilities=[AgentCapability.RADIOLOGY],
        priority=8,
    ))
    supervisor_router.register_agent(RegisteredAgent(
        agent_id="AGENT-DISCHARGE-SUMM",
        name="Discharge Summary & Care Continuity Agent",
        capabilities=[AgentCapability.DISCHARGE],
        priority=7,
    ))

router = APIRouter(prefix="/api/v1/data-platform", tags=["Unified Data Platform"])


# =====================================================================
# Request & Response Schemas
# =====================================================================

class SQLExecuteRequest(BaseModel):
    sql: str
    warehouse_id: Optional[str] = "clinical-warehouse-01"


class BIAskRequest(BaseModel):
    question: str
    table: Optional[str] = "sql_test"


class VariantShredRequest(BaseModel):
    raw_json: str
    target_fields: List[str] = Field(default_factory=list)


class AgentRouteRequest(BaseModel):
    capability: str  # "TRIAGE", "PHARMACY", "RADIOLOGY", "DISCHARGE", "SAFETY"


class PlanExecuteRequest(BaseModel):
    goal: str
    steps: List[Dict[str, Any]]


# =====================================================================
# Endpoints
# =====================================================================

@router.post("/sql/execute")
def execute_lakehouse_sql(req: SQLExecuteRequest) -> Dict[str, Any]:
    """Execute SQL query over Lakehouse ACID tables."""
    try:
        res = lakehouse_sql_engine.execute(req.sql)
        return {
            "columns": res.columns,
            "rows": res.rows,
            "total_count": res.total_count,
            "profile": res.profile.model_dump(),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/catalog/search")
def search_catalog(
    query: str = Query(..., min_length=1),
    asset_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Search Clinical Data Catalog assets."""
    atype = AssetType(asset_type) if asset_type else None
    results = clinical_data_catalog.search(query, asset_type=atype)
    return {
        "query": query,
        "results_count": len(results),
        "assets": [a.model_dump() for a in results],
    }


@router.post("/bi/ask")
def ask_agentic_bi(req: BIAskRequest) -> Dict[str, Any]:
    """Answer natural language BI question using AI BI Engine."""
    try:
        ans = agentic_bi_engine.ask(req.question, table=req.table or "sql_test")
        return ans.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/spark/variant-shred")
def shred_variant_json(req: VariantShredRequest) -> Dict[str, Any]:
    """Parse & shred semi-structured JSON using Spark 4.x Variant Engine."""
    try:
        shredded = spark4_variant_handler.parse_variant_blob(req.raw_json, req.target_fields)
        return shredded.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/apps/list")
def list_data_apps() -> Dict[str, Any]:
    """List registered Data & AI Apps."""
    apps = data_ai_apps_runtime.list_apps()
    return {"total": len(apps), "apps": [a.model_dump() for a in apps]}


@router.post("/agents/route")
def route_agent_task(req: AgentRouteRequest) -> Dict[str, Any]:
    """Route task to best-fit specialist agent via Multi-Agent Supervisor."""
    try:
        cap = AgentCapability(req.capability.upper())
        decision = supervisor_router.route(cap)
        return decision.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid capability. Choose from: {[c.value for c in AgentCapability]}")


@router.post("/agents/plan-and-execute")
def plan_and_execute_agent_goal(req: PlanExecuteRequest) -> Dict[str, Any]:
    """Decompose and execute multi-step clinical plan via Plan-and-Execute Orchestrator."""
    try:
        from backend.agents.supervisor_orchestrator import PlanStep
        plan_steps = [
            PlanStep(
                description=s["description"],
                required_capability=AgentCapability(s["required_capability"].upper()),
                tool_name=s.get("tool_name"),
                tool_kwargs=s.get("tool_kwargs", {}),
            )
            for s in req.steps
        ]
        exec_plan = plan_and_execute_orchestrator.plan(req.goal, plan_steps)
        res_plan = plan_and_execute_orchestrator.execute(exec_plan)
        return res_plan.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/agents/fraud-detection/analyze")
def analyze_claim_fraud(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze claim for upcoding, phantom billing, and duplicate fraud."""
    from backend.agents.enterprise_clinical_agents import agent_fraud_detection
    res = agent_fraud_detection.analyze_claim(claim_data)
    return res.model_dump()


@router.post("/agents/entity-resolution/resolve")
def resolve_patient_entity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve patient identity & deduplicate EMPI records."""
    from backend.agents.enterprise_clinical_agents import agent_entity_resolution
    candidate = payload.get("candidate", {})
    master = payload.get("master_records", [])
    res = agent_entity_resolution.resolve_entity(candidate, master)
    return res.model_dump()


@router.post("/agents/cost-analyzer/analyze")
def analyze_patient_cost(patient_case: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze treatment cost, DRG length of stay, & savings opportunities."""
    from backend.agents.enterprise_clinical_agents import agent_cost_analyzer
    res = agent_cost_analyzer.analyze_cost(patient_case)
    return res.model_dump()


@router.post("/agents/future-forecast/predict")
def predict_hospital_forecast(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Forecast ED surge, ICU bed demand, & patient trajectory."""
    from backend.agents.enterprise_clinical_agents import agent_future_forecast
    history = payload.get("historical_counts", [50.0, 55.0, 52.0, 58.0, 60.0])
    horizon = payload.get("forecast_horizon_days", 7)
    res = agent_future_forecast.forecast_demand(history, horizon)
    return res.model_dump()


@router.post("/agents/prior-auth/process")
def process_prior_auth_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process prior authorization request against medical necessity guidelines."""
    from backend.agents.hospital_operations_agents import agent_prior_auth
    res = agent_prior_auth.process_prior_auth(request_data)
    return res.model_dump()


@router.post("/agents/sepsis/evaluate")
def evaluate_icu_sepsis_risk(vital_stream: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate real-time ICU qSOFA score & sepsis deterioration risk."""
    from backend.agents.hospital_operations_agents import agent_sepsis_deterioration
    res = agent_sepsis_deterioration.evaluate_sepsis_risk(vital_stream)
    return res.model_dump()


@router.post("/agents/surgical-or/optimize")
def optimize_surgical_or_schedule(surgical_case: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize operating room turnover, scheduling, & sterilization prep."""
    from backend.agents.hospital_operations_agents import agent_surgical_or
    res = agent_surgical_or.optimize_or_schedule(surgical_case)
    return res.model_dump()


@router.post("/agents/trial-matching/match")
def match_clinical_trials(patient_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Match patient profile & biomarkers to active ClinicalTrials.gov protocols."""
    from backend.agents.clinical_research_rpm_agents import agent_trial_matching
    res = agent_trial_matching.match_trials(patient_profile)
    return res.model_dump()


@router.post("/agents/rpm-adherence/evaluate")
def evaluate_rpm_adherence(rpm_telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate remote patient telemetry & medication adherence compliance."""
    from backend.agents.clinical_research_rpm_agents import agent_rpm_adherence
    res = agent_rpm_adherence.evaluate_rpm(rpm_telemetry)
    return res.model_dump()


@router.post("/agents/governed-execute")
def execute_governed_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute agent action under full FDA audit logging, lineage tracking, & auto-resolution."""
    from backend.agents.agent_governance_engine import agent_governance_engine
    from backend.agents.hospital_operations_agents import agent_sepsis_deterioration
    
    agent_id = payload.get("agent_id", "AGENT-ICU-SEPSIS")
    action_name = payload.get("action_name", "evaluate_sepsis_risk")
    input_data = payload.get("input_data", {"respiratory_rate": 25, "systolic_bp": 90, "gcs_score": 13})
    
    res = agent_governance_engine.execute_governed_action(
        agent_id=agent_id,
        action_name=action_name,
        input_data=input_data,
        agent_func=lambda data: agent_sepsis_deterioration.evaluate_sepsis_risk(data).model_dump(),
    )
    return res.model_dump()


@router.get("/agents/lineage")
def get_agent_data_lineage() -> Dict[str, Any]:
    """Retrieve full agent data lineage provenance graph."""
    from backend.agents.agent_governance_engine import agent_governance_engine
    chain = agent_governance_engine.get_lineage_chain()
    return {"total_nodes": len(chain), "lineage_graph": chain}
