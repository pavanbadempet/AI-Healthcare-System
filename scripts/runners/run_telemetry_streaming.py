"""
Real-Time Telemetry Analytics Pipeline.

Uses PySpark Structured Streaming to read vital observations from a streaming source,
calculates sliding window vital sign averages, applies pre-trained ML models (heart and lung risk),
and commits conformed observations and critical alerts (MonitoringSignals) to the database.
"""

import argparse
import logging
import os
import pickle
import sys
import time
from datetime import datetime, timezone

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from backend.database import SessionLocal
from backend.models import MonitoringSignal, VitalObservation

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TelemetryStreaming")

DEFAULT_STREAM_DIR = os.path.join(BASE_DIR, "data", "telemetry_stream")

# Global variables for models
_models_loaded = False
heart_model = None
lungs_model = None
lungs_scaler = None

def load_ml_models():
    """Load Scikit-Learn models once to reuse across micro-batches."""
    global _models_loaded, heart_model, lungs_model, lungs_scaler
    if _models_loaded:
        return

    backend_dir = os.path.join(BASE_DIR, "backend")

    # Load heart disease model
    heart_path = os.path.join(backend_dir, "heart_disease_model.pkl")
    if os.path.exists(heart_path):
        try:
            with open(heart_path, "rb") as f:
                heart_model = pickle.load(f)
            logger.info("Successfully loaded pre-trained Heart Disease model.")
        except Exception as e:
            logger.error(f"Failed to load Heart model: {e}")
    else:
        logger.warning(f"Heart model not found at {heart_path}. Using fallback heuristics.")

    # Load lung model and scaler
    lungs_path = os.path.join(backend_dir, "lungs_model.pkl")
    scaler_path = os.path.join(backend_dir, "lungs_scaler.pkl")

    if os.path.exists(lungs_path):
        try:
            with open(lungs_path, "rb") as f:
                lungs_model = pickle.load(f)
            logger.info("Successfully loaded pre-trained Lungs model.")

            if os.path.exists(scaler_path):
                with open(scaler_path, "rb") as f:
                    lungs_scaler = pickle.load(f)
                logger.info("Successfully loaded Lungs feature scaler.")
        except Exception as e:
            logger.error(f"Failed to load Lungs model/scaler: {e}")
    else:
        logger.warning(f"Lungs model not found at {lungs_path}. Using fallback heuristics.")

    _models_loaded = True

def predict_heart_disease_risk(avg_hr, avg_systolic_bp):
    """Predict heart disease probability using ML model or fallback heuristics."""
    if heart_model is not None:
        try:
            # Heart input list features:
            # [age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]
            # Map avg_systolic_bp -> trestbps, avg_hr -> thalach
            # Use safe clinical baseline profile for other static fields
            input_list = [
                55.0,   # age
                1.0,    # sex (Male)
                1.0,    # cp (typical angina)
                float(avg_systolic_bp),  # trestbps
                230.0,  # chol (mildly elevated)
                0.0,    # fbs (normal sugar)
                1.0,    # restecg (normal)
                float(avg_hr),  # thalach (max HR)
                0.0,    # exang (no exercise-induced angina)
                1.0,    # oldpeak (slight ST depression)
                1.0,    # slope
                0.0,    # ca
                2.0     # thal
            ]

            # Predict probabilities
            if hasattr(heart_model, "predict_proba"):
                probs = heart_model.predict_proba([input_list])[0]
                return float(probs[1]) # probability of heart disease
            else:
                pred = heart_model.predict([input_list])[0]
                return 0.85 if pred == 1 else 0.15
        except Exception as e:
            logger.debug(f"Heart model prediction failed: {e}. Falling back to heuristics.")

    # Fallback heuristic: high blood pressure + high heart rate = increased cardiac strain
    risk = 0.10
    if avg_hr > 100: risk += 0.25
    if avg_hr > 130: risk += 0.35
    if avg_systolic_bp > 140: risk += 0.20
    if avg_systolic_bp > 170: risk += 0.30
    return min(risk, 0.99)

