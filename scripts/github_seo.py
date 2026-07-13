#!/usr/bin/env python3
"""
GitHub SEO Optimization Script
================================
Sets repository topics, description, and metadata for maximum
GitHub search visibility and trending potential.

Usage:
    python scripts/github_seo.py --token YOUR_GITHUB_TOKEN

Or set GITHUB_TOKEN env var:
    export GITHUB_TOKEN=ghp_...
    python scripts/github_seo.py
"""

import argparse
import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

OWNER = "pavanbadempet"
REPO = "AI-Healthcare-System"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

# ============================================================
# OPTIMIZED TOPICS (GitHub allows max 20)
# Strategy: Mix high-volume generic + long-tail specific terms
# ============================================================
TOPICS = [
    # High-volume (appear in GitHub Explore / Trending)
    "machine-learning",
    "data-engineering",
    "artificial-intelligence",
    "healthcare",
    "python",
    "fastapi",
    # Data Engineering / MLOps
    "pyspark",
    "apache-airflow",
    "delta-lake",
    "mlops",
    "lakehouse",
    "data-pipeline",
    # Specific / Niche
    "medical-ai",
    "clinical-decision-support",
    "langchain",
    "rag",
    "ollama",
    "xgboost",
    "shap",
    "hipaa",
]

# Optimized repo description (155 chars max for Google snippet)
DESCRIPTION = (
    "AI Data Engineering Healthcare Platform: PySpark Medallion Lakehouse, "
    "Airflow DAGs, 5 ML Models, Local LLM RAG, and FastAPI Clinical Architecture."
)

HOMEPAGE = ""  # Set to your live demo URL if you have one


def set_topics(token: str):
    """Set repository topics via GitHub API."""
    r = requests.put(
        f"{API}/topics",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.mercy-preview+json",
        },
        json={"names": TOPICS},
    )
    if r.status_code == 200:
        print(f"✅ Topics set ({len(TOPICS)}): {', '.join(TOPICS)}")
    else:
        print(f"❌ Topics failed: {r.status_code} {r.text}")
    return r.status_code == 200


def set_description(token: str):
    """Set repository description and homepage."""
    payload = {"description": DESCRIPTION}
    if HOMEPAGE:
        payload["homepage"] = HOMEPAGE
    r = requests.patch(
        API,
        headers={"Authorization": f"token {token}"},
        json=payload,
    )
    if r.status_code == 200:
        print(f"✅ Description set: {DESCRIPTION[:80]}...")
    else:
        print(f"❌ Description failed: {r.status_code} {r.text}")
    return r.status_code == 200


def check_current(token: str):
    """Show current repo metadata."""
    r = requests.get(API, headers={"Authorization": f"token {token}"})
    if r.status_code != 200:
        print(f"❌ Cannot access repo: {r.status_code}")
        return
    data = r.json()
    print("\n📊 Current State:")
    print(f"   Description: {data.get('description', 'NONE')}")
    print(f"   Homepage:    {data.get('homepage', 'NONE')}")
    print(f"   Stars:       {data.get('stargazers_count', 0)}")
    print(f"   Forks:       {data.get('forks_count', 0)}")
    print(f"   Topics:      {', '.join(data.get('topics', []))}")
    print(f"   Visibility:  {data.get('visibility', 'unknown')}")
    print()


def main():
    parser = argparse.ArgumentParser(description="GitHub SEO Optimizer")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--check", action="store_true", help="Check current state only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be set")
    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN")

    if args.dry_run:
        print("🔍 DRY RUN — Would set:")
        print(f"\n   Description: {DESCRIPTION}")
        print(f"\n   Topics ({len(TOPICS)}):")
        for i, t in enumerate(TOPICS, 1):
            print(f"     {i:2d}. {t}")
        return

    if not token:
        print("❌ No token. Use --token or set GITHUB_TOKEN env var.")
        print("   Create one at: https://github.com/settings/tokens")
        print("   Required scope: 'repo' (full control)")
        print("\n   Or run with --dry-run to preview changes.")
        sys.exit(1)

    check_current(token)

    if args.check:
        return

    print("🚀 Applying SEO optimizations...\n")
    set_topics(token)
    set_description(token)
    print("\n✅ Done! Changes take effect immediately on GitHub.")
    print("\n📝 MANUAL STEPS STILL NEEDED:")
    print("   1. Go to: https://github.com/pavanbadempet/AI-Healthcare-System/settings")
    print("   2. Scroll to 'Social preview' section")
    print("   3. Upload docs/assets/social-preview.svg (or convert to PNG first)")
    print("      → This image shows on Twitter/LinkedIn/Discord when your repo is shared")


if __name__ == "__main__":
    main()
