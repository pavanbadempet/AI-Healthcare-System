"""
Test Results Reporter and Metrics Aggregator for E2E Test Suite.
Tracks execution times, pass/fail counts, domain breakdowns, and writes JSON/Markdown summaries.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TestResult:
    name: str
    tier: str
    domain: str
    status: str  # "PASS", "FAIL", "SKIP", "ERROR"
    duration_ms: float = 0.0
    status_code: Optional[int] = None
    error: Optional[str] = None


@dataclass
class TestRunSummary:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0
    tier_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    domain_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    results: List[TestResult] = field(default_factory=list)


class TestReporter:
    """Collects test results and formats human-readable and machine-readable reports."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.perf_counter()

    def record(
        self,
        name: str,
        tier: str,
        domain: str,
        status: str,
        duration_ms: float = 0.0,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
    ):
        self.results.append(
            TestResult(
                name=name,
                tier=tier,
                domain=domain,
                status=status.upper(),
                duration_ms=round(duration_ms, 2),
                status_code=status_code,
                error=error,
            )
        )

    def summarize(self) -> TestRunSummary:
        summary = TestRunSummary(
            total=len(self.results),
            total_duration_ms=round((time.perf_counter() - self.start_time) * 1000.0, 2),
            results=self.results,
        )

        for r in self.results:
            st = r.status.upper()
            if r.tier not in summary.tier_counts:
                summary.tier_counts[r.tier] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
            summary.tier_counts[r.tier]["total"] += 1

            if r.domain not in summary.domain_counts:
                summary.domain_counts[r.domain] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
            summary.domain_counts[r.domain]["total"] += 1

            if st == "PASS":
                summary.passed += 1
                summary.tier_counts[r.tier]["passed"] += 1
                summary.domain_counts[r.domain]["passed"] += 1
            elif st == "FAIL":
                summary.failed += 1
                summary.tier_counts[r.tier]["failed"] += 1
                summary.domain_counts[r.domain]["failed"] += 1
            elif st == "SKIP":
                summary.skipped += 1
                summary.tier_counts[r.tier]["skipped"] += 1
                summary.domain_counts[r.domain]["skipped"] += 1
            else:
                summary.errors += 1
                summary.tier_counts[r.tier]["errors"] += 1
                summary.domain_counts[r.domain]["errors"] += 1

        return summary

    def print_summary(self):
        summary = self.summarize()
        print("\n" + "=" * 80)
        print("  AI HEALTHCARE SYSTEM - E2E TEST SUITE EXECUTION SUMMARY")
        print("=" * 80)
        print(f" Total Tests Run : {summary.total}")
        print(f" Passed          : {summary.passed}")
        print(f" Failed          : {summary.failed}")
        print(f" Errors          : {summary.errors}")
        print(f" Skipped         : {summary.skipped}")
        print(f" Total Duration  : {summary.total_duration_ms:.2f} ms ({summary.total_duration_ms / 1000.0:.2f} s)")
        print("-" * 80)
        print("  TIER BREAKDOWN")
        print("-" * 80)
        for tier, counts in sorted(summary.tier_counts.items()):
            print(f"  [{tier.upper()}] Total: {counts['total']:<4} Passed: {counts['passed']:<4} Failed: {counts['failed']:<4} Errors: {counts['errors']:<4}")

        print("=" * 80 + "\n")

    def save_json(self, output_path: str):
        summary = self.summarize()
        data = {
            "summary": {
                "total": summary.total,
                "passed": summary.passed,
                "failed": summary.failed,
                "errors": summary.errors,
                "skipped": summary.skipped,
                "total_duration_ms": summary.total_duration_ms,
            },
            "tier_counts": summary.tier_counts,
            "domain_counts": summary.domain_counts,
            "results": [asdict(r) for r in summary.results],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
