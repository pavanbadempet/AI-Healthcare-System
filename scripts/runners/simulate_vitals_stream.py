"""
Vital Signs Telemetry Simulator.

Generates continuous streaming vital observations (heart rate, blood pressure, SpO2, etc.)
for active patients in the hospital admissions table. Supports writing to a local directory
as JSON files (for file-stream Structured Streaming) or publishing to a Kafka topic.
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from backend.database import SessionLocal
from backend.models import Admission

DEFAULT_STREAM_DIR = os.path.join(BASE_DIR, "data", "telemetry_stream")
os.makedirs(DEFAULT_STREAM_DIR, exist_ok=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Simulate real-time vital observations for admitted patients.")
    parser.add_argument("--interval", type=float, default=5.0, help="Simulation interval in seconds (default: 5.0)")
    parser.add_argument("--output-dir", default=DEFAULT_STREAM_DIR, help="Directory to write streaming JSON files")
    parser.add_argument("--kafka", action="store_true", help="Publish directly to a Kafka broker")
    parser.add_argument("--kafka-servers", default="localhost:9092", help="Kafka bootstrap server address")
    parser.add_argument("--kafka-topic", default="hospital.vitals_stream", help="Kafka topic name")
    parser.add_argument("--anomaly-rate", type=float, default=0.08, help="Probability of vital sign anomaly (0.0 to 1.0)")
    parser.add_argument("--cleanup-minutes", type=int, default=5, help="Delete stream files older than N minutes to save disk space")
    return parser.parse_args()

def get_active_patients():
    """Query database for active admitted patients, or fall back to dummy data."""
    db = SessionLocal()
    try:
        active_admissions = (
            db.query(Admission)
            .filter(Admission.status == "active")
            .all()
        )
        if active_admissions:
            patients = []
            for adm in active_admissions:
                patients.append({
                    "patient_id": adm.patient_id,
                    "facility_id": adm.facility_id or 1,
                    "encounter_id": adm.encounter_id,
                    "department_id": adm.department_id or 1
                })
            print(f"Retrieved {len(patients)} active patients from admissions table.")
            return patients
    except Exception as e:
        print(f"Database query failed ({e}). Falling back to baseline seed patients.")
    finally:
        db.close()

    # Fallback seed data
    return [
        {"patient_id": 2, "facility_id": 1, "encounter_id": None, "department_id": None},
        {"patient_id": 3, "facility_id": 1, "encounter_id": None, "department_id": None},
        {"patient_id": 4, "facility_id": 1, "encounter_id": None, "department_id": None},
        {"patient_id": 5, "facility_id": 1, "encounter_id": None, "department_id": None}
    ]

def generate_vitals(patient, anomaly_rate):
    """Generate vital observations. Normal ranges vs. distress anomalies."""
    is_anomaly = random.random() < anomaly_rate

    timestamp = datetime.now(timezone.utc).isoformat()

    if is_anomaly:
        anomaly_type = random.choice(["hypoxia", "tachycardia", "hypertension", "fever"])
        print(f"Generating clinical anomaly [{anomaly_type}] for patient {patient['patient_id']}")

        if anomaly_type == "hypoxia":
            heart_rate = float(random.randint(105, 130))
            spo2 = float(random.randint(85, 92))  # Critical drop in oxygen
            systolic_bp = float(random.randint(110, 140))
            diastolic_bp = float(random.randint(70, 90))
            temp = float(round(random.uniform(36.5, 37.5), 1))
            resp_rate = float(random.randint(22, 30))  # Rapid breathing
        elif anomaly_type == "tachycardia":
            heart_rate = float(random.randint(130, 160)) # Severe heart rate spike
            spo2 = float(random.randint(94, 98))
            systolic_bp = float(random.randint(120, 150))
            diastolic_bp = float(random.randint(80, 100))
            temp = float(round(random.uniform(36.5, 37.5), 1))
            resp_rate = float(random.randint(16, 24))
        elif anomaly_type == "hypertension":
            heart_rate = float(random.randint(80, 105))
            spo2 = float(random.randint(95, 99))
            systolic_bp = float(random.randint(165, 195)) # Critical hypertensive crisis
            diastolic_bp = float(random.randint(100, 120))
            temp = float(round(random.uniform(36.5, 37.2), 1))
            resp_rate = float(random.randint(12, 18))
        else: # fever
            heart_rate = float(random.randint(95, 115))
            spo2 = float(random.randint(94, 97))
            systolic_bp = float(random.randint(110, 130))
            diastolic_bp = float(random.randint(70, 85))
            temp = float(round(random.uniform(39.0, 40.5), 1)) # High fever
            resp_rate = float(random.randint(18, 26))
    else:
        # Normal, stable vitals
        heart_rate = float(random.randint(65, 88))
        spo2 = float(random.randint(96, 99))
        systolic_bp = float(random.randint(112, 128))
        diastolic_bp = float(random.randint(72, 84))
        temp = float(round(random.uniform(36.4, 37.2), 1))
        resp_rate = float(random.randint(12, 16))

    return {
        "patient_id": patient["patient_id"],
        "facility_id": patient["facility_id"],
        "encounter_id": patient["encounter_id"],
        "department_id": patient["department_id"],
        "heart_rate": heart_rate,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "spo2": spo2,
        "temperature_c": temp,
        "respiratory_rate": resp_rate,
        "source": "device",
        "timestamp": timestamp
    }

def cleanup_old_files(directory, max_age_seconds):
    """Clean up older streaming files to keep directory size bound."""
    now = time.time()
    count = 0
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath) and filename.endswith(".json"):
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    count += 1
        if count > 0:
            print(f"Purged {count} obsolete telemetry files older than {max_age_seconds / 60:.1f} minutes.")
    except Exception as e:
        print(f"Error during folder cleanup: {e}")

def main():
    args = parse_args()
    print("=" * 60)
    print("REAL-TIME CLINICAL VITAL SIGNS TELEMETRY SIMULATOR")
    print("=" * 60)
    print(f"Interval: {args.interval}s")
    print(f"Anomaly Rate: {args.anomaly_rate * 100:.1f}%")

    # Initialize Kafka if configured
    producer = None
    if args.kafka:
        print(f"Publishing mode: Kafka broker ({args.kafka_servers}) -> topic '{args.kafka_topic}'")
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=args.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            print("Successfully connected to Kafka Broker.")
        except ImportError:
            print("ERROR: 'kafka-python' is not installed. Run 'pip install kafka-python' or run without --kafka.")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to connect to Kafka: {e}")
            sys.exit(1)
    else:
        print(f"Publishing mode: Local Directory Stream -> '{args.output_dir}'")
        os.makedirs(args.output_dir, exist_ok=True)

    iteration = 0
    try:
        while True:
            patients = get_active_patients()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Simulating {len(patients)} patients...")

            for patient in patients:
                vital_reading = generate_vitals(patient, args.anomaly_rate)

                if producer is not None:
                    # Write to Kafka
                    producer.send(args.kafka_topic, value=vital_reading)
                else:
                    # Write to local JSON file
                    file_timestamp = int(time.time() * 1000)
                    filename = f"vital_patient_{patient['patient_id']}_{file_timestamp}.json"
                    filepath = os.path.join(args.output_dir, filename)
                    with open(filepath, "w") as f:
                        json.dump(vital_reading, f)

            if producer is not None:
                producer.flush()

            iteration += 1

            # Run cleanup every 10 iterations to prevent file buildup
            if not args.kafka and iteration % 10 == 0:
                cleanup_old_files(args.output_dir, args.cleanup_minutes * 60)

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
    finally:
        if producer is not None:
            producer.close()

if __name__ == "__main__":
    main()
