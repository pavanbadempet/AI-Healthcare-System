import os
import time
from typing import Any, Dict, List


class BaseAgent:
    """
    Base class for all portable AI agents in the APEX framework.
    Provides lifecycle management, step-by-step reasoning logs, execution telemetry,
    and automatic environment detection for platform-specific integration (e.g. GitHub Actions).
    """

    def __init__(self, name: str):
        self.name = name
        self.steps: List[Dict[str, Any]] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.input_tokens_estimated: int = 0
        self.output_tokens_estimated: int = 0
        self.status: str = "initialized"
        self.errors: List[str] = []

    def start(self):
        """Starts the agent execution session."""
        self.start_time = time.time()
        self.status = "running"
        self.log_step("Initialize Agent", f"Agent '{self.name}' initialized and running.")

    def finish(self, status: str = "completed"):
        """Finishes the agent execution session and prints/saves reports."""
        self.end_time = time.time()
        self.status = status
        self.log_step("Shutdown Agent", f"Agent '{self.name}' execution completed with status: {status}.")

        # Handle GitHub Actions environment integration
        if self.is_github_actions():
            self.write_github_step_summary()
            self.write_github_outputs()

    def log_step(self, action: str, result: str, status: str = "success"):
        """Logs a step in the agent's execution path."""
        step = {
            "index": len(self.steps) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "action": action,
            "result": result,
            "status": status,
        }
        self.steps.append(step)

    def log_error(self, message: str):
        """Logs an error encountered during agent execution."""
        self.errors.append(message)
        self.log_step("Error Encountered", message, status="failed")

    def estimate_tokens(self, text: str, is_output: bool = False):
        """Simple token estimation (1 token approx 4 characters)."""
        tokens = len(text) // 4
        if is_output:
            self.output_tokens_estimated += tokens
        else:
            self.input_tokens_estimated += tokens

    @property
    def duration(self) -> float:
        """Returns duration of the execution in seconds."""
        if self.start_time == 0.0:
            return 0.0
        end = self.end_time if self.end_time > 0.0 else time.time()
        return round(end - self.start_time, 2)

    @property
    def estimated_cost(self) -> float:
        """
        Estimate API cost of execution.
        Using a blended rate representing typical developer API prices in 2026:
        - Input: $0.075 / 1M tokens (highly optimized models)
        - Output: $0.30 / 1M tokens
        """
        input_cost = (self.input_tokens_estimated / 1_000_000) * 0.075
        output_cost = (self.output_tokens_estimated / 1_000_000) * 0.30
        return round(input_cost + output_cost, 6)

    def is_github_actions(self) -> bool:
        """Checks if the agent is running in a GitHub Actions runner environment."""
        return os.getenv("GITHUB_ACTIONS") == "true"

    def get_summary_markdown(self) -> str:
        """Generates a detailed summary of the agent run in Markdown format."""
        emoji = "✅" if self.status == "completed" else "❌"
        md = []
        md.append(f"# {emoji} APEX Agent Execution Summary: {self.name}")
        md.append("")
        md.append("## 📊 Telemetry")
        md.append("| Metric | Value |")
        md.append("|---|---|")
        md.append(f"| **Status** | {self.status.upper()} |")
        md.append(f"| **Duration** | {self.duration} seconds |")
        md.append(f"| **Est. Input Tokens** | {self.input_tokens_estimated:,} |")
        md.append(f"| **Est. Output Tokens** | {self.output_tokens_estimated:,} |")
        md.append(f"| **Est. Cost (USD)** | ${self.estimated_cost:.6f} |")
        md.append("")

        md.append("## 🧠 Reasoning & Execution Log")
        md.append("| Step | Action | Result | Status |")
        md.append("|---|---|---|---|")
        for step in self.steps:
            step_emoji = "🟢" if step["status"] == "success" else "🔴"
            # Format multi-line results for table
            res = step["result"].replace("\n", "<br>")
            md.append(f"| {step['index']} | {step['action']} | {res} | {step_emoji} {step['status']} |")
        md.append("")

        if self.errors:
            md.append("## ⚠️ Errors Encountered")
            for err in self.errors:
                md.append(f"- {err}")
            md.append("")

        return "\n".join(md)

    def write_github_step_summary(self):
        """Writes the Markdown summary report directly to the Job Summary page."""
        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_path:
            try:
                with open(summary_path, "a", encoding="utf-8") as f:
                    f.write("\n" + self.get_summary_markdown() + "\n")
            except Exception as e:
                print(f"Warning: Failed to write to GITHUB_STEP_SUMMARY: {e}")

    def write_github_outputs(self):
        """Writes output values to the GITHUB_OUTPUT environment file."""
        output_path = os.getenv("GITHUB_OUTPUT")
        if output_path:
            try:
                outputs = {
                    "agent_status": self.status,
                    "duration_seconds": str(self.duration),
                    "input_tokens": str(self.input_tokens_estimated),
                    "output_tokens": str(self.output_tokens_estimated),
                    "execution_cost": f"{self.estimated_cost:.6f}",
                }
                with open(output_path, "a", encoding="utf-8") as f:
                    for key, val in outputs.items():
                        f.write(f"{key}={val}\n")
            except Exception as e:
                print(f"Warning: Failed to write to GITHUB_OUTPUT: {e}")
