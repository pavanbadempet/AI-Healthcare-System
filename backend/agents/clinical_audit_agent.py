from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.models.clinical import MonitoringSignal, VitalObservation


class ClinicalAuditAgent(BaseAgent):
    """
    Clinical Audit & Alert Agent.
    Scans recent vitals and alerts from the database, runs LLM risk assessment
    summaries and generates clinical audit reports.
    """

    def __init__(self, db: Session, name: str = "Clinical Audit Agent"):
        super().__init__(name)
        self.db = db

    async def run(self, hours: int = 24, dry_run: bool = False) -> Tuple[str, Dict[str, Any]]:
        """
        Runs the clinical audit agent loop.
        Returns:
            A tuple of (report_markdown: str, report_json: dict)
        """
        self.start()

        # 1. Fetch data
        self.log_step("Fetch Recent Data", f"Querying database for records in the last {hours} hours.")
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Query active critical signals
        signals = (
            self.db.query(MonitoringSignal)
            .filter(MonitoringSignal.created_at >= cutoff_time)
            .filter(MonitoringSignal.severity.in_(["critical", "warning"]))
            .order_by(desc(MonitoringSignal.created_at))
            .all()
        )

        self.log_step("Filter High-Risk Patients", f"Found {len(signals)} critical/warning signals in the specified timeframe.")

        # Group by patient to avoid duplicate assessments in the same run
        patients_to_audit = {}
        for sig in signals:
            if sig.patient_id not in patients_to_audit:
                patients_to_audit[sig.patient_id] = {
                    "patient": sig.patient,
                    "signals": [],
                    "latest_vitals": None
                }
            patients_to_audit[sig.patient_id]["signals"].append(sig)

        # Retrieve latest vitals for each patient
        for patient_id, data in patients_to_audit.items():
            latest_vitals = (
                self.db.query(VitalObservation)
                .filter(VitalObservation.patient_id == patient_id)
                .order_by(desc(VitalObservation.observed_at))
                .limit(5)
                .all()
            )
            data["latest_vitals"] = latest_vitals

        # If no patients found, create a placeholder report
        if not patients_to_audit:
            no_data_msg = "No high-risk patients or critical alerts found in the database. System is stable."
            self.log_step("Run AI Clinical Assessment", "Skipped - database is healthy with no alerts.")
            self.finish("completed")

            report = f"# 🩺 Clinical Audit Report\n\nGenerated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n{no_data_msg}\n"
            report_json = {
                "name": self.name,
                "status": self.status,
                "duration_seconds": self.duration,
                "cost_usd": self.estimated_cost,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "scope_hours": hours,
                "audited_patients_count": 0,
                "audits": []
            }
            return report, report_json

        # 2. Perform AI assessment for each high-risk patient
        audits = []
        for patient_id, data in patients_to_audit.items():
            patient = data["patient"]
            patient_name = patient.full_name if (patient and patient.full_name) else (patient.username if patient else f"Patient #{patient_id}")
            latest = data["latest_vitals"][0] if data["latest_vitals"] else None

            self.log_step("Run AI Clinical Assessment", f"Evaluating clinical risk for patient: {patient_name}.")

            # Format vitals context
            vitals_str = "No recent vitals."
            if latest:
                vitals_str = (
                    f"Heart Rate: {latest.heart_rate} bpm, "
                    f"BP: {latest.systolic_bp}/{latest.diastolic_bp} mmHg, "
                    f"SpO2: {latest.spo2}%, "
                    f"Temp: {latest.temperature_c}°C, "
                    f"Respiratory Rate: {latest.respiratory_rate} breaths/min"
                )

            history_list = []
            for v in data["latest_vitals"][1:]:
                history_list.append(
                    f"- {v.observed_at.strftime('%Y-%m-%d %H:%M')}: HR={v.heart_rate}, BP={v.systolic_bp}/{v.diastolic_bp}, SpO2={v.spo2}%"
                )
            history_str = "\n".join(history_list) if history_list else "No prior history."

            signals_str = "\n".join([f"- [{s.severity.upper()}] {s.title}: {s.summary}" for s in data["signals"]])

            # Construct system prompt and user query
            system_prompt = (
                "You are an AI Clinical Audit Agent. Your job is to analyze real-time patient vitals, "
                "evaluate deterioration risk, and suggest immediate clinical actions. "
                "Keep your assessment structured, objective, and highly actionable. Include a medical disclaimer."
            )

            user_prompt = (
                f"Analyze the following patient telemetry record:\n\n"
                f"**Patient**: {patient_name}\n"
                f"**Latest Vitals**: {vitals_str}\n"
                f"**Recent Telemetry History**:\n{history_str}\n\n"
                f"**Triggered Alerts**:\n{signals_str}\n\n"
                f"Please provide:\n"
                f"1. A brief clinical risk assessment (deterioration likelihood, critical concerns).\n"
                f"2. Three priority clinical recommendations (interventions, tests, precautions).\n"
            )

            self.estimate_tokens(user_prompt, is_output=False)

            if dry_run:
                # Dynamic clinical heuristic fallback
                recs = []
                concerns = []
                if latest:
                    if latest.spo2 and latest.spo2 < 90:
                        concerns.append("Severe oxygen desaturation (hypoxia)")
                        recs.append("Immediately check/escalate oxygen flow rate and elevate head of bed.")
                    elif latest.spo2 and latest.spo2 < 94:
                        concerns.append("Mild hypoxia desaturation")
                        recs.append("Monitor blood oxygen saturation closely every 1 hour.")

                    if latest.heart_rate and latest.heart_rate > 120:
                        concerns.append("Severe tachycardia (elevated pulse)")
                        recs.append("Request a 12-lead ECG, assess hydration, check serum electrolytes.")
                    elif latest.heart_rate and latest.heart_rate > 100:
                        concerns.append("Mild tachycardia")
                        recs.append("Assess patient for pain, anxiety, or fever.")

                    if latest.temperature_c and latest.temperature_c > 38.5:
                        concerns.append("High fever (pyrexia)")
                        recs.append("Administer antipyretics as ordered, obtain blood cultures if indicated.")

                    if latest.respiratory_rate and latest.respiratory_rate > 24:
                        concerns.append("Tachypnea (rapid breathing)")
                        recs.append("Assess work of breathing, monitor respiratory fatigue.")

                if not concerns:
                    concerns.append("Borderline vital fluctuations or anomaly reports.")
                    recs.append("Re-evaluate vitals in 2 hours and review medication list.")

                # Format recommendations list
                recs_str = "\n".join([f"{idx+1}. {r}" for idx, r in enumerate(recs[:3])])
                if len(recs) < 3:
                    recs_str += f"\n{len(recs)+1}. Continue continuous vitals tracking."

                ai_response = (
                    f"**[HEURISTIC LOCAL ASSESSMENT (DRY RUN)]**\n"
                    f"Clinical Deterioration Likelihood: Elevated. Major Concerns: {', '.join(concerns)}\n\n"
                    f"Priority Clinical Recommendations:\n{recs_str}"
                )
            else:
                try:
                    ai_response = await generate(user_prompt, system=system_prompt)
                except Exception as e:
                    self.log_error(f"AI generation failed for {patient_name}: {e}")
                    ai_response = "**ERROR:** Clinical assessment generation failed due to backend timeout/offline state."

            self.estimate_tokens(ai_response, is_output=True)

            audits.append({
                "patient_id": patient_id,
                "patient_name": patient_name,
                "latest_vitals": vitals_str,
                "alerts": signals_str,
                "assessment": ai_response
            })

        # 3. Construct the comprehensive report
        report_md = []
        report_md.append("# 🩺 Clinical Audit Report")
        report_md.append(f"Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        report_md.append(f"Audit Scope: Past {hours} hours")
        report_md.append("")

        report_md.append("## 🏥 Critical Alerts Summary")
        report_md.append("| Patient | Latest Telemetry | Triggered Alerts |")
        report_md.append("|---|---|---|")
        for audit in audits:
            # Clean up newlines for table
            al = audit["alerts"].replace("\n", "<br>")
            report_md.append(f"| **{audit['patient_name']}** | {audit['latest_vitals']} | {al} |")
        report_md.append("")

        report_md.append("## 📋 Patient-Specific Clinical Audits")
        for audit in audits:
            report_md.append(f"### 👤 Patient: {audit['patient_name']}")
            report_md.append(f"**Current Vitals**: {audit['latest_vitals']}")
            report_md.append("**Alert History**:")
            report_md.append(audit["alerts"])
            report_md.append("")
            report_md.append("**AI Clinical Analysis & Recommendations**:")
            report_md.append(audit["assessment"])
            report_md.append("")
            report_md.append("---")

        report_md.append("\n*Disclaimer: AI-generated health suggestions are for auditing support only. Always consult a qualified clinician for patient care.*")

        self.finish("completed")
        report_json = {
            "name": self.name,
            "status": self.status,
            "duration_seconds": self.duration,
            "cost_usd": self.estimated_cost,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scope_hours": hours,
            "audited_patients_count": len(audits),
            "audits": audits
        }
        return "\n".join(report_md), report_json
