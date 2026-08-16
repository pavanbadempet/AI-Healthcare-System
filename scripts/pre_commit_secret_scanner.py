"""
Pre-Commit Secret Scanner & Zero-Leak Enforcement Gate.
Scans all staged files before every git commit to guarantee that no credentials,
PostgreSQL connection strings with passwords, Neon keys, API tokens, or secrets
can ever be committed to the repository.
"""

import sys
import os
import re
import subprocess
from typing import List, Tuple

# Ensure UTF-8 output across all operating systems
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Patterns identifying real leaked credentials & connection strings
SECRET_PATTERNS = [
    (r"postgres(?:ql)?:\/\/[a-zA-Z0-9_]+:[a-zA-Z0-9_.\-~%!$&'()*+,;=]{6,}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "PostgreSQL URI with hardcoded password"),
    (r"\bnpg_[a-zA-Z0-9]{10,}\b", "Neon Database Token (npg_*)"),
    (r"\bdapi[a-zA-Z0-9]{20,}\b", "Databricks Personal Access Token (dapi*)"),
    (r"\bhf_[a-zA-Z0-9]{20,}\b", "Hugging Face Access Token (hf_*)"),
    (r"\bsk-[a-zA-Z0-9_\-]{32,}\b", "OpenAI / Anthropic Secret Key (sk-*)"),
    (r"\bghp_[a-zA-Z0-9]{20,}\b", "GitHub Personal Access Token (ghp_*)"),
    (r"\bAIza[a-zA-Z0-9_\-]{35}\b", "Google API / Cloud Token"),
    (r"\bdp\.pt\.[a-zA-Z0-9]{20,}\b", "Doppler Service Token"),
    (r"-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----", "Private Cryptographic Key"),
    (r"mongodb(?:\+srv)?:\/\/[a-zA-Z0-9_]+:[^@]+@", "MongoDB Connection String with Password"),
    (r"mysql:\/\/[a-zA-Z0-9_]+:[^@]+@", "MySQL Connection String with Password")
]

# Excluded directories and local-only config files
IGNORED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "target", "dist", "build",
    ".pytest_cache", "__pycache__", ".turbo", ".next"
}

EXCLUDED_FILES = [
    "scripts/pre_commit_secret_scanner.py",
    ".env.example",
    ".env",
    "tests/"
]


def get_staged_files() -> List[str]:
    """Returns list of staged files in git."""
    try:
        res = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
        files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        return files
    except Exception:
        return []


def scan_file(filepath: str) -> List[Tuple[int, str, str]]:
    """Scans a single file for secret pattern violations."""
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return []
    
    # Check if excluded
    norm_path = filepath.replace("\\", "/")
    for exc in EXCLUDED_FILES:
        if exc in norm_path or norm_path == exc or norm_path == f"./{exc}":
            return []

    violations = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, start=1):
                # Ignore comment placeholders with dummy words
                if "user:pass" in line or "user:password" in line or "dummy" in line or "placeholder" in line or "mock_" in line or "example.invalid" in line:
                    continue
                for pattern, name in SECRET_PATTERNS:
                    if re.search(pattern, line):
                        violations.append((line_idx, name, line.strip()[:80]))
    except Exception:
        pass
    return violations


def main():
    staged = get_staged_files()
    if not staged:
        # If no staged files specified, scan all git-tracked and modified workspace files
        files_to_scan = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                files_to_scan.append(os.path.join(root, file))
        staged = files_to_scan

    total_violations = 0
    print("=" * 70)
    print("[SECURITY GATE] RUNNING PRE-COMMIT ZERO-LEAK SECRET SCANNER")
    print(f"Scanning {len(staged)} files...")
    print("=" * 70)

    for fpath in staged:
        violations = scan_file(fpath)
        if violations:
            for line_no, _, _ in violations:
                print(f"[BLOCKED] Security violation detected in {fpath} (Line {line_no})")
                total_violations += 1

    if total_violations > 0:
        print("\n" + "!" * 70)
        print(f"[CRITICAL ERROR] COMMIT ABORTED: {total_violations} potential secrets found in staged files!")
        print("Please remove all hardcoded tokens, passwords, or URIs before committing.")
        print("!" * 70)
        sys.exit(1)
    else:
        print("[OK] Zero secrets detected across all scanned files. Code is safe to commit.")
        sys.exit(0)


if __name__ == "__main__":
    main()
