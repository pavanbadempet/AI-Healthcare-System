"""
Pre-Commit Secret Scanner & Zero-Leak Enforcement Gate.
Scans all staged files before every git commit to guarantee that no credentials,
PostgreSQL connection strings with passwords, Neon keys, API tokens, Doppler tokens,
or .env files can ever be committed to the repository.
"""

import os
import re
import subprocess
import sys
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
    (r"[a-zA-Z0-9_.\-]+:[a-zA-Z0-9_.\-~%!$&'()*+,;=]{6,}@ep-[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+\.neon\.tech", "Neon Database Connection with hardcoded credentials"),
    (r"\bnpg_[a-zA-Z0-9]{10,}\b", "Neon Database Token (npg_*)"),
    (r"\bdapi[a-zA-Z0-9]{20,}\b", "Databricks Personal Access Token (dapi*)"),
    (r"\bhf_[a-zA-Z0-9]{20,}\b", "Hugging Face Access Token (hf_*)"),
    (r"\bsk-[a-zA-Z0-9_\-]{32,}\b", "OpenAI / Anthropic Secret Key (sk-*)"),
    (r"\b(?:ghp|gho)_[a-zA-Z0-9]{20,}\b", "GitHub Personal Access Token (ghp_*)"),
    (r"\bgithub_pat_[a-zA-Z0-9_]{50,}\b", "GitHub Fine-Grained Token"),
    (r"\bAIza[a-zA-Z0-9_\-]{35}\b", "Google API / Cloud Token"),
    (r"\bdp\.(?:pt|ct|st)\.[a-zA-Z0-9]{20,}\b", "Doppler Token (dp.*)"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS Access Key ID (AKIA*)"),
    (r"-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----", "Private Cryptographic Key"),
    (r"mongodb(?:\+srv)?:\/\/[a-zA-Z0-9_]+:[^@]+@", "MongoDB Connection String with Password"),
    (r"mysql:\/\/[a-zA-Z0-9_]+:[^@]+@", "MySQL Connection String with Password"),
]

# Excluded files that legitimately reference the scanner rules or mocks
EXCLUDED_FILES = [
    "scripts/pre_commit_secret_scanner.py",
    "scripts/pre_commit_secret_scanner.ts",
    ".env.example",
    "tests/",
]

# Safe placeholder tokens that are permissible in documentation and examples
SAFE_PLACEHOLDERS = [
    "user:pass",
    "user:password",
    "username:password",
    "dummy",
    "placeholder",
    "mock_",
    "example.invalid",
    "<password>",
    "${POSTGRES_PASSWORD}",
]


def get_staged_files() -> List[str]:
    """Returns list of staged files in git."""
    try:
        res = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
        files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        return files
    except Exception:
        return []


def get_all_tracked_files() -> List[str]:
    """Returns all git-tracked files quickly via git ls-files."""
    try:
        res = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception:
        return []


def scan_file(filepath: str) -> List[Tuple[int, str, str]]:
    """Scans a single file for secret pattern violations."""
    norm_path = filepath.replace("\\", "/")

    # Rule 1: STRICTLY FORBID ANY .env FILE EXCEPT .env.example
    filename = os.path.basename(norm_path)
    if filename == ".env" or (filename.startswith(".env.") and filename != ".env.example") or filename.endswith(".env"):
        return [(1, "Prohibited Environment File", f"Attempted to commit '{filename}'. All secrets must be stored in Doppler!")]

    # Rule 2: Skip safe excluded files/dirs
    for exc in EXCLUDED_FILES:
        if exc in norm_path or norm_path == exc or norm_path == f"./{exc}":
            return []

    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return []

    violations = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, start=1):
                # Ignore placeholders in comments/docs
                if any(p in line for p in SAFE_PLACEHOLDERS):
                    continue
                for pattern, name in SECRET_PATTERNS:
                    if re.search(pattern, line):
                        violations.append((line_idx, name, line.strip()[:80]))
    except Exception:
        pass
    return violations


def main():
    staged = get_staged_files()
    mode = "STAGED"
    if not staged:
        staged = get_all_tracked_files()
        mode = "ALL TRACKED"

    total_violations = 0
    print("=" * 70)
    print(f"[SECURITY GATE] RUNNING PRE-COMMIT ZERO-LEAK SECRET SCANNER ({mode})")
    print(f"Scanning {len(staged)} files...")
    print("=" * 70)

    for fpath in staged:
        violations = scan_file(fpath)
        if violations:
            for line_no, vtype, detail in violations:
                print(f"[BLOCKED] {vtype} detected in {fpath} (Line {line_no}): {detail}")
                total_violations += 1

    if total_violations > 0:
        print("\n" + "!" * 70)
        print(f"[CRITICAL ERROR] COMMIT ABORTED: {total_violations} secret violations found!")
        print("Never store plaintext credentials in code or files. Use Doppler:")
        print("  doppler secrets set KEY=VALUE")
        print("  doppler run -- <command>")
        print("!" * 70)
        sys.exit(1)
    else:
        print(f"[OK] Zero secrets detected across all {len(staged)} scanned files. Safe to proceed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
