import os
import psycopg2
from datetime import datetime, timezone, timedelta

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("No DATABASE_URL set.")
    exit(1)

conn = psycopg2.connect(db_url)
cur = conn.cursor()

print("Connected to Neon DB. Checking tables...")

# 1. Update patient users with clean, professional, non-encrypted full names
patients_data = [
    (1, "m_thorne", "Marcus Thorne", "male", "1968-04-12", "A+", "Acute Anterior STEMI • Post-PCI Stent"),
    (4, "s_jenkins", "Sarah Jenkins", "female", "1984-09-22", "O+", "Diabetic Ketoacidosis • Insulin Protocol"),
    (7, "l_zhao", "Linda Zhao", "female", "1960-11-05", "B+", "Acute Respiratory Distress Syndrome (ARDS)"),
    (15, "r_garcia", "Robert Garcia", "male", "1975-02-18", "O-", "Post-Coronary Artery Bypass Graft (CABG)"),
]

for uid, username, full_name, gender, dob, blood_type, ailments in patients_data:
    cur.execute("""
        UPDATE users 
        SET username = %s, full_name = %s, gender = %s, dob = %s, blood_type = %s, existing_ailments = %s
        WHERE id = %s
    """, (username, full_name, gender, dob, blood_type, ailments, uid))
    print(f"Updated user #{uid} -> {full_name}")

# Also check Emily Watson and Oscar Meyer
cur.execute("SELECT id FROM users WHERE username = 'e_watson'")
watson_row = cur.fetchone()
if not watson_row:
    cur.execute("""
        INSERT INTO users (username, hashed_password, role, full_name, gender, dob, blood_type, existing_ailments, facility_id, is_deleted)
        VALUES ('e_watson', 'pbkdf2_sha256$mockhash', 'patient', 'Emily Watson', 'female', '1990-07-14', 'A-', 'Submassive Pulmonary Embolism', 1, 0)
        RETURNING id
    """)
    watson_id = cur.fetchone()[0]
else:
    watson_id = watson_row[0]

cur.execute("SELECT id FROM users WHERE username = 'o_meyer'")
meyer_row = cur.fetchone()
if not meyer_row:
    cur.execute("""
        INSERT INTO users (username, hashed_password, role, full_name, gender, dob, blood_type, existing_ailments, facility_id, is_deleted)
        VALUES ('o_meyer', 'pbkdf2_sha256$mockhash', 'patient', 'Oscar Meyer', 'male', '1954-03-30', 'B-', 'Decompensated Congestive Heart Failure', 1, 0)
        RETURNING id
    """)
    meyer_id = cur.fetchone()[0]
else:
    meyer_id = meyer_row[0]

# 2. Update Beds in Neon DB
beds_data = [
    ("ICU-A-01", "Cardiology ICU", "occupied", 1),
    ("ICU-A-02", "Cardiology ICU", "occupied", 4),
    ("ICU-A-03", "Cardiology ICU", "occupied", 7),
    ("ICU-A-04", "Cardiology ICU", "occupied", 15),
    ("ICU-A-05", "Cardiology ICU", "available", None),
]

cur.execute("DELETE FROM beds")
for bed_no, ward, status, pid in beds_data:
    cur.execute("""
        INSERT INTO beds (bed_number, ward, status, current_patient_id, facility_id, department_id)
        VALUES (%s, %s, %s, %s, 1, 1)
    """, (bed_no, ward, status, pid))
print("Seeded 5 clinical beds in ICU.")

# 3. Ensure Encounters and Admissions exist for these active patients
for pid, enc_type, complaint in [
    (1, "EMERGENCY", "Acute STEMI chest pain"),
    (4, "INPATIENT", "DKA with metabolic acidosis"),
    (7, "ICU", "Hypoxemic respiratory failure"),
    (15, "SURGICAL", "Post-CABG step-down monitoring"),
]:
    cur.execute("SELECT id FROM encounters WHERE patient_id = %s LIMIT 1", (pid,))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO encounters (patient_id, facility_id, department_id, encounter_type, status, reason, priority, started_at, is_deleted)
            VALUES (%s, 1, 1, %s, 'open', %s, 'urgent', NOW(), 0)
            RETURNING id
        """, (pid, enc_type, complaint))
        enc_id = cur.fetchone()[0]
    else:
        enc_id = row[0]
        cur.execute("UPDATE encounters SET status = 'open', reason = %s WHERE id = %s", (complaint, enc_id))

    cur.execute("SELECT id FROM admissions WHERE patient_id = %s LIMIT 1", (pid,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO admissions (patient_id, facility_id, encounter_id, admitted_at, status, reason, doctor_id, department_id, is_deleted)
            VALUES (%s, 1, %s, NOW() - INTERVAL '1 day', 'active', %s, 11, 1, 0)
        """, (pid, enc_id, complaint))
        print(f"Created admission for patient #{pid}")

# 4. Seed Time-Series Vital Observations for each active patient
now = datetime.now(timezone.utc)
vitals_plan = [
    # (patient_id, hr_base, sbp_base, dbp_base, spo2_base, temp_base, rr_base, glucose_base)
    (1, 112, 148, 94, 91.5, 37.4, 24, 118), # Marcus Thorne (STEMI / Alert)
    (4, 82, 122, 78, 98.0, 36.8, 16, 235), # Sarah Jenkins (DKA / Elevated Glucose)
    (7, 68, 112, 72, 99.0, 36.6, 14, 98),  # Linda Zhao (Stable ARDS recovery)
    (15, 78, 130, 84, 97.0, 37.0, 18, 110), # Robert Garcia (Post-CABG)
]

cur.execute("DELETE FROM vital_observations")
total_obs = 0
for pid, hr, sbp, dbp, spo2, temp, rr, glucose in vitals_plan:
    # 8 time points over the past 2 hours
    for i in range(8):
        t = now - timedelta(minutes=(7 - i) * 15)
        # Add slight natural physiological jitter
        jitter_hr = hr + ((i % 3) - 1) * 2
        jitter_spo2 = min(100.0, spo2 + ((i % 2) - 0.5))
        jitter_sbp = sbp + ((i % 3) - 1) * 3
        cur.execute("""
            INSERT INTO vital_observations (
                patient_id, facility_id, department_id, source,
                heart_rate, systolic_bp, diastolic_bp, spo2,
                temperature_c, respiratory_rate, blood_glucose,
                observed_at, created_at, is_deleted
            )
            VALUES (%s, 1, 1, 'device', %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
        """, (pid, jitter_hr, jitter_sbp, dbp, jitter_spo2, temp, rr, glucose, t, t))
        total_obs += 1

print(f"Seeded {total_obs} high-fidelity vital observations across 4 active patients.")

conn.commit()
conn.close()
print("Database seeding completed successfully!")
