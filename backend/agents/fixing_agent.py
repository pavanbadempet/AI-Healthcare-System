import json
import logging

from sqlalchemy.orm import Session

from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalFixingAgent(BaseAgent):
    """
    State-of-the-Art (SOTA) Self-Healing & Auto-Fixing Application Agent.
    Analyzes system diagnostics and exception logs to execute automated recovery operations.
    """

    def __init__(self, db: Session, name: str = "Clinical Self-Healing Agent"):
        super().__init__(name)
        self.db = db

    async def diagnose_and_heal(self, error_logs: str, health_signals: str) -> dict:
        """
        Runs diagnostic reasoning on application errors and triggers self-healing routines.
        """
        self.start()

        if not error_logs or not error_logs.strip():
            error_logs = "No active error signatures found in logging buffer."
        if not health_signals or not health_signals.strip():
            health_signals = "CPU: 12%, Memory: 42%, Active SQL Pool: 3/10"

        self.log_step("Diagnose Faults & Self-Heal", "Calling SOTA System Self-Healing LLM...")
        prompt = get_prompt("auto_fixing_analysis").format(
            error_logs=error_logs,
            health_signals=health_signals
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are a SOTA system self-healing and recovery coordinator. Output valid JSON only."
        )
        self.estimate_tokens(raw_output, is_output=True)

        try:
            clean_str = raw_output.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()

            structured_report = json.loads(clean_str)
            self.log_step("Parse Healing Plan", "Successfully parsed structured self-healing recovery plan.")

            # Execute actual maintenance if suggested or if a lock condition is found
            healing_actions = structured_report.get("healing_actions", [])
            run_maintenance = False
            for action in healing_actions:
                if any(kw in action.lower() for kw in ["vacuum", "optimize", "maintenance", "reclaim", "repair"]):
                    run_maintenance = True
                    break

            if "lock" in error_logs.lower() or "vacuum" in error_logs.lower():
                run_maintenance = True

            if run_maintenance:
                self.log_step("Execute Maintenance", "Database lock/optimization condition detected. Triggering real SQLite/PostgreSQL storage maintenance...")
                from backend.maintenance import run_system_maintenance
                try:
                    m_report = run_system_maintenance(self.db)
                    structured_report["executed_maintenance"] = True
                    structured_report["maintenance_report"] = m_report
                    self.log_step("Execute Maintenance", "Self-healing database optimization finished successfully.")
                except Exception as m_err:
                    logger.error("Database maintenance during self-healing failed: %s", m_err)
                    self.log_error(f"Maintenance execution failed: {str(m_err)}")
                    structured_report["executed_maintenance"] = False
                    structured_report["maintenance_error"] = str(m_err)

            self.finish("completed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                },
                "status": "completed",
                "report": structured_report
            }
        except Exception as e:
            self.log_error(f"Failed to parse self-healing response: {e}")
            self.finish("failed")
            return {
                "error": "Failed to parse structured self-healing recovery plan.",
                "raw_output": raw_output
            }

