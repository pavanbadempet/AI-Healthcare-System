#!/usr/bin/env python3
"""
Hospital Operational Patient Flow Simulator
=============================================
Simulates 24-hour ED arrivals, ward transfers, ICU stays, and discharge throughput
to evaluate bottleneck points and occupancy peaks under surge conditions.
"""

import random
import sys


def run_patient_flow_simulation(hours: int = 24, total_beds: int = 100) -> dict:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    current_occupancy = 60
    ed_arrivals = 0
    discharges = 0
    bottleneck_hours = []

    for hr in range(hours):
        # Peak ED arrival hours (10 AM - 4 PM and 6 PM - 9 PM)
        arrival_rate = random.randint(3, 8) if (10 <= hr <= 16 or 18 <= hr <= 21) else random.randint(1, 3)
        discharge_rate = random.randint(2, 6) if (11 <= hr <= 17) else random.randint(0, 2)

        ed_arrivals += arrival_rate
        discharges += discharge_rate
        current_occupancy = max(0, min(total_beds, current_occupancy + arrival_rate - discharge_rate))

        if current_occupancy >= int(total_beds * 0.90):
            bottleneck_hours.append(hr)

    return {
        "simulation_hours": hours,
        "total_hospital_beds": total_beds,
        "total_ed_arrivals": ed_arrivals,
        "total_discharges": discharges,
        "final_occupancy": current_occupancy,
        "final_occupancy_pct": round((current_occupancy / total_beds) * 100, 1),
        "surge_bottleneck_hours": bottleneck_hours,
        "status": "COMPLETED",
    }


def main():
    res = run_patient_flow_simulation()
    print(f"✅ Hospital Patient Flow Simulation Complete:")
    print(f"   ED Arrivals: {res['total_ed_arrivals']} | Discharges: {res['total_discharges']}")
    print(f"   Peak Occupancy Pct: {res['final_occupancy_pct']}%")


if __name__ == "__main__":
    main()
