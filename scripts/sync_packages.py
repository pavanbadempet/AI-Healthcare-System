"""Developer utility to sync and push package changes to standalone private repositories.

Uses git subtree push to extract directory histories and push them to remote repositories.
"""

import os
import subprocess
import sys

# Target repositories configuration
PACKAGES = {
    "fastapi-license-gate": {
        "path": "packages/fastapi-license-gate",
        "url": "https://github.com/pavanbadempet/fastapi-license-gate.git",
    },
    "clinical-tabular": {
        "path": "packages/clinical-tabular",
        "url": "https://github.com/pavanbadempet/clinical-tabular.git",
    },
}


def run_command(command_list, cwd=None):
    """Utility to execute shell commands."""
    try:
        # Clear GITHUB_TOKEN if it is set and invalid
        env = os.environ.copy()
        if "GITHUB_TOKEN" in env and not env["GITHUB_TOKEN"].startswith("gho_"):
            env["GITHUB_TOKEN"] = ""

        result = subprocess.run(command_list, cwd=cwd, text=True, capture_output=True, check=True, env=env)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command_list)}:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return False


def main():
    print("=== Starting Package Standalone Sync ===")

    # Ensure git is clean before subtree push (subtree push requires a clean state or committed changes)
    status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if status_res.stdout.strip():
        print("WARNING: You have uncommitted changes in your main repository.")
        print("Subtree sync only pushes committed changes. Please commit your changes first.")
        print("-" * 50)

    success = True
    for name, config in PACKAGES.items():
        print(f"\nSyncing '{name}' ({config['path']}) to remote...")

        # Split the subtree to get the split commit SHA
        try:
            env = os.environ.copy()
            if "GITHUB_TOKEN" in env and not env["GITHUB_TOKEN"].startswith("gho_"):
                env["GITHUB_TOKEN"] = ""

            split_res = subprocess.run(
                ["git", "subtree", "split", f"--prefix={config['path']}"],
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            split_sha = split_res.stdout.strip()
            if not split_sha:
                print(f"[FAIL] Failed to get subtree split SHA for '{name}'")
                success = False
                continue

            print(f"Subtree split SHA: {split_sha}")
            # Force push the split commit directly to the remote repository
            push_cmd = ["git", "push", config["url"], f"{split_sha}:main", "--force"]
            if run_command(push_cmd):
                print(f"[OK] Successfully synced '{name}' via force push!")
            else:
                print(f"[FAIL] Failed to push '{name}' to remote.")
                success = False
        except Exception as e:
            print(f"[FAIL] Error syncing '{name}': {e}")
            success = False

    print("\n=== Sync Process Finished ===")
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
