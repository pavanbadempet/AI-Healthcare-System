# 06 — Database Design

## Q: What database do you use and why?

**Development**: SQLite — zero configuration, single file, no server needed. Perfect for local dev and demos.

**Production**: PostgreSQL — just change `DATABASE_URL` environment variable. SQLAlchemy abstracts the difference.

```python
# database.py
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")
engine = create_engine(DATABASE_URL)
```

## Q: What is your database schema?

### Users Table
```sql
CREATE TABLE users (
    id          INTEGER PRIMARY KEY,
    username    VARCHAR UNIQUE NOT NULL,
    email       VARCHAR,
    hashed_password VARCHAR NOT NULL,
    full_name   VARCHAR,
    role        VARCHAR DEFAULT 'patient',  -- admin, doctor, patient
    gender      VARCHAR,
    dob         VARCHAR,
    blood_type  VARCHAR,
    height      VARCHAR,
    weight      VARCHAR,
    about_me    TEXT,
    plan_tier   VARCHAR DEFAULT 'free',     -- free, pro, enterprise
    subscription_expiry TIMESTAMP,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Health Records Table
```sql
CREATE TABLE health_records (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id),
    record_type VARCHAR,    -- 'diabetes', 'heart', 'liver', etc.
    data        JSON,       -- Raw input values
    prediction  VARCHAR,    -- 'High Risk', 'Healthy Heart', etc.
    timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Appointments Table
```sql
CREATE TABLE appointments (
    id               INTEGER PRIMARY KEY,
    patient_id       INTEGER REFERENCES users(id),
    doctor_id        INTEGER REFERENCES users(id),
    appointment_date TIMESTAMP,
    status           VARCHAR DEFAULT 'scheduled',
    notes            TEXT
);
```

## Q: How do you handle migrations?

Smart migration on startup — checks before adding:

```python
def run_migrations():
    inspector = inspect(engine)
    existing_columns = {col['name'] for col in inspector.get_columns("users")}
    
    required = {"about_me": "TEXT", "plan_tier": "VARCHAR", ...}
    
    for col_name, col_type in required.items():
        if col_name not in existing_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
```

**Why not Alembic?** For a project this size, the startup migration check is simpler. Alembic would be needed for production with team collaboration.

## Q: How do you handle database sessions?

```python
def get_db():
    db = SessionLocal()
    try:
        yield db       # Provide session to handler
    finally:
        db.close()     # ALWAYS close, even on error

# Used via FastAPI's dependency injection:
@router.get("/records")
def get_records(db: Session = Depends(get_db)):
    return db.query(Record).filter(...).all()
```

**Key guarantee**: Session is ALWAYS closed — prevents connection leaks.

## Q: What is SQLAlchemy and how do you use it?

SQLAlchemy is an **ORM** (Object-Relational Mapper). It maps Python classes to database tables:

```python
# models.py
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)
    hashed_password = Column(String)
    
    records = relationship("HealthRecord", back_populates="user")

class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    record_type = Column(String)
    data = Column(JSON)
    prediction = Column(String)
```

**Benefits:**
- Write Python, not SQL
- Database-agnostic (SQLite ↔ PostgreSQL with zero code changes)
- Prevents SQL injection automatically
- Relationships handled via Python objects
