#!/usr/bin/env python3
import re
import subprocess
import sys


def run_pytest(args):
    # Default to running tests/ if no arguments provided
    pytest_args = [sys.executable, "-m", "pytest"] + (args if args else ["tests/"])

    print(f"Running command: {' '.join(pytest_args)}")
    print("Filtering test output to save tokens...")
    print("-" * 60)

    process = subprocess.Popen(
        pytest_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    in_failure_block = False
    current_failure = []
    failures = []
    summary_line = ""
    passed_count = 0
    failed_count = 0

    # Simple regex to identify passed/failed indicators
    passed_pattern = re.compile(r"PASSED\s*$|\[\s*\d+%\s*\]\s*.*PASSED")
    failed_indicator = re.compile(r"FAILED\s*$|\[\s*\d+%\s*\]\s*.*FAILED")

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break

        line_str = line.strip()
        output_lines.append(line)

        # Check for passing test lines (we suppress these)
        if passed_pattern.search(line_str):
            passed_count += 1
            continue

        # Check for failing test indicators
        if failed_indicator.search(line_str):
            failed_count += 1
            print(f"❌ {line_str}")
            continue

        # Check for start of failure tracebacks/blocks
        if line_str.startswith("____") and line_str.endswith("____"):
            in_failure_block = True
            if current_failure:
                failures.append(current_failure)
                current_failure = []
            current_failure.append(line)
            continue

        # Check for end of failure tracebacks/blocks (often marked by empty lines or start of summary)
        if in_failure_block:
            if line_str.startswith("===") and ("failed" in line_str or "passed" in line_str):
                in_failure_block = False
                failures.append(current_failure)
                current_failure = []
                summary_line = line
            else:
                current_failure.append(line)
            continue

        # Capture the final summary line
        if line_str.startswith("===") and ("failed" in line_str or "passed" in line_str or "error" in line_str):
            summary_line = line

    # If process exited but we still have a failure block
    if current_failure:
        failures.append(current_failure)

    # Print compressed failures
    if failures:
        print("\n--- FAILING TEST DETAILS (COMPRESSED) ---")
        for i, fail_lines in enumerate(failures):
            print(f"\n[Failure #{i+1}]")
            # Print the header line (e.g. ____ test_name ____)
            print(fail_lines[0].strip())

            # Extract key lines: the source code line and the assertion error
            src_lines = []
            assert_lines = []

            for f_line in fail_lines[1:]:
                f_line_str = f_line.strip()
                # If it's a file path line (e.g. tests/test_file.py:23)
                if re.match(r"^[a-zA-Z0-9_\-\./]+\.py:\d+:", f_line_str):
                    src_lines.append(f_line)
                elif f_line_str.startswith(">"):
                    src_lines.append(f_line)
                elif "AssertionError" in f_line_str or f_line_str.startswith("E "):
                    assert_lines.append(f_line)

            # Print last 5 code context lines
            if src_lines:
                print("Code Context:")
                for line in src_lines[-5:]:
                    print(f"  {line.rstrip()}")

            # Print assertion details
            if assert_lines:
                print("Assertion details:")
                for line in assert_lines:
                    print(f"  {line.rstrip()}")
        print("-" * 60)

    # Print high-level metrics
    print(f"\nResults: {passed_count} passed, {failed_count} failed.")
    if summary_line:
        print(summary_line.strip())

    return process.returncode

if __name__ == "__main__":
    sys.exit(run_pytest(sys.argv[1:]))
