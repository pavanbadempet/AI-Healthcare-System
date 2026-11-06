"""Database seeding routines for admin bootstrap and demo clinical data."""
import logging
import os
from datetime import datetime, timezone

from . import auth, database, models

logger = logging.getLogger(__name__)


def create_default_admin():
    """Create a configured admin user if explicit bootstrap credentials are provided."""
    default_username = os.getenv("DEFAULT_ADMIN_USERNAME")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    if not default_username or not default_password:
        logger.info("Default admin seeding skipped; bootstrap credentials are not configured.")
        return

    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL") or f"{default_username}@system.local"

    with database.get_db_context() as session:
        try:
            # Check if username, email, or admin role already exists
            existing_user = session.query(models.User).filter(
                (models.User.username == default_username) |
                (models.User.email == admin_email) |
                (models.User.role == "admin")
            ).first()

            if not existing_user:
                logger.warning("No admin user found. Creating configured bootstrap admin user...")
                hashed_pw = auth.get_password_hash(default_password)
                default_admin = models.User(
                    username=default_username,
                    hashed_password=hashed_pw,
                    email=admin_email,
                    role="admin",
                    full_name=os.getenv("DEFAULT_ADMIN_FULL_NAME", "System Administrator"),
                    allow_data_collection=0
                )
                session.add(default_admin)
                session.commit()
                logger.info("Default admin created from configured bootstrap credentials.")
            else:
                logger.info("Admin or matching bootstrap account already exists (%s).", existing_user.username)
        except Exception:
            session.rollback()
            logger.warning("Default admin seeding skipped due to existing constraint or uninitialized schema.")


