from backend import database, models, auth
import sys

def seed_data():
    print("Starting database seeding...")
    db = database.SessionLocal()
    try:
        # --- SEED ADMIN ---
        admin = db.query(models.User).filter(models.User.role == "admin").first()
        if not admin:
            print("Creating Admin user...")
            hashed_pw = auth.get_password_hash("admin123")
            admin_user = models.User(
                username="admin", 
                hashed_password=hashed_pw,
                email="admin@hospital.com",
                full_name="System Administrator",
                role="admin",
                allow_data_collection=0,
                dob="1980-01-01" # Ensure DOB is present if schema requires it
            )
            db.add(admin_user)
            print("Admin created: admin / admin123")
        else:
            print("Admin already exists.")

        # --- SEED DOCTOR ---
        doctor = db.query(models.User).filter(models.User.role == "doctor").first()
        if not doctor:
            print("Creating Doctor user...")
            hashed_pw = auth.get_password_hash("doctor123")
            doctor_user = models.User(
                username="dr_smith",
                hashed_password=hashed_pw,
                email="dr.smith@hospital.com",
                full_name="Dr. Adam Smith",
                role="doctor",
                # consultation_fee=150.0, # Commenting out as column might not exist yet (migration script handles it but maybe not run yet)
                # specialization="General Physician",
                profile_picture="https://i.pravatar.cc/150?u=dr_smith",
                dob="1975-05-20",
                allow_data_collection=1
            )
            # handle potential missing columns by checking getattr or just try/except
            # For now, let's assume the basic User model works and add extras if columns exist
            # The 'run_migrations' in main.py should have added them, but let's be safe.
            try:
                doctor_user.consultation_fee = 150.0
                doctor_user.specialization = "General Physician"
            except:
                pass

            db.add(doctor_user)
            print("Doctor created: dr_smith / doctor123")
        else:
            print("Doctor already exists.")
            
        db.commit()
        print("Seeding complete!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
