# 06 — Database Design (Complete Deep-Dive)

> Everything about the database layer — schema, ORM, sessions, migrations, queries.

---

## Q: What database do you use and why?

### Development: SQLite
- **Zero configuration** — `pip install` and it works. No database server to install.
- **Single file** — entire database is `healthcare.db`. Easy to delete and recreate.
- **Fast for reads** — perfect for single-user development.
- **Limitation** — single writer at a time (no concurrent writes).

### Production: PostgreSQL
- **Concurrent writes** — multiple users can write simultaneously.
- **Connection pooling** — handles 100+ concurrent connections.
- **ACID compliance** — full transactional integrity for patient data.
- **Just change one environment variable:**
  ```bash
  # Development (default)
  DATABASE_URL=sqlite:///./healthcare.db
  
  # Production (Neon managed PostgreSQL)
  DATABASE_URL=postgresql://user:pass@ep-cool-name.neon.tech/healthcare
  ```

### How the switch works (zero code changes):

```python
# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This ONE line reads the env variable — same code for SQLite and PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")

# SQLAlchemy handles the difference internally
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

---

## Q: Show me the complete database schema with all fields.

### Users Table (the core entity):

```python
# backend/models.py

class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, index=True)
    hashed_password = Column(String, nullable=False)  # bcrypt hash, NEVER plaintext
    
    # Profile
    full_name = Column(String, default="")
    role = Column(String, default="patient")  # "admin" | "doctor" | "patient"
    gender = Column(String, default="")
    dob = Column(String, default="")          # Date of birth
    blood_type = Column(String, default="")   # A+, B-, O+, etc.
    height = Column(String, default="")       # In cm or feet
    weight = Column(String, default="")       # In kg or lbs
    about_me = Column(String, default="")     # Free text bio
    
    # Subscription (tiered access)
    plan_tier = Column(String, default="free")        # "free" | "pro" | "enterprise"
    subscription_expiry = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    records = relationship("HealthRecord", back_populates="owner")
```

**Why these fields?**
- `hashed_password`: bcrypt with salt — even if database is stolen, passwords are safe
- `role`: Role-based access control — admin sees all, patient sees only their own
- `plan_tier`: Subscription tiers for premium features (not enforced yet)
- `index=True` on username/email: Database creates B-tree index → O(log n) lookups instead of O(n) full scan

### Health Records Table:

```python
class HealthRecord(Base):
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    record_type = Column(String)    # "diabetes" | "heart" | "liver" | "kidney" | "lungs"
    data = Column(JSON)             # Raw input values: {"bmi": 35, "age": 55, ...}
    prediction = Column(String)     # "High Risk" | "Healthy Heart" | etc.
    confidence = Column(Float)      # 94.2 (percentage)
    risk_level = Column(String)     # "High" | "Moderate" | "Low"
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to user
    owner = relationship("User", back_populates="records")
```

**Why JSON column for `data`?**
- Each disease has different input fields (diabetes: 9 features, kidney: 24 features)
- JSON column stores any shape of data without schema changes
- Alternative: separate table per disease — more normalized but more complex

### Appointments Table:

```python
class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    
    appointment_date = Column(DateTime)
    status = Column(String, default="scheduled")  # "scheduled" | "completed" | "cancelled"
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Q: How do you handle database sessions? Explain dependency injection.

### The Session Lifecycle:

```python
# backend/database.py

def get_db():
    """Yield a database session, guaranteed to close even on error."""
    db = SessionLocal()
    try:
        yield db       # Provide session to the route handler
    finally:
        db.close()     # ALWAYS close — prevents connection leaks
```

### How It's Used in Route Handlers:

```python
# backend/auth.py

from fastapi import Depends
from sqlalchemy.orm import Session

@router.post("/signup")
def signup(
    username: str,
    password: str,
    db: Session = Depends(get_db)  # FastAPI auto-calls get_db()
):
    # Check if user exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username taken")
    
    # Create user
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user = User(username=username, hashed_password=hashed.decode())
    db.add(user)
    db.commit()          # Save to database
    db.refresh(user)     # Reload with generated ID
    
    return {"id": user.id, "username": user.username}
    # After return → finally block closes the session
```

### Why Dependency Injection?

```python
# WITHOUT DI (bad — session leak risk):
@router.get("/records")
def get_records():
    db = SessionLocal()
    records = db.query(Record).all()
    db.close()  # What if the query throws an error? Session LEAKS!
    return records

# WITH DI (good — guaranteed cleanup):
@router.get("/records")
def get_records(db: Session = Depends(get_db)):
    return db.query(Record).all()
    # Session auto-closes via finally block, even on error
```

**Benefits:**
1. **No session leaks** — `finally` guarantees cleanup
2. **Testable** — override `get_db` with a test database in tests
3. **DRY** — don't write session open/close in every handler
4. **FastAPI auto-handles** — just declare `db: Session = Depends(get_db)`