def seed_hospital_operations_data():
    """Seeds default facility, departments, and beds if the database has none."""
    with database.get_db_context() as session:
        try:
            facility = session.query(models.HospitalFacility).first()
            if not facility:
                facility = models.HospitalFacility(
                    name="Central General Hospital",
                    facility_type="hospital",
                    country="US",
                    region="North America",
                    status="active"
                )
                session.add(facility)
                session.commit()
                session.refresh(facility)

            existing_depts = session.query(models.Department).count()
            if existing_depts == 0:
                dept_list = [
                    ("Intensive Care Unit (ICU-A)", "IPD", "Building A - 3rd Floor"),
                    ("Med-Surg Ward 4B", "IPD", "Building B - 4th Floor"),
                    ("Cardiac Care Unit", "IPD", "Building A - 2nd Floor"),
                    ("Pediatric Ward", "IPD", "Building C - 1st Floor"),
                    ("Emergency Department", "Emergency", "Building A - Ground Floor"),
                ]
                for name, dtype, loc in dept_list:
                    existing_d = session.query(models.Department).filter(models.Department.name == name).first()
                    if not existing_d:
                        dept = models.Department(
                            facility_id=facility.id,
                            name=name,
                            department_type=dtype,
                            location=loc,
                            status="active"
                        )
                        session.add(dept)
                session.commit()

            existing_beds = session.query(models.Bed).count()
            if existing_beds == 0:
                icu_dept = session.query(models.Department).filter(models.Department.name.like("%ICU%")).first()
                med_dept = session.query(models.Department).filter(models.Department.name.like("%Med-Surg%")).first()
                car_dept = session.query(models.Department).filter(models.Department.name.like("%Cardiac%")).first()
                ped_dept = session.query(models.Department).filter(models.Department.name.like("%Pediatric%")).first()

                dept_map = [
                    (icu_dept, "ICU", 20),
                    (med_dept, "MED", 40),
                    (car_dept, "CAR", 16),
                    (ped_dept, "PED", 24),
                ]
                for dept_obj, prefix, count in dept_map:
                    if not dept_obj:
                        continue
                    for i in range(1, count + 1):
                        bed_code = f"{prefix}-{i:02d}"
                        existing_b = session.query(models.Bed).filter(
                            models.Bed.facility_id == facility.id,
                            models.Bed.bed_number == bed_code
                        ).first()
                        if not existing_b:
                            status = "occupied" if i <= int(count * 0.8) else ("cleaning" if i == int(count * 0.8) + 1 else "available")
                            bed = models.Bed(
                                facility_id=facility.id,
                                department_id=dept_obj.id,
                                bed_number=bed_code,
                                ward=dept_obj.name,
                                status=status
                            )
                            session.add(bed)
                session.commit()
                logger.info("Default hospital facility, departments, and beds seeded.")

            existing_meds = session.query(models.MedicationInventory).count()
            if existing_meds == 0:
                med_items = [
                    ("Atorvastatin", "80mg", "Oral Tablet", "LOT-AT80-991", 500.0, 50.0),
                    ("Aspirin (Enteric-Coated)", "325mg", "Oral Tablet", "LOT-ASA325-102", 1200.0, 100.0),
                    ("Metformin HCl ER", "500mg", "Oral Tablet", "LOT-MET500-442", 800.0, 80.0),
                    ("Ceftriaxone", "1g", "IV Solution", "LOT-CEF1G-003", 150.0, 20.0),
                    ("Levofloxacin", "750mg", "IV Piggyback", "LOT-LEVO750-811", 100.0, 15.0),
                    ("Albuterol Sulfate", "2.5mg/3mL", "Inhalation Solution", "LOT-ALB25-560", 300.0, 30.0),
                    ("Furosemide", "40mg/4mL", "IV Injection", "LOT-FUR40-771", 250.0, 25.0),
                    ("Heparin Sodium", "5000 units/mL", "IV Vial", "LOT-HEP5K-302", 200.0, 25.0),
                    ("Insulin Lispro (Humalog)", "100 units/mL", "Subcutaneous Vial", "LOT-INS100-994", 180.0, 20.0),
                ]
                for mname, mstr, mform, mbatch, mqty, mreord in med_items:
                    med = models.MedicationInventory(
                        facility_id=facility.id,
                        medication_name=mname,
                        strength=mstr,
                        form=mform,
                        batch_number=mbatch,
                        quantity_on_hand=mqty,
                        reorder_level=mreord,
                        status="active"
                    )
                    session.add(med)
                session.commit()

            existing_patients = session.query(models.User).filter(models.User.role == "patient").count()
            if existing_patients == 0:
                # Find or create a default doctor user
                doctor = session.query(models.User).filter(models.User.role == "doctor").first()
                if not doctor:
                    doctor = models.User(
                        username="dr_smith",
                        hashed_password=auth.get_password_hash("Doctor123!"),
                        email="dr.smith@hospital.local",
                        role="doctor",
                        full_name="Dr. Sarah Smith, MD",
                        facility_id=facility.id,
                        specialization="Internal Medicine",
                        allow_data_collection=0
                    )
                    session.add(doctor)
                    session.commit()
                    session.refresh(doctor)

                demo_patients = [
                    ("sarah_jenkins", "Sarah Jenkins", "sarah@patient.local", 28, "F", 72.0, 120.0, 80.0, 98.0, 36.8, "ICU", "ICU-01"),
                    ("marcus_thorne", "Marcus Thorne", "marcus@patient.local", 54, "M", 118.0, 145.0, 95.0, 94.0, 38.2, "CAR", "CAR-01"),
                    ("linda_zhao", "Linda Zhao", "linda@patient.local", 42, "F", 64.0, 115.0, 75.0, 99.0, 36.7, "MED", "MED-01"),
                    ("robert_g", "Robert Garcia", "robert@patient.local", 61, "M", 85.0, 132.0, 84.0, 97.0, 37.0, "MED", "MED-02"),
                    ("emily_watson", "Emily Watson", "emily@patient.local", 19, "F", 68.0, 112.0, 68.0, 98.0, 36.6, "PED", "PED-01"),
                    ("oscar_meyer", "Oscar Meyer", "oscar@patient.local", 67, "M", 76.0, 128.0, 82.0, 96.0, 36.9, "ICU", "ICU-02"),
                ]

                for uname, fname, email, age, gender, hr, sbp, dbp, spo2, temp, dept_pref, bed_num in demo_patients:
                    puser = models.User(
                        username=uname,
                        hashed_password=auth.get_password_hash("Patient123!"),
                        email=email,
                        role="patient",
                        full_name=fname,
                        facility_id=facility.id,
                        allow_data_collection=0
                    )
                    session.add(puser)
                    session.commit()
                    session.refresh(puser)

                    dept_match = session.query(models.Department).filter(models.Department.name.like(f"%{dept_pref}%")).first()
                    dept_id = dept_match.id if dept_match else 1

                    # Create Encounter
                    encounter = models.Encounter(
                        facility_id=facility.id,
                        patient_id=puser.id,
                        doctor_id=doctor.id,
                        department_id=dept_id,
                        encounter_type="IPD",
                        reason="Inpatient clinical monitoring and diagnostic evaluation",
                        priority="urgent" if hr > 100 or spo2 < 95 else "routine",
                        status="open",
                        started_at=datetime.now(timezone.utc)
                    )
                    session.add(encounter)
                    session.commit()
                    session.refresh(encounter)

                    # Create Vital Observation
                    vital = models.VitalObservation(
                        facility_id=facility.id,
                        patient_id=puser.id,
                        recorded_by_id=doctor.id,
                        encounter_id=encounter.id,
                        department_id=dept_id,
                        source="device",
                        heart_rate=hr,
                        systolic_bp=sbp,
                        diastolic_bp=dbp,
                        spo2=spo2,
                        temperature_c=temp,
                        respiratory_rate=16.0 if hr <= 100 else 24.0,
                        blood_glucose=95.0 if uname != "marcus_thorne" else 145.0,
                        observed_at=datetime.now(timezone.utc)
                    )
                    session.add(vital)

                    # Link bed and create admission
                    bed_match = session.query(models.Bed).filter(
                        models.Bed.facility_id == facility.id,
                        models.Bed.bed_number == bed_num
                    ).first()
                    if bed_match:
                        bed_match.current_patient_id = puser.id
                        bed_match.status = "occupied"

                    admission = models.Admission(
                        facility_id=facility.id,
                        encounter_id=encounter.id,
                        patient_id=puser.id,
                        doctor_id=doctor.id,
                        department_id=dept_id,
                        bed_id=bed_match.id if bed_match else None,
                        reason="Inpatient Care & Telemetry",
                        status="active",
                        admitted_at=datetime.now(timezone.utc)
                    )
                    session.add(admission)

                    # Create Care Event
                    event = models.CareEvent(
                        facility_id=facility.id,
                        patient_id=puser.id,
                        actor_user_id=doctor.id,
                        encounter_id=encounter.id,
                        department_id=dept_id,
                        event_type="ADMISSION",
                        title=f"Inpatient Admission to {dept_pref}",
                        summary=f"Patient admitted with initial vitals: HR {hr} bpm, BP {sbp}/{dbp}, SpO2 {spo2}%.",
                        severity="warning" if hr > 100 or spo2 < 95 else "info",
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(event)

                    # Create Diagnostic Order & Result
                    if uname == "marcus_thorne":
                        order_ecg = models.ClinicalOrder(
                            facility_id=facility.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            order_type="radiology",
                            title="12-Lead Electrocardiogram (ECG)",
                            priority="stat",
                            status="completed",
                            notes="Evaluate ST segment changes in anterior leads V2-V4",
                            completed_at=datetime.now(timezone.utc)
                        )
                        session.add(order_ecg)
                        session.commit()
                        session.refresh(order_ecg)

                        res_ecg = models.DiagnosticResult(
                            facility_id=facility.id,
                            order_id=order_ecg.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            result_type="radiology",
                            title="12-Lead ECG Analysis",
                            summary="Sinus tachycardia at 118 bpm. Acute ST-elevation of 2.5mm in leads V2, V3, V4 with reciprocal ST-depression in II, III, aVF. Consistent with acute anterior STEMI.",
                            abnormal_flag=1,
                            status="final",
                            review_status="reviewed",
                            review_note="Cardiology consulted. Emergency catheterization lab activated.",
                            reviewed_by_id=doctor.id,
                            reviewed_at=datetime.now(timezone.utc)
                        )
                        session.add(res_ecg)

                        order_trop = models.ClinicalOrder(
                            facility_id=facility.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            order_type="lab",
                            title="High-Sensitivity Cardiac Troponin I (hs-cTnI)",
                            priority="stat",
                            status="completed",
                            notes="Serial troponin draw for acute myocardial injury",
                            completed_at=datetime.now(timezone.utc)
                        )
                        session.add(order_trop)
                        session.commit()
                        session.refresh(order_trop)

                        res_trop = models.DiagnosticResult(
                            facility_id=facility.id,
                            order_id=order_trop.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            result_type="lab",
                            title="High-Sensitivity Cardiac Troponin I",
                            summary="Serum hs-cTnI: 1.840 ng/mL [CRITICAL HIGH, Reference: 0.000 - 0.034 ng/mL]. Delta positive vs admission baseline.",
                            abnormal_flag=1,
                            status="final",
                            review_status="reviewed",
                            review_note="Critical value communicated to Attending Cardiologist.",
                            reviewed_by_id=doctor.id,
                            reviewed_at=datetime.now(timezone.utc)
                        )
                        session.add(res_trop)

                    elif uname == "sarah_jenkins":
                        order_cbc = models.ClinicalOrder(
                            facility_id=facility.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            order_type="lab",
                            title="Complete Blood Count with Differential",
                            priority="routine",
                            status="completed",
                            notes="Post-operative 24h surveillance",
                            completed_at=datetime.now(timezone.utc)
                        )
                        session.add(order_cbc)
                        session.commit()
                        session.refresh(order_cbc)

                        res_cbc = models.DiagnosticResult(
                            facility_id=facility.id,
                            order_id=order_cbc.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            result_type="lab",
                            title="Complete Blood Count with Diff",
                            summary="WBC: 7.4 x10^3/mcL, Hemoglobin: 13.2 g/dL, Hematocrit: 39.8%, Platelets: 260 x10^3/mcL, ANC: 4.8 x10^3/mcL. Normal post-surgical profile.",
                            abnormal_flag=0,
                            status="final",
                            review_status="reviewed",
                            review_note="Surgical recovery progressing within expected clinical parameters.",
                            reviewed_by_id=doctor.id,
                            reviewed_at=datetime.now(timezone.utc)
                        )
                        session.add(res_cbc)

                    elif uname == "linda_zhao":
                        order_a1c = models.ClinicalOrder(
                            facility_id=facility.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            order_type="lab",
                            title="Hemoglobin A1c (Glycated Hb) & Glucose Panel",
                            priority="routine",
                            status="completed",
                            notes="Evaluate glycemic control and inpatient insulin titration",
                            completed_at=datetime.now(timezone.utc)
                        )
                        session.add(order_a1c)
                        session.commit()
                        session.refresh(order_a1c)

                        res_a1c = models.DiagnosticResult(
                            facility_id=facility.id,
                            order_id=order_a1c.id,
                            encounter_id=encounter.id,
                            patient_id=puser.id,
                            doctor_id=doctor.id,
                            department_id=dept_id,
                            result_type="lab",
                            title="Hemoglobin A1c & Blood Glucose",
                            summary="HbA1c: 9.2% [HIGH, Target: <7.0%], Fasting Plasma Glucose: 248 mg/dL [HIGH, Reference: 70 - 99 mg/dL]. Serum Ketones: 1.2 mmol/L [MODERATE].",
                            abnormal_flag=1,
                            status="final",
                            review_status="reviewed",
                            review_note="Initiate subcutaneous basal-bolus insulin sliding scale protocol.",
                            reviewed_by_id=doctor.id,
                            reviewed_at=datetime.now(timezone.utc)
                        )
                        session.add(res_a1c)

                    # Seed active prescription
                    presc = models.Prescription(
                        facility_id=facility.id,
                        encounter_id=encounter.id,
                        patient_id=puser.id,
                        doctor_id=doctor.id,
                        diagnosis_context="Acute Coronary Syndrome" if uname == "marcus_thorne" else ("Type 2 Diabetes Mellitus" if uname == "linda_zhao" else "Inpatient Clinical Care"),
                        status="active",
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(presc)
                    session.commit()
                    session.refresh(presc)

                    med_name = "Atorvastatin" if uname == "marcus_thorne" else ("Metformin HCl ER" if uname == "linda_zhao" else "Ceftriaxone")
                    med_dose = "80mg" if uname == "marcus_thorne" else ("500mg" if uname == "linda_zhao" else "1g")
                    med_freq = "Once daily at bedtime" if uname == "marcus_thorne" else ("Twice daily with meals" if uname == "linda_zhao" else "Every 24 hours IV")

                    item = models.PrescriptionItem(
                        prescription_id=presc.id,
                        medication_name=med_name,
                        dosage=med_dose,
                        frequency=med_freq,
                        duration="14 days",
                        quantity_prescribed=14.0,
                        quantity_dispensed=14.0,
                        instructions="Administer with full glass of water. Monitor clinical parameters.",
                        status="dispensed"
                    )
                    session.add(item)

                session.commit()
                logger.info("Demo patient profiles, encounters, vitals, admissions, diagnostic results, and prescriptions seeded successfully.")

            existing_services = session.query(models.BillableService).count()
            if existing_services == 0:
                services_list = [
                    ("SRV-EM-01", "Emergency Department Triage & Acute Resuscitation", "Emergency", 1500.0),
                    ("SRV-ICU-01", "Intensive Care Unit (ICU) Bed & Hemodynamic Monitoring / 24h", "IPD", 8500.0),
                    ("SRV-CAR-01", "Cardiac Care Unit (CCU) Bed & Telemetry Surveillance / 24h", "IPD", 6200.0),
                    ("SRV-MED-01", "Inpatient Med-Surg Room & Skilled Nursing Care / 24h", "IPD", 3200.0),
                    ("SRV-LAB-01", "Comprehensive Metabolic Panel & High-Sensitivity Troponin I", "Diagnostics", 1800.0),
                    ("SRV-RAD-01", "12-Lead Electrocardiogram & Cardiologist Interpretation", "Diagnostics", 950.0),
                    ("SRV-PHARM-01", "Inpatient Clinical Pharmacotherapy & IV Infusion Management", "Pharmacy", 2400.0),
                ]
                for scode, sname, stype, sprice in services_list:
                    srv = models.BillableService(
                        facility_id=facility.id,
                        service_code=scode,
                        name=sname,
                        service_type=stype,
                        unit_price=sprice,
                        status="active"
                    )
                    session.add(srv)
                session.commit()

            existing_claims = session.query(models.InsuranceClaim).count()
            if existing_claims == 0:
                claims_list = [
                    ("CLM-2026-98101", "Marcus Thorne", "Star Health & Allied Insurance", "POL-ST-994821", 42500.0, 3500.0, "approved"),
                    ("CLM-2026-98102", "Sarah Jenkins", "HDFC ERGO Health Insurance", "POL-HE-331094", 28000.0, 2000.0, "submitted"),
                    ("CLM-2026-98103", "Linda Zhao", "Max Bupa Health Insurance", "POL-MB-771203", 18500.0, 1500.0, "in_review"),
                    ("CLM-2026-98104", "Robert Garcia", "Care Health Insurance", "POL-CH-552109", 22000.0, 1800.0, "submitted"),
                ]
                for cnum, pname, payer, pol, camt, copay, cstatus in claims_list:
                    claim = models.InsuranceClaim(
                        claim_number=cnum,
                        patient_name=pname,
                        payer_name=payer,
                        policy_id=pol,
                        claim_amount=camt,
                        copay_amount=copay,
                        status=cstatus
                    )
                    session.add(claim)
                session.commit()

            existing_appts = session.query(models.Appointment).count()
            if existing_appts == 0:
                p_marcus = session.query(models.User).filter(models.User.username == "marcus_thorne").first()
                p_sarah = session.query(models.User).filter(models.User.username == "sarah_jenkins").first()
                doc = session.query(models.User).filter(models.User.role == "doctor").first()
                if doc and p_marcus:
                    appt1 = models.Appointment(
                        facility_id=facility.id,
                        user_id=p_marcus.id,
                        doctor_id=doc.id,
                        specialist="Cardiology",
                        date_time=datetime.now(timezone.utc),
                        reason="Post-STEMI Coronary Angiogram Follow-up",
                        status="Scheduled"
                    )
                    session.add(appt1)
                if doc and p_sarah:
                    appt2 = models.Appointment(
                        facility_id=facility.id,
                        user_id=p_sarah.id,
                        doctor_id=doc.id,
                        specialist="General Surgery",
                        date_time=datetime.now(timezone.utc),
                        reason="Post-Operative Wound & Recovery Check",
                        status="Scheduled"
                    )
                    session.add(appt2)
                session.commit()
                logger.info("Demo billable services, insurance claims, and appointments seeded successfully.")
        except Exception as seed_err:
            session.rollback()
            logger.warning("Hospital operations seeding failed: %s", seed_err)
