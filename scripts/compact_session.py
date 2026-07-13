#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"

def find_active_transcript(cid=None):
    if cid:
        transcript_path = BRAIN_DIR / cid / ".system_generated" / "logs" / "transcript.jsonl"
        if transcript_path.exists():
            return transcript_path
        print(f"Error: Specified conversation transcript not found at: {transcript_path}")
        return None

    # Find the most recently modified transcript.jsonl
    latest_time = 0
    latest_path = None

    if not BRAIN_DIR.exists():
        print(f"Error: Antigravity app data folder not found at: {BRAIN_DIR}")
        return None

    for item in BRAIN_DIR.iterdir():
        if item.is_dir():
            t_path = item / ".system_generated" / "logs" / "transcript.jsonl"
            if t_path.exists():
                mtime = t_path.stat().st_mtime
                if mtime > latest_time:
                    latest_time = mtime
                    latest_path = t_path

    return latest_path

def parse_transcript(transcript_path):
    modified_files = set()
    user_inputs = []
    failed_commands = []

    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                step = json.loads(line)
            except Exception:
                continue

            step_type = step.get("type")
            source = step.get("source")

            # Extract User Queries
            if step_type == "USER_INPUT" and source == "USER_EXPLICIT":
                content = step.get("content", "")
                if content:
                    # Clean up user request tags
                    cleaned = content.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
                    if cleaned and cleaned.lower() != "continue":
                        user_inputs.append(cleaned)

            # Extract File Modifications from tool calls
            tool_calls = step.get("tool_calls", [])
            if not tool_calls and "tool_calls" in step.get("content", ""):
                # Sometimes stored in content string
                try:
                    tool_calls = json.loads(step.get("content")).get("tool_calls", [])
                except Exception:
                    pass

            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("name")
                    args = tc.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            pass

                    if name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                        target_file = args.get("TargetFile")
                        if target_file:
                            # Normalize path
                            norm_path = Path(target_file).resolve()
                            try:
                                # Try to display path relative to GitHub if possible
                                if "GitHub" in str(norm_path):
                                    relative = norm_path.relative_to(Path(os.getcwd()).parent)
                                    modified_files.add(f"file:///{relative.as_posix()}")
                                else:
                                    modified_files.add(f"file:///{norm_path.as_posix()}")
                            except Exception:
                                modified_files.add(f"file:///{norm_path.as_posix()}")

            # Check for failed terminal commands
            if step_type == "RUN_COMMAND" and step.get("status") == "ERROR":
                cmd = step.get("command", "")
                failed_commands.append(cmd)

    return {
        "modified_files": sorted(list(modified_files)),
        "user_inputs": user_inputs,
        "failed_commands": failed_commands
    }

def generate_handoff_prompt(cid, data):
    print("=" * 70)
    print("  RECOMMENDED HANDOFF PROMPT (Copy the text below for your next session)")
    print("=" * 70)
    print()

    prompt = []
    prompt.append("# Session Handoff Context")
    prompt.append(f"Resume context from prior session: `{cid}`.")
    prompt.append("")

    prompt.append("## Files Modified")
    if data["modified_files"]:
        for f in data["modified_files"]:
            prompt.append(f"- [{Path(f).name}]({f})")
    else:
        prompt.append("- None detected.")
    prompt.append("")

    prompt.append("## Tasks Accomplished")
    recent_goals = data["user_inputs"][-5:] if data["user_inputs"] else []
    if recent_goals:
        for goal in recent_goals:
            prompt.append(f"- Completed: {goal}")
    else:
        prompt.append("- Initial setup and alignment tasks completed.")
    prompt.append("")

    prompt.append("## Active Errors / Failures")
    if data["failed_commands"]:
        for cmd in data["failed_commands"][-3:]:
            prompt.append(f"- Blocked command: `{cmd}`")
    else:
        prompt.append("- None. System builds and runs correctly.")
    prompt.append("")

    prompt.append("## Next Steps")
    prompt.append("- Verify the modified files are in active use.")
    prompt.append("- Continue addressing follow-up requirements.")

    full_prompt = "\n".join(prompt)
    print(full_prompt)
    print()
    print("=" * 70)

    # Calculate estimated tokens saved
    # The active conversation system prompt + skills is about 80k tokens.
    # With N turns, this compacter resets N turns of history (approx 20k-200k tokens).
    print("\n[TIP] Start a fresh session with the prompt above to reset active token overhead back to ZERO.")
    return full_prompt

def main():
    parser = argparse.ArgumentParser(description="Parse active transcript to generate a session handoff compacter.")
    parser.add_argument("--cid", help="Specify conversation ID directly")
    args = parser.parse_args()

    transcript_path = find_active_transcript(args.cid)
    if not transcript_path:
        return 1

    cid = transcript_path.parent.parent.name
    print(f"Reading active session transcript: {cid}")

    data = parse_transcript(transcript_path)
    prompt_content = generate_handoff_prompt(cid, data)

    handoff_file = ROOT / "active_handoff.md"
    try:
        handoff_file.write_text(prompt_content, encoding="utf-8")
        print("\n[SAVED] Handoff context successfully written to: active_handoff.md")
    except Exception as e:
        print(f"\n[WARNING] Could not write active_handoff.md: {e}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
