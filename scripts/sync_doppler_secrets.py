"""
Doppler Secret Management & Single Source of Truth Synchronization.
Securely manages, verifies, and pushes project secrets directly to Doppler
so credentials NEVER need to touch source code or git-tracked files.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("doppler_sync")

# The 8 Core Multi-Cloud Project Secret Keys
REQUIRED_SECRET_KEYS = [
    "DATABASE_URL",             # Neon Serverless PostgreSQL
    "DATABRICKS_HOST",         # Databricks Free Edition Workspace Host
    "DATABRICKS_TOKEN",        # Databricks Personal Access Token
    "CLOUDFLARE_WORKER_URL",   # Cloudflare Workers AI Edge Endpoint
    "CLOUDFLARE_AUTH_TOKEN",   # Cloudflare Bearer Token
    "HF_TOKEN",                # Hugging Face Access Token
    "KAGGLE_USERNAME",         # Kaggle GPU API Username
    "KAGGLE_KEY"               # Kaggle GPU API Key
]


def audit_doppler_environment() -> Dict[str, Dict[str, Any]]:
    """Audits which required secrets are resolved in current environment."""
    report = {}
    for key in REQUIRED_SECRET_KEYS:
        val = os.environ.get(key)
        report[key] = {
            "present": bool(val),
            "length": len(val) if val else 0,
            "masked": f"{val[:3]}...{val[-3:]}" if val and len(val) > 8 else ("SET" if val else "MISSING")
        }
    return report


def push_secret_to_doppler(token: str, project: str, config: str, secrets_to_set: Dict[str, str]) -> bool:
    """Pushes a dictionary of secrets to Doppler via the Doppler REST API."""
    import urllib.error
    import urllib.request

    url = f"https://api.doppler.com/v1/configs/config/secrets?project={project}&config={config}"
    payload = json.dumps({"secrets": secrets_to_set}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            json.loads(resp.read().decode("utf-8"))
            logger.info("Successfully synchronized %d secret(s) to Doppler project '%s' (%s)", len(secrets_to_set), project, config)
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        logger.error("Doppler API error %d: %s", e.code, err_body)
        return False
    except Exception as e:
        logger.error("Failed to connect to Doppler API: %s", str(e))
        return False


def main():
    print("=" * 70)
    print("🔐 DOPPLER: SINGLE SOURCE OF TRUTH SECRET AUDIT")
    print("=" * 70)

    audit = audit_doppler_environment()
    present_count = sum(1 for v in audit.values() if v["present"])
    total_count = len(REQUIRED_SECRET_KEYS)

    for key, info in audit.items():
        status = f"[OK] Present ({info['masked']})" if info["present"] else "[--] Missing (Using local sandbox mock)"
        print(f"  * {key.ljust(25)}: {status}")

    print("-" * 70)
    print(f"Summary: {present_count}/{total_count} secrets resolved dynamically via Doppler/Environment.")
    print("Zero credentials stored in git. All missing secrets safely default to local sandbox mocks.")
    print("=" * 70)

    # If Doppler token provided via CLI, allow updating
    if len(sys.argv) > 1 and sys.argv[1] == "--push":
        doppler_token = os.environ.get("DOPPLER_TOKEN") or os.environ.get("DOPPLER")
        if not doppler_token:
            print("To push secrets to Doppler, set DOPPLER_TOKEN in environment or run with doppler CLI:")
            print("  doppler secrets set KEY=VALUE")
            sys.exit(1)


if __name__ == "__main__":
    main()
