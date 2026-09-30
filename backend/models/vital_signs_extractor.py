"""
Streaming HL7 v2.x ORU^R01 vital signs telemetry parser.
"""
from typing import Dict, Optional

class VitalSignsTelemetryParser:
    """Parses numeric telemetry observations (heart rate, SpO2, systolic BP) from HL7 segments."""

    @staticmethod
    def parse_obx_segment(segment: str) -> Optional[Dict[str, float]]:
        fields = segment.split("|")
        if len(fields) > 5 and fields[0] == "OBX":
            code = fields[3]
            try:
                val = float(fields[5])
                return {"vital_code": code, "value": val}
            except ValueError:
                return None
        return None
