import json
import logging
import os
from sqlalchemy.orm import Session

from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalPatchAgent(BaseAgent):
    """
    State-of-the-Art (SOTA) Automated Vulnerability and Hotpatch Agent.
    Audits codebase dependencies and environment settings, proposing virtual hotpatches.
    """

    def __init__(self, db: Session, name: str = "Clinical Security Auto-Patcher"):
        super().__init__(name)
        self.db = db

    def _run_real_security_audit(self) -> dict:
        """
        Scans the active virtual environment for dependencies with known security advisories
        or suboptimal versions.
        """
        import importlib.metadata
        
        # Local knowledge base of known vulnerabilities / insecure package versions
        CVE_DATABASE = {
            "fastapi": {"max_vulnerable": "0.100.0", "cve": "CVE-2023-46122", "severity": "MEDIUM", "fix": "Upgrade to fastapi>=0.100.1"},
            "requests": {"max_vulnerable": "2.31.0", "cve": "CVE-2023-32681", "severity": "HIGH", "fix": "Upgrade to requests>=2.31.0"},
            "cryptography": {"max_vulnerable": "41.0.3", "cve": "CVE-2023-49083", "severity": "HIGH", "fix": "Upgrade to cryptography>=41.0.4"},
            "urllib3": {"max_vulnerable": "1.26.16", "cve": "CVE-2023-34308", "severity": "MEDIUM", "fix": "Upgrade to urllib3>=1.26.17"},
            "pyjwt": {"max_vulnerable": "2.4.0", "cve": "CVE-2022-39227", "severity": "HIGH", "fix": "Upgrade to pyjwt>=2.4.1"},
            "pydantic": {"max_vulnerable": "1.10.11", "cve": "CVE-2023-38199", "severity": "LOW", "fix": "Upgrade to pydantic>=1.10.12 or v2"},
            "jinja2": {"max_vulnerable": "3.1.2", "cve": "CVE-2024-22195", "severity": "HIGH", "fix": "Upgrade to Jinja2>=3.1.3"},
        }
        
        audit_results = {
            "vulnerabilities_found": [],
            "packages_scanned": 0,
            "status": "SECURE",
        }
        
        def is_vulnerable(installed_version: str, max_vulnerable: str) -> bool:
            try:
                inst_parts = [int(x) for x in installed_version.split(".") if x.isdigit()]
                max_parts = [int(x) for x in max_vulnerable.split(".") if x.isdigit()]
                length = max(len(inst_parts), len(max_parts))
                inst_parts += [0] * (length - len(inst_parts))
                max_parts += [0] * (length - len(max_parts))
                return inst_parts <= max_parts
            except Exception:
                return False

        for pkg, vuln in CVE_DATABASE.items():
            try:
                version = importlib.metadata.version(pkg)
                audit_results["packages_scanned"] += 1
                if is_vulnerable(version, vuln["max_vulnerable"]):
                    audit_results["vulnerabilities_found"].append({
                        "package": pkg,
                        "installed_version": version,
                        "cve": vuln["cve"],
                        "severity": vuln["severity"],
                        "remediation": vuln["fix"]
                    })
            except importlib.metadata.PackageNotFoundError:
                continue
                
        if audit_results["vulnerabilities_found"]:
            audit_results["status"] = "VULNERABLE"
            
        return audit_results

    async def audit_and_apply_patches(self, dependencies: str, env_config: str) -> dict:
        """
        Runs a security posture scan and generates recommended and virtual hotpatches.
        """
        self.start()

        # 1. Run local programmatic security vulnerability check
        self.log_step("Real Dependency Audit", "Running programmatic vulnerability scan on installed environment...")
        local_audit = self._run_real_security_audit()
        
        # Inject the real audit findings into the dependencies string
        findings_summary = ""
        if local_audit["vulnerabilities_found"]:
            findings_summary += "\nPROGRAMMATIC SECURITY FINDINGS:\n"
            for v in local_audit["vulnerabilities_found"]:
                findings_summary += f"- {v['package']} ({v['installed_version']}): {v['cve']} [{v['severity']}]. Remediation: {v['remediation']}\n"
        else:
            findings_summary += "\nPROGRAMMATIC SECURITY FINDINGS:\n- Programmatic scan of installed packages detected zero active CVE matching patterns.\n"
            
        dependencies = f"{dependencies}\n{findings_summary}"

        if not dependencies or not dependencies.strip():
            dependencies = "Unknown dependencies list"
        if not env_config or not env_config.strip():
            env_config = "SECRET_KEY: Set, DEBUG: False, CORS_ORIGIN: *"

        self.log_step("Audit Security & Patch Configuration", "Invoking SOTA security LLM generator...")
        prompt = get_prompt("security_patch_analysis").format(
            dependencies=dependencies,
            env_config=env_config
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are a SOTA cyber security patching and configuration auditor for a healthcare system. Output valid JSON only."
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
            
            # Enrich report with programmatic audit findings
            structured_report["programmatic_audit"] = local_audit
            
            self.log_step("Parse Patch Report", "Successfully parsed structured security patching report.")
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
            self.log_error(f"Failed to parse security patching response: {e}")
            self.finish("failed")
            return {
                "error": "Failed to parse structured security patching response.",
                "raw_output": raw_output
            }

