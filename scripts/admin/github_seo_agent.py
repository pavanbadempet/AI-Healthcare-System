#!/usr/bin/env python3
"""
GitHub Repository Metadata Sync
===============================
Runs on GitHub Actions (schedule + workflow_dispatch).
1. Ensures topic tags & meta-description are applied.
2. Checks open starter issues for contributors.
3. Keeps repository documentation metadata in sync.
"""

import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

OWNER = "pavanbadempet"
REPO = "AI-Healthcare-System"
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"

SEO_TOPICS = [
    "healthcare",
    "machine-learning",
    "fastapi",
    "medical-ai",
    "ollama",
    "apache-airflow",
    "pyspark",
    "clinical-decision-support",
    "hipaa",
    "mlops",
    "ehr",
    "fhir",
    "hospital-management",
    "langgraph",
    "react",
    "agent-framework",
    "clinical-intelligence",
    "hipaa-compliant",
    "hl7-fhir",
    "delta-lake",
]

OPTIMIZED_DESCRIPTION = (
    "AI Data Engineering Healthcare Platform: PySpark Medallion Lakehouse, "
    "Airflow DAGs, 5 ML Models, Local LLM RAG, and FastAPI Clinical Architecture."
)


def run_seo_audit(token: str):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Metadata-Sync",
    }

    print(f"Starting repository metadata sync for {OWNER}/{REPO}...")

    # 1. Update Repository Description & Homepage
    r_patch = requests.patch(API_URL, headers=headers, json={"description": OPTIMIZED_DESCRIPTION})
    if r_patch.status_code == 200:
        print("✅ Repository description verified & updated via REST API.")
    else:
        # Fallback to gh CLI subprocess
        import subprocess
        cmd = ["gh", "repo", "edit", f"{OWNER}/{REPO}", "--description", OPTIMIZED_DESCRIPTION]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ Repository description verified & updated via gh CLI.")
        else:
            print(f"⚠️ Description update status: {res.stderr.strip() or r_patch.text[:100]}")

    # 2. Update 20 High-Ranking GitHub Topics
    topics_url = f"{API_URL}/topics"
    headers_mercy = {**headers, "Accept": "application/vnd.github.mercy-preview+json"}
    r_topics = requests.put(topics_url, headers=headers_mercy, json={"names": SEO_TOPICS})
    if r_topics.status_code == 200:
        print(f"✅ Verified {len(SEO_TOPICS)} topic tags on GitHub via REST API.")
    else:
        # Fallback to gh CLI subprocess
        import subprocess
        topic_str = ",".join(SEO_TOPICS)
        cmd = ["gh", "repo", "edit", f"{OWNER}/{REPO}", "--add-topic", topic_str]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"✅ Verified {len(SEO_TOPICS)} topic tags on GitHub via gh CLI.")
        else:
            print(f"⚠️ Topics update status: {res.stderr.strip() or r_topics.text[:100]}")

    # 3. Audit open 'good first issue' contributor magnets
    issues_url = f"{API_URL}/issues?labels=good%20first%20issue&state=open"
    r_issues = requests.get(issues_url, headers=headers)
    if r_issues.status_code == 200:
        open_starter_issues = r_issues.json()
        print(f"📊 Active 'good first issue' starter tasks: {len(open_starter_issues)}")
        if len(open_starter_issues) < 2:
            print("💡 Recommendation: Consider adding starter issues for new contributors.")

    print("\nRepository metadata sync complete.")


def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN is required.")
        sys.exit(0)

    run_seo_audit(token)


if __name__ == "__main__":
    main()