---

## Q: How do you handle database migrations?

### Smart Migration on Startup:

```python
# backend/database.py

def run_migrations():
    """Check and add missing columns on startup.
    This is called during FastAPI lifespan, before any requests."""
    
    inspector = inspect(engine)
    
    # Check if tables exist at all
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
        return
    
    # Check for missing columns
    existing_columns = {col['name'] for col in inspector.get_columns("users")}
    
    required_columns = {
        "about_me": "TEXT DEFAULT ''",
        "plan_tier": "VARCHAR DEFAULT 'free'",
        "subscription_expiry": "TIMESTAMP",
        "gender": "VARCHAR DEFAULT ''",
        "dob": "VARCHAR DEFAULT ''",
        "blood_type": "VARCHAR DEFAULT ''",
        "height": "VARCHAR DEFAULT ''",
        "weight": "VARCHAR DEFAULT ''",
    }
    
    with engine.connect() as conn:
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                logger.info(f"Added column: users.{col_name}")
        conn.commit()
```

### Why Not Alembic?

| | Our Approach | Alembic |
|---|---|---|
| Complexity | ~30 lines of code | Full migration framework |
| Files | Zero migration files | Migration scripts per change |
| Team collaboration | Simple (one dev) | Essential (multiple devs) |
| Rollback | Manual | Built-in `alembic downgrade` |
| Production use | OK for small projects | Required for large teams |

**Decision**: For this project size, startup migration is simpler. I'd switch to Alembic for a team project with multiple developers and production deployments.

---

## Q: Show me example database queries from the actual app.

### Get user's health records with filtering:
```python
@router.get("/records")
def get_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    record_type: str = None,
    limit: int = 50
):
    query = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id  # Only own records
    )
    
    if record_type:
        query = query.filter(HealthRecord.record_type == record_type)
    
    return query.order_by(HealthRecord.timestamp.desc()).limit(limit).all()
```

### Admin: Get all users with record counts:
```python
@router.get("/admin/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(
        User.id,
        User.username,
        User.role,
        func.count(HealthRecord.id).label("record_count")
    ).outerjoin(HealthRecord).group_by(User.id).all()
    
    return [{"id": u.id, "username": u.username, "role": u.role, 
             "records": u.record_count} for u in users]
```

### Save prediction result:
```python
def save_prediction(db: Session, user_id: int, disease: str, 
                     data: dict, prediction: str, confidence: float):
    record = HealthRecord(
        user_id=user_id,
        record_type=disease,
        data=data,           # JSON: {"bmi": 35, "age": 55, ...}
        prediction=prediction,  # "High Risk"
        confidence=confidence,  # 94.2
        risk_level="High" if confidence >= 75 else "Moderate" if confidence >= 40 else "Low"
    )
    db.add(record)
    db.commit()
    return record
```

---

## Q: What is SQLAlchemy and how does it prevent SQL injection?

### ORM = Object-Relational Mapping

```python
# WITHOUT ORM (raw SQL — vulnerable to injection):
username = request.form["username"]
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
# If username = "admin'; DROP TABLE users; --" → DATABASE DESTROYED

# WITH SQLAlchemy ORM (safe):
user = db.query(User).filter(User.username == username).first()
# SQLAlchemy parameterizes: SELECT * FROM users WHERE username = ?
# The username value is NEVER concatenated into the SQL string
```

### How SQLAlchemy Works Under the Hood:

```python
# Python ORM code:
db.query(User).filter(User.role == "admin").order_by(User.created_at.desc()).limit(10)

# Translates to SQL:
SELECT * FROM users WHERE role = 'admin' ORDER BY created_at DESC LIMIT 10

# The translation happens via Dialect:
# SQLite dialect → SQLite SQL
# PostgreSQL dialect → PostgreSQL SQL
# Same Python code → different SQL based on DATABASE_URL
```

---

## Q: How would you migrate from SQLite to PostgreSQL in production?

### Step-by-step:

```bash
# 1. Set up PostgreSQL (e.g., on Neon.tech)
# Get connection string: postgresql://user:pass@host/dbname

# 2. Set environment variable
export DATABASE_URL="postgresql://user:pass@ep-cool.neon.tech/healthcare"

# 3. Start the app — it auto-creates tables and runs migrations
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 4. Migrate existing data (if needed)
python scripts/migrate_sqlite_to_postgres.py
```

### Migration script:
```python
import sqlite3
import psycopg2

# Read from SQLite
sqlite_conn = sqlite3.connect("healthcare.db")
users = sqlite_conn.execute("SELECT * FROM users").fetchall()

# Write to PostgreSQL
pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
for user in users:
    pg_conn.execute("INSERT INTO users VALUES (%s, %s, ...)", user)
pg_conn.commit()
```

**What changes**: Nothing in the application code. Only the `DATABASE_URL` environment variable. SQLAlchemy handles all dialect differences internally.
