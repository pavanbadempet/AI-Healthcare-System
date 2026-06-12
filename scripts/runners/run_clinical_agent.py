import argparse
import asyncio
import os
import sys
import time
from datetime import datetime, timezone

# Add the project root to python path to resolve backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database import SessionLocal
from backend.agents.clinical_audit_agent import ClinicalAuditAgent


async def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="APEX Clinical Audit Agent CLI Runner")
    parser.add_argument("--hours", type=int, default=24, help="Scope of recent data to audit (in hours)")
    parser.add_argument("--dry-run", action="store_true", help="Run in mock/dry-run mode without external AI queries")
    parser.add_argument("--output-dir", type=str, default="output/clinical_audits", help="Output directory for reports")
    args = parser.parse_args()

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Clinical Audit Agent...")
    print(f"Params: hours={args.hours}, dry_run={args.dry_run}, output_dir={args.output_dir}")

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize DB session
    db = SessionLocal()
    try:
        agent = ClinicalAuditAgent(db, name="Clinical Deterioration Audit Agent")
        
        # Run agent
        report_md = await agent.run(hours=args.hours, dry_run=args.dry_run)
        
        # Save output report
        timestamp = int(time.time())
        report_file_name = f"clinical_audit_report_{timestamp}.md"
        report_path = os.path.join(args.output_dir, report_file_name)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"Success: Clinical audit report written to: {report_path}")

        # Also write a fixed path report for GHA or downstream scripts to find easily
        latest_path = os.path.join(args.output_dir, "latest_clinical_audit.md")
        with open(latest_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"Success: Latest clinical audit link updated at: {latest_path}")

        # Print reasoning telemetry summary
        print("\n" + "=" * 40 + "\n")
        print(agent.get_summary_markdown())
        print("\n" + "=" * 40 + "\n")
        
    except Exception as e:
        print(f"Fatal error during agent execution: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