def predict_lung_risk(avg_spo2, avg_resp_rate):
    """Predict lung issue probability using ML model or fallback heuristics."""
    if lungs_model is not None:
        try:
            import pandas as pd
            # Lungs features:
            # ['GENDER', 'AGE', 'SMOKING', 'YELLOW_FINGERS', 'ANXIETY', 'PEER_PRESSURE',
            #  'CHRONIC_DISEASE', 'FATIGUE', 'ALLERGY', 'WHEEZING', 'ALCOHOL_CONSUMING',
            #  'COUGHING', 'SHORTNESS_OF_BREATH', 'SWALLOWING_DIFFICULTY', 'CHEST_PAIN']
            # Map: 2 for YES / 1 for NO
            shortness_of_breath = 2 if avg_spo2 < 94.0 or avg_resp_rate > 22.0 else 1
            wheezing = 2 if avg_resp_rate > 20.0 else 1
            coughing = 2 if avg_resp_rate > 18.0 else 1
            fatigue = 2 if avg_spo2 < 95.0 else 1
            chest_pain = 2 if avg_spo2 < 92.0 else 1

            input_list = [
                1,      # GENDER (Male)
                55,     # AGE
                2,      # SMOKING (YES)
                1,      # YELLOW_FINGERS
                1,      # ANXIETY
                1,      # PEER_PRESSURE
                1,      # CHRONIC_DISEASE
                fatigue,
                1,      # ALLERGY
                wheezing,
                1,      # ALCOHOL_CONSUMING
                coughing,
                shortness_of_breath,
                1,      # SWALLOWING_DIFFICULTY
                chest_pain
            ]

            feature_names = [
                'GENDER', 'AGE', 'SMOKING', 'YELLOW_FINGERS', 'ANXIETY', 'PEER_PRESSURE',
                'CHRONIC_DISEASE', 'FATIGUE', 'ALLERGY', 'WHEEZING', 'ALCOHOL_CONSUMING',
                'COUGHING', 'SHORTNESS_OF_BREATH', 'SWALLOWING_DIFFICULTY', 'CHEST_PAIN'
            ]

            df = pd.DataFrame([input_list], columns=feature_names)
            if lungs_scaler is not None:
                X = lungs_scaler.transform(df)
            else:
                X = df.values

            if hasattr(lungs_model, "predict_proba"):
                probs = lungs_model.predict_proba(X)[0]
                return float(probs[1]) # probability of lung issue
            else:
                pred = lungs_model.predict(X)[0]
                # In lung dataset, 1 is positive, 0 is negative
                return 0.85 if pred == 1 else 0.15
        except Exception as e:
            logger.debug(f"Lung model prediction failed: {e}. Falling back to heuristics.")

    # Fallback heuristic: low oxygen + high respiration = respiratory strain
    risk = 0.05
    if avg_spo2 < 95: risk += 0.20
    if avg_spo2 < 92: risk += 0.45
    if avg_spo2 < 88: risk += 0.25
    if avg_resp_rate > 20: risk += 0.15
    if avg_resp_rate > 26: risk += 0.20
    return min(risk, 0.99)

