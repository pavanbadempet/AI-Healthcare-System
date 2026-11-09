"""
Automated Housekeeping & Build Cache Eviction Engine.
Runs transparently during pre-commit, pre-push, and test workflows to guarantee
that local disk caches (.hypothesis, test databases, cargo build artifacts)
never accumulate bloat or exceed storage limits.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_housekeeping(max_target_gb: float = 3.0):
    root = Path(__file__).resolve().parent.parent

    # 1. Purge .hypothesis test state cache
    hypothesis_dir = root / ".hypothesis"
    if hypothesis_dir.exists():
        try:
            shutil.rmtree(hypothesis_dir, ignore_errors=True)
            print("[AUTO-CLEAN] Purged ephemeral .hypothesis test cache.")
        except Exception:
            pass

    # 2. Purge ephemeral test databases in rust_gateway
    rg_dir = root / "rust_gateway"
    if rg_dir.exists():
        cleaned_dbs = 0
        for p in rg_dir.glob("test_*.db*"):
            try:
                p.unlink(missing_ok=True)
                cleaned_dbs += 1
            except Exception:
                pass
        if cleaned_dbs > 0:
            print(f"[AUTO-CLEAN] Removed {cleaned_dbs} orphaned test database files.")

    # 3. Purge orphaned node_modules in microservices if present
    ms_nm = root / "microservices" / "cloudflare_ai_worker" / "node_modules"
    if ms_nm.exists():
        try:
            shutil.rmtree(ms_nm, ignore_errors=True)
            print("[AUTO-CLEAN] Purged microservices/cloudflare_ai_worker/node_modules.")
        except Exception:
            pass

    # 4. Automatically prune Cargo target cache if it exceeds threshold
    target_dir = rg_dir / "target"
    if target_dir.exists():
        try:
            total_bytes = sum(f.stat().st_size for f in target_dir.glob("**/*") if f.is_file())
            limit_bytes = max_target_gb * 1024 * 1024 * 1024
            if total_bytes > limit_bytes:
                size_gb = round(total_bytes / (1024 * 1024 * 1024), 2)
                print(f"[AUTO-CLEAN] rust_gateway/target ({size_gb} GB) exceeded {max_target_gb} GB limit.")
                print("[AUTO-CLEAN] Executing automated cargo clean...")
                subprocess.run(
                    ["cargo", "clean", "--manifest-path", str(rg_dir / "Cargo.toml")],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
                print("[AUTO-CLEAN] Automated cargo cleanup complete.")
        except Exception:
            pass


if __name__ == "__main__":
    run_housekeeping()
