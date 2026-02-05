from backend import database, models, auth

def seed_doctor():
    db = database.SessionLocal()
    try:
        # Check if doctor exists
        if db.query(models.User).filter(models.User.role == "doctor").first():
            print("Doctor already exists.")
            return

        # Create Dr. Smith
        hashed_pw = auth.get_password_hash("doctor123")
        doctor = models.User(
            username="dr_smith",
            hashed_password=hashed_pw,
            email="dr.smith@hospital.com",
            full_name="Dr. Adam Smith",
            role="doctor",
            consultation_fee=150.0,
            specialization="General Physician", # Note: Schema might not have this column yet based on previous migration check
            profile_picture="https://i.pravatar.cc/150?u=dr_smith",
            dob="1980-01-01",
            allow_data_collection=1
        )
        db.add(doctor)
        db.commit()
        print("✅ Created Doctor: Dr. Adam Smith (user: dr_smith, pass: doctor123)")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_doctor()