def process_conformed_record(db, record, avg_stats=None, heart_risk=None, lung_risk=None, flush=True):
    """Processes a single conformed vital observation record and generates alerts."""
    patient_id = int(record["patient_id"])
    heart_rate = float(record["heart_rate"]) if record.get("heart_rate") is not None else 75.0
    systolic_bp = float(record["systolic_bp"]) if record.get("systolic_bp") is not None else 120.0
    diastolic_bp = float(record["diastolic_bp"]) if record.get("diastolic_bp") is not None else 80.0
    spo2 = float(record["spo2"]) if record.get("spo2") is not None else 98.0
    temp = float(record["temperature_c"]) if record.get("temperature_c") is not None else 37.0
    resp_rate = float(record["respiratory_rate"]) if record.get("respiratory_rate") is not None else 14.0

    facility_id = int(record["facility_id"]) if record.get("facility_id") is not None else 1
    encounter_id = int(record["encounter_id"]) if record.get("encounter_id") is not None else None
    department_id = int(record["department_id"]) if record.get("department_id") is not None else None

    observed_at_str = record["timestamp"]
    try:
        observed_at = datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))
    except Exception:
        observed_at = datetime.now(timezone.utc)

    # --- 1. Write conformed vital observation ---
    observation = VitalObservation(
        facility_id=facility_id,
        patient_id=patient_id,
        encounter_id=encounter_id,
        department_id=department_id,
        heart_rate=heart_rate,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        spo2=spo2,
        temperature_c=temp,
        respiratory_rate=resp_rate,
        source="device",
        observed_at=observed_at,
        created_at=datetime.now(timezone.utc)
    )
    db.add(observation)
    if flush:
        db.flush() # Flush to get observation.id

    # --- 2. Calculate Rolling Averages (last 2 minutes) ---
    if avg_stats is not None:
        avg_hr, avg_systolic_bp, avg_diastolic_bp, avg_spo2, avg_temp, avg_resp_rate = avg_stats
    else:
        from datetime import timedelta
        from sqlalchemy import func
        two_minutes_ago = observed_at - timedelta(minutes=2)

        # Fetch averages from DB
        stats = db.query(
            func.avg(VitalObservation.heart_rate),
            func.avg(VitalObservation.systolic_bp),
            func.avg(VitalObservation.diastolic_bp),
            func.avg(VitalObservation.spo2),
            func.avg(VitalObservation.temperature_c),
            func.avg(VitalObservation.respiratory_rate)
        ).filter(
            VitalObservation.patient_id == patient_id,
            VitalObservation.observed_at >= two_minutes_ago
        ).first()

        avg_hr = float(stats[0]) if stats[0] is not None else heart_rate
        avg_systolic_bp = float(stats[1]) if stats[1] is not None else systolic_bp
        avg_diastolic_bp = float(stats[2]) if stats[2] is not None else diastolic_bp
        avg_spo2 = float(stats[3]) if stats[3] is not None else spo2
        avg_temp = float(stats[4]) if stats[4] is not None else temp
        avg_resp_rate = float(stats[5]) if stats[5] is not None else resp_rate

    # --- 3. Calculate ML Risk Probabilities ---
    ml_start = time.perf_counter()
    h_risk = heart_risk if heart_risk is not None else predict_heart_disease_risk(avg_hr, avg_systolic_bp)
    l_risk = lung_risk if lung_risk is not None else predict_lung_risk(avg_spo2, avg_resp_rate)
    ml_duration_ms = (time.perf_counter() - ml_start) * 1000

    # --- 4. Evaluate Alerts & Severity ---
    trigger_alert = False
    severity = "info"
    title = ""
    summary = []

    if avg_spo2 < 92.0:
        trigger_alert = True
        severity = "critical"
        title = "Critical Hypoxia Alert"
        summary.append(f"Severe blood oxygen desaturation detected: {avg_spo2:.1f}%.")
    elif avg_spo2 < 94.0:
        trigger_alert = True
        severity = "warning" if severity != "critical" else severity
        title = title or "Borderline Hypoxia Alert"
        summary.append(f"Borderline blood oxygen levels: {avg_spo2:.1f}%.")

    if avg_hr > 130.0 or avg_hr < 45.0:
        trigger_alert = True
        severity = "critical"
        title = "Critical Arrhythmia Alert"
        summary.append(f"Extreme heart rate threshold breached: {avg_hr:.1f} bpm.")
    elif avg_hr > 105.0 or avg_hr < 55.0:
        trigger_alert = True
        severity = "warning" if severity != "critical" else severity
        title = title or "Abnormal Heart Rate Alert"
        summary.append(f"Abnormal heart rate: {avg_hr:.1f} bpm.")

    if avg_systolic_bp > 160.0 or avg_diastolic_bp > 100.0:
        trigger_alert = True
        severity = "warning" if severity != "critical" else severity
        title = title or "Severe Hypertension Alert"
        summary.append(f"Elevated blood pressure: {avg_systolic_bp:.1f}/{avg_diastolic_bp:.1f} mmHg.")

    if l_risk > 0.75:
        trigger_alert = True
        severity = "critical"
        title = title or "High Respiratory Distress Risk"
        summary.append(f"Lung ML model predicts {l_risk*100:.1f}% risk of respiratory failure.")
    elif h_risk > 0.75:
        trigger_alert = True
        severity = "critical"
        title = title or "High Cardiac Distress Risk"
        summary.append(f"Heart ML model predicts {h_risk*100:.1f}% risk of cardiovascular collapse.")

    alert_summary = " ".join(summary)
    if trigger_alert:
        logger.warning(f"ALERT! Patient {patient_id} - {title}: {alert_summary}")

        if flush:
            signal = MonitoringSignal(
                facility_id=facility_id,
                patient_id=patient_id,
                vital_observation_id=observation.id,
                encounter_id=encounter_id,
                department_id=department_id,
                signal_type="critical_collapse_risk" if severity == "critical" else "vital_anomaly",
                severity=severity,
                title=title,
                summary=alert_summary,
                status="open",
                created_at=datetime.now(timezone.utc)
            )
            db.add(signal)
            return ml_duration_ms
        else:
            return ml_duration_ms, (observation, severity, title, alert_summary, facility_id, encounter_id, department_id)

    if flush:
        return ml_duration_ms
    else:
        return ml_duration_ms, None

