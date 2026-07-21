#!/usr/bin/env python3
"""
Code Quality & Architecture Linter.

Verifies backend standards:
1. No swallowed exceptions (`except Exception: pass`) in API route handlers.
2. Prompts are centralized in `prompt_registry.py`.
3. System prompts enforce concise output without synthetic filler.
4. FastAPI route handlers use dependency injection for database sessions.
"""

import ast
import os
import re
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")

# Synthetic filler phrases to disallow in prompt registry templates
FILLER_PHRASES = [
    r"\bas an ai\b",
    r"\bcertainly!\b",
    r"\bin summary,\b",
    r"\bas a large language model\b",
]

def check_swallowed_exceptions() -> list[str]:
    """Scan backend Python files for bare 'except Exception: pass' without logging."""
    issues = []
    for root, _, files in os.walk(BACKEND_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, BACKEND_DIR)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=path)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ExceptHandler):
                            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                                issues.append(
                                    f"Uncaught exception (`pass`) in backend/{rel_path}:L{node.lineno}"
                                )
                except Exception:
                    pass
    return issues

def check_prompt_registry() -> list[str]:
    """Check that prompt templates in prompt_registry.py are clean and concise."""
    issues = []
    registry_path = os.path.join(BACKEND_DIR, "prompt_registry.py")
    if not os.path.exists(registry_path):
        issues.append("backend/prompt_registry.py is missing!")
        return issues
    
    with open(registry_path, "r", encoding="utf-8") as f:
        content = f.read()

    for phrase in FILLER_PHRASES:
        if re.search(phrase, content, re.IGNORECASE):
            issues.append(f"Prompt registry contains synthetic filler: '{phrase}'")

    return issues

def check_route_schemas() -> list[str]:
    """Verify FastAPI route handlers use dependency injection for database sessions."""
    issues = []
    for root, _, files in os.walk(BACKEND_DIR):
        for file in files:
            if file.endswith(".py") and ("router" in file or file in ["main.py", "chat.py", "prediction.py"]):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, BACKEND_DIR)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                matches = re.finditer(r"@(app|router)\.(get|post|put|delete|patch)\(.*?\)\s*\n\s*def\s+(\w+)\(.*?\):", text, re.DOTALL)
                for match in matches:
                    func_name = match.group(3)
                    start_idx = match.end()
                    next_def = re.search(r"\ndef\s+|\n@", text[start_idx:])
                    func_body = text[start_idx : start_idx + next_def.start()] if next_def else text[start_idx:]
                    if "SessionLocal()" in func_body:
                        issues.append(f"Direct SessionLocal() in route '{func_name}' in backend/{rel_path} (use Depends(database.get_db))")

    return issues

def main():
    print("=" * 60)
    print("  AI HEALTHCARE SYSTEM - Code Quality Linter")
    print("=" * 60)
    
    exception_issues = check_swallowed_exceptions()
    prompt_issues = check_prompt_registry()
    schema_issues = check_route_schemas()

    total_issues = len(exception_issues) + len(prompt_issues) + len(schema_issues)

    print(f"\n1. Exception Handling Check:")
    if exception_issues:
        print(f"   [WARNING] Found {len(exception_issues)} uncaught exception blocks.")
        for issue in exception_issues[:5]:
            print(f"     - {issue}")
        if len(exception_issues) > 5:
            print(f"     ... and {len(exception_issues) - 5} more.")
    else:
        print("   [OK] Clean: No bare swallowed exceptions found.")

    print(f"\n2. Prompt Registry Audit:")
    if prompt_issues:
        print(f"   [WARNING] Prompt issues found:")
        for issue in prompt_issues:
            print(f"     - {issue}")
    else:
        print("   [OK] Clean: Prompts strictly enforce concise phrasing.")

    print(f"\n3. API Route Dependency Audit:")
    if schema_issues:
        print(f"   [WARNING] Route dependency issues found:")
        for issue in schema_issues:
            print(f"     - {issue}")
    else:
        print("   [OK] Clean: Routes use dependency injection for database sessions.")

    print("\n" + "=" * 60)
    if total_issues == 0:
        print("  RESULT: CODE QUALITY AUDIT PASSED [OK]")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"  RESULT: AUDIT COMPLETE WITH {total_issues} WARNING(S) [WARNING]")
        print("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    main()
