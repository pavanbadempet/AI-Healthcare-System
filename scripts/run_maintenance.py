#!/usr/bin/env python
"""CLI Utility to run ClinOS system maintenance."""

import os
import sys

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_context
from backend.maintenance import run_system_maintenance

def main():
    print("Initializing system maintenance...")
    with get_db_context() as db:
        report = run_system_maintenance(db, executor_id=1)
        
    print("\n--- Maintenance Report ---")
    print(f"Status: {report['status']}")
    print(f"Primary DB optimized: {report['database_optimized']}")
    print(f"Vector DB optimized: {report['vector_store_optimized']}")
    print("Purged Records:")
    for dataset, count in report["purged_records"].items():
        print(f"  - {dataset}: {count} rows")
        
    if report["status"] == "success":
        print("\nMaintenance completed successfully.")
        sys.exit(0)
    else:
        print("\nMaintenance completed with issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