def process_batch(df, batch_id):
    """Processes a micro-batch of vitals data using native PySpark execution."""
    records = df.collect()
    if not records:
        return

    logger.info(f"Processing micro-batch {batch_id} with {len(records)} records...")
    load_ml_models()
    db = SessionLocal()
    start_time = time.perf_counter()
    total_ml_latency = 0.0
    try:
        # Convert records to dictionary format
        records_dict = [row.asDict() for row in records]

        # 1. Bulk pre-fetch historical vitals for all patient_ids in the batch
        patient_ids = list({int(r["patient_id"]) for r in records_dict if r.get("patient_id") is not None})

        # Extract and parse timestamps
        record_datetimes = []
        for r in records_dict:
            ts_str = r.get("timestamp")
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
            r["_datetime"] = dt
            record_datetimes.append(dt)

        min_observed_at = min(record_datetimes) if record_datetimes else datetime.now(timezone.utc)
        from datetime import timedelta
        two_minutes_before_min = min_observed_at - timedelta(minutes=2)

        # Query DB in bulk for these patients
        historical_vitals = db.query(
            VitalObservation.patient_id,
            VitalObservation.heart_rate,
            VitalObservation.systolic_bp,
            VitalObservation.diastolic_bp,
            VitalObservation.spo2,
            VitalObservation.temperature_c,
            VitalObservation.respiratory_rate,
            VitalObservation.observed_at
        ).filter(
            VitalObservation.patient_id.in_(patient_ids),
            VitalObservation.observed_at >= two_minutes_before_min
        ).all()

        # Group historical vitals by patient_id
        patient_history = {}
        for hv in historical_vitals:
            pid = hv.patient_id
            if pid not in patient_history:
                patient_history[pid] = []
            patient_history[pid].append({
                "heart_rate": hv.heart_rate,
                "systolic_bp": hv.systolic_bp,
                "diastolic_bp": hv.diastolic_bp,
                "spo2": hv.spo2,
                "temperature_c": hv.temperature_c,
                "respiratory_rate": hv.respiratory_rate,
                "observed_at": hv.observed_at.replace(tzinfo=timezone.utc) if hv.observed_at.tzinfo is None else hv.observed_at
            })

        # 2. Compute rolling averages for each record in the batch (chronologically)
        sorted_records = sorted(records_dict, key=lambda x: x["_datetime"])

        calculated_stats = []
        for r in sorted_records:
            pid = int(r["patient_id"])
            obs_at = r["_datetime"].replace(tzinfo=timezone.utc) if r["_datetime"].tzinfo is None else r["_datetime"]

            if pid not in patient_history:
                patient_history[pid] = []

            # Add current observation to history
            patient_history[pid].append({
                "heart_rate": float(r["heart_rate"]) if r.get("heart_rate") is not None else 75.0,
                "systolic_bp": float(r["systolic_bp"]) if r.get("systolic_bp") is not None else 120.0,
                "diastolic_bp": float(r["diastolic_bp"]) if r.get("diastolic_bp") is not None else 80.0,
                "spo2": float(r["spo2"]) if r.get("spo2") is not None else 98.0,
                "temperature_c": float(r["temperature_c"]) if r.get("temperature_c") is not None else 37.0,
                "respiratory_rate": float(r["respiratory_rate"]) if r.get("respiratory_rate") is not None else 14.0,
                "observed_at": obs_at
            })

            # Filter history to last 2 minutes
            cutoff = obs_at - timedelta(minutes=2)
            patient_history[pid] = [h for h in patient_history[pid] if h["observed_at"] >= cutoff]

            # Calculate averages
            hist = patient_history[pid]
            avg_hr = sum(h["heart_rate"] for h in hist) / len(hist)
            avg_systolic_bp = sum(h["systolic_bp"] for h in hist) / len(hist)
            avg_diastolic_bp = sum(h["diastolic_bp"] for h in hist) / len(hist)
            avg_spo2 = sum(h["spo2"] for h in hist) / len(hist)
            avg_temp = sum(h["temperature_c"] for h in hist) / len(hist)
            avg_resp_rate = sum(h["respiratory_rate"] for h in hist) / len(hist)

            stats = (avg_hr, avg_systolic_bp, avg_diastolic_bp, avg_spo2, avg_temp, avg_resp_rate)
            calculated_stats.append(stats)
            r["_avg_stats"] = stats

        # 3. Vectorized ML Inference
        import numpy as np
        import pandas as pd

        heart_inputs = []
        lung_inputs = []

        for r in sorted_records:
            avg_hr, avg_systolic_bp, _, avg_spo2, _, avg_resp_rate = r["_avg_stats"]
            heart_inputs.append([
                55.0, 1.0, 1.0, float(avg_systolic_bp), 230.0, 0.0, 1.0, float(avg_hr), 0.0, 1.0, 1.0, 0.0, 2.0
            ])
            shortness_of_breath = 2 if avg_spo2 < 94.0 or avg_resp_rate > 22.0 else 1
            wheezing = 2 if avg_resp_rate > 20.0 else 1
            coughing = 2 if avg_resp_rate > 18.0 else 1
            fatigue = 2 if avg_spo2 < 95.0 else 1
            chest_pain = 2 if avg_spo2 < 92.0 else 1
            lung_inputs.append([
                1, 55, 2, 1, 1, 1, 1, fatigue, 1, wheezing, 1, coughing, shortness_of_breath, 1, chest_pain
            ])

        heart_probs = None
        lung_probs = None

        ml_start = time.perf_counter()
        if heart_model is not None and hasattr(heart_model, "predict_proba"):
            try:
                heart_probs = heart_model.predict_proba(heart_inputs)[:, 1]
            except Exception as ex:
                logger.debug(f"Vectorized heart model prediction failed: {ex}")

        if lungs_model is not None and hasattr(lungs_model, "predict_proba"):
            try:
                feature_names = [
                    'GENDER', 'AGE', 'SMOKING', 'YELLOW_FINGERS', 'ANXIETY', 'PEER_PRESSURE',
                    'CHRONIC_DISEASE', 'FATIGUE', 'ALLERGY', 'WHEEZING', 'ALCOHOL_CONSUMING',
                    'COUGHING', 'SHORTNESS_OF_BREATH', 'SWALLOWING_DIFFICULTY', 'CHEST_PAIN'
                ]
                df_lung = pd.DataFrame(lung_inputs, columns=feature_names)
                if lungs_scaler is not None:
                    X_lung = lungs_scaler.transform(df_lung)
                else:
                    X_lung = df_lung.values
                lung_probs = lungs_model.predict_proba(X_lung)[:, 1]
            except Exception as ex:
                logger.debug(f"Vectorized lungs model prediction failed: {ex}")
        ml_duration_ms = (time.perf_counter() - ml_start) * 1000

        # 4. Process records individually with pre-computed values, without flushing yet
        pending_alerts = []
        for i, r in enumerate(sorted_records):
            h_risk = float(heart_probs[i]) if heart_probs is not None else None
            l_risk = float(lung_probs[i]) if lung_probs is not None else None

            res = process_conformed_record(
                db, r,
                avg_stats=r["_avg_stats"],
                heart_risk=h_risk,
                lung_risk=l_risk,
                flush=False
            )

            # Handle mock returning float/int or tuple (for unit test compatibility)
            if isinstance(res, tuple):
                ml_lat, alert_tuple = res
            else:
                ml_lat = res
                alert_tuple = None

            total_ml_latency += ml_lat
            if alert_tuple is not None:
                pending_alerts.append(alert_tuple)

        # 5. Bulk insert observations and flush to generate auto-incrementing IDs
        db.flush()

        # 6. Bulk insert monitoring signals using generated observation IDs
        signals_to_add = []
        for obs_obj, severity, title, alert_summary, fac_id, enc_id, dept_id in pending_alerts:
            signal = MonitoringSignal(
                facility_id=fac_id,
                patient_id=obs_obj.patient_id,
                vital_observation_id=obs_obj.id,
                encounter_id=enc_id,
                department_id=dept_id,
                signal_type="critical_collapse_risk" if severity == "critical" else "vital_anomaly",
                severity=severity,
                title=title,
                summary=alert_summary,
                status="open",
                created_at=datetime.now(timezone.utc)
            )
            signals_to_add.append(signal)

        if signals_to_add:
            db.add_all(signals_to_add)

        # Calculate total batch processing duration
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000

        # Save Spark batch metrics
        from backend.models.clinical import SparkStreamingMetrics
        metric = SparkStreamingMetrics(
            batch_id=batch_id,
            records_processed=len(records),
            processing_time_ms=processing_time_ms,
            ml_latency_ms=total_ml_latency,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(metric)
        db.commit()
        logger.info(f"Successfully processed micro-batch {batch_id} with {len(records)} records in {processing_time_ms:.1f}ms")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process micro-batch {batch_id}: {e}")
        raise e
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Spark Structured Streaming pipeline for patient vital telemetry.")
    parser.add_argument("--input-dir", default=DEFAULT_STREAM_DIR, help="Local directory stream source (JSON files)")
    parser.add_argument("--kafka", action="store_true", help="Ingest directly from Kafka topic stream")
    parser.add_argument("--kafka-servers", default="localhost:9092", help="Kafka bootstrap servers list")
    parser.add_argument("--kafka-topic", default="hospital.vitals_stream", help="Kafka topic name")
    parser.add_argument("--processing-time", default="5 seconds", help="Trigger processing time interval")
    parser.add_argument("--checkpoint-dir", default=os.path.join(BASE_DIR, "data", "checkpoints", "telemetry"), help="Checkpoint directory")
    args = parser.parse_args()

    # Configure HADOOP_HOME for Windows PySpark execution
    if os.name == "nt":
        local_hadoop = os.path.join(BASE_DIR, ".hadoop")
        if os.path.exists(local_hadoop):
            os.environ["HADOOP_HOME"] = local_hadoop
            # Ensure hadoop.dll can be loaded by adding bin to PATH
            hadoop_bin = os.path.join(local_hadoop, "bin")
            if hadoop_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = hadoop_bin + os.pathsep + os.environ.get("PATH", "")
            logger.info(f"Set HADOOP_HOME to: {local_hadoop} and updated PATH.")
        else:
            logger.warning(f"Windows environment detected but local .hadoop directory not found at {local_hadoop}. "
                           "PySpark may fail if HADOOP_HOME is not set globally.")

    # Ensure Spark workers use the exact same Python environment as the driver
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    logger.info(f"Set PYSPARK_PYTHON and PYSPARK_DRIVER_PYTHON to: {sys.executable}")

    print("=" * 60)
    print("SPARK STRUCTURED STREAMING VITAL SIGNS PIPELINE")
    print("=" * 60)

    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import avg, col, first, max, to_timestamp, window  # noqa: F401
        from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType
    except ImportError:
        print("ERROR: PySpark is not installed. Run 'pip install pyspark' before executing this streaming pipeline.")
        sys.exit(1)

    os.makedirs(args.checkpoint_dir, exist_ok=True)

    spark = SparkSession.builder \
        .appName("TelemetryStreamingPipeline") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

    logger.info("Created PySpark session successfully.")

    # Define conformed vitals schema
    vitals_schema = StructType([
        StructField("patient_id", IntegerType(), False),
        StructField("facility_id", IntegerType(), True),
        StructField("encounter_id", IntegerType(), True),
        StructField("department_id", IntegerType(), True),
        StructField("heart_rate", DoubleType(), True),
        StructField("systolic_bp", DoubleType(), True),
        StructField("diastolic_bp", DoubleType(), True),
        StructField("spo2", DoubleType(), True),
        StructField("temperature_c", DoubleType(), True),
        StructField("respiratory_rate", DoubleType(), True),
        StructField("source", StringType(), True),
        StructField("timestamp", StringType(), False)
    ])

    # Configure input stream
    if args.kafka:
        logger.info(f"Subscribing to Kafka bootstrap={args.kafka_servers} topic={args.kafka_topic}...")
        from pyspark.sql.functions import from_json

        kafka_stream = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", args.kafka_servers) \
            .option("subscribe", args.kafka_topic) \
            .option("startingOffsets", "latest") \
            .load()

        vitals_stream = kafka_stream.select(
            from_json(col("value").cast("string"), vitals_schema).alias("data")
        ).select("data.*")
    else:
        logger.info(f"Monitoring local directory stream source: '{args.input_dir}'")
        if not os.path.exists(args.input_dir):
            os.makedirs(args.input_dir, exist_ok=True)

        vitals_stream = spark.readStream \
            .format("json") \
            .schema(vitals_schema) \
            .option("maxFilesPerTrigger", 10) \
            .load(args.input_dir)

    # Start the Structured Streaming query with foreachBatch
    logger.info("Initializing Structured Streaming query with foreachBatch...")
    query = vitals_stream.writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", args.checkpoint_dir) \
        .trigger(processingTime=args.processing_time) \
        .start()

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        logger.info("Stopping telemetry streaming query...")
    finally:
        logger.info("Halting streaming query...")
        query.stop()
        spark.stop()
        logger.info("Spark session halted.")

if __name__ == "__main__":
    main()
