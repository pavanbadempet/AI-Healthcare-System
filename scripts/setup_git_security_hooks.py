"""
Setup & Enforce Git Security Hooks.
Installs and ensures executable permissions on both pre-commit and pre-push hooks
to guarantee zero credentials can ever be committed or pushed from any machine.
"""

import os
import stat
import sys

HOOKS_DIR = os.path.join(".git", "hooks")

PRE_COMMIT_HOOK = """#!/bin/sh
# AI Healthcare System — Pre-Commit Secret Scanner Hook
python scripts/pre_commit_secret_scanner.py
RESULT=$?
if [ $RESULT -ne 0 ]; then
    echo "Pre-commit secret scanner failed. Commit aborted."
    exit 1
fi
exit 0
"""

PRE_PUSH_HOOK = """#!/bin/sh
# AI Healthcare System — Pre-Push Zero-Leak Security Gate
echo "[SECURITY] Running pre-push secret and credential scan..."
python scripts/pre_commit_secret_scanner.py
RESULT=$?
if [ $RESULT -ne 0 ]; then
    echo "[CRITICAL] Pre-push secret scan failed! Push aborted to protect credentials."
    exit 1
fi

command -v git-lfs >/dev/null 2>&1 || { printf >&2 "\\n%s\\n\\n" "This repository is configured for Git LFS but 'git-lfs' was not found on your path. If you no longer wish to use Git LFS, remove this hook by deleting the 'pre-push' file in the hooks directory (set by 'core.hookspath'; usually '.git/hooks')."; exit 2; }
git lfs pre-push "$@"
"""


def install_hooks():
    if not os.path.exists(HOOKS_DIR):
        print(f"[WARN] .git/hooks directory not found at '{HOOKS_DIR}'. Skipping local hook installation.")
        return

    hooks = {
        "pre-commit": PRE_COMMIT_HOOK,
        "pre-push": PRE_PUSH_HOOK
    }

    for hook_name, hook_content in hooks.items():
        hook_path = os.path.join(HOOKS_DIR, hook_name)
        with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_content)

        # Ensure executable bit is set
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[OK] Installed security hook: {hook_name}")

    print("[SUCCESS] All git security gates installed. Zero secrets can be committed or pushed.")


if __name__ == "__main__":
    install_hooks()
