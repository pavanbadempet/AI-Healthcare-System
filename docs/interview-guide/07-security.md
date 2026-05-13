# 07 — Security & Compliance

## Q: How do you handle authentication and authorization?

### Authentication (WHO are you?)
- **OAuth2 with JWT** — Industry standard
- Login sends `username + password` as `application/x-www-form-urlencoded` (OAuth2 spec)
- Backend verifies with **bcrypt** (one-way hash + salt)
- Returns **JWT token** (HS256 signed, contains user_id + role + expiry)
- Token sent in `Authorization: Bearer <token>` header on every request

### Authorization (WHAT can you do?)
- **Role-based**: `admin`, `doctor`, `patient`
- Admin endpoints check `user.role == "admin"`
- Patients can only access their own records: `Record.user_id == current_user.id`
- Doctors can view assigned patients

## Q: How do you prevent common web attacks?

| Attack | Prevention |
|---|---|
| **SQL Injection** | SQLAlchemy ORM — never raw SQL with user input |
| **XSS** | React auto-escapes all rendered content |
| **CSRF** | API uses JWT tokens in headers, not cookies |
| **Clickjacking** | `X-Frame-Options: DENY` header |
| **MIME Sniffing** | `X-Content-Type-Options: nosniff` header |
| **Brute Force** | Rate limiting middleware |
| **Host Header Injection** | TrustedHostMiddleware whitelist |
| **Information Disclosure** | Error responses contain UUID, never stack traces |
| **Password Theft** | bcrypt hashing (one-way, with salt) |
| **Token Theft** | JWT expiry, HTTPS in production |

## Q: What is HIPAA and how does your system address it?

**HIPAA** = Health Insurance Portability and Accountability Act — US law governing health data privacy.

| HIPAA Requirement | Our Implementation |
|---|---|
| Access controls | Role-based auth (admin/doctor/patient) |
| Audit trail | LoggingMiddleware logs every request |
| Data encryption in transit | HTTPS in production |
| Minimum necessary | Only collect needed health metrics |
| Patient rights | Users can view/delete their own records |
| Security incident response | Error IDs for tracking, no PII in logs |
| Medical disclaimers | Every AI output includes disclaimer |

**Honest caveat**: Full HIPAA compliance requires organizational policies, staff training, and third-party audits — not just code. My system implements the **technical safeguards**, but organizational and administrative safeguards would need to be added for a real deployment.

## Q: How do you handle PII (Personally Identifiable Information)?

**Rules from AGENTS.md:**
- Never log patient names, DOBs, or health data in error messages
- Error responses contain UUID error IDs, not details
- Database passwords are bcrypt-hashed
- AI responses always include medical disclaimers

```python
# BAD — exposes PII in logs:
logger.error(f"Failed for patient {user.full_name}, DOB: {user.dob}")

# GOOD — generic error with tracking ID:
error_id = str(uuid.uuid4())[:8]
logger.error(f"Error {error_id}: prediction failed")
return {"detail": f"Error: {error_id}"}
```

## Q: How does bcrypt work?

```python
import bcrypt

# HASHING (during signup):
password = "admin123"
salt = bcrypt.gensalt()                    # Random salt
hashed = bcrypt.hashpw(password.encode(), salt)
# Result: $2b$12$LJ3H... (includes algorithm + cost + salt + hash)

# VERIFICATION (during login):
bcrypt.checkpw("admin123".encode(), stored_hash)  # True
bcrypt.checkpw("wrong".encode(), stored_hash)     # False
```

**Why bcrypt?**
- One-way: Can't reverse hash to get password
- Salted: Same password produces different hashes
- Cost factor: Intentionally slow — makes brute force expensive
- Industry standard for password storage

## Q: How does JWT work?

```python
# Token creation:
payload = {
    "sub": "admin",        # Subject (username)
    "role": "admin",       # Role
    "exp": datetime.utcnow() + timedelta(hours=24)  # Expiry
}
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
# Result: eyJhbGciOiJI...  (3 parts: header.payload.signature)

# Token verification:
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
username = payload["sub"]  # "admin"
```

**Why JWT over sessions?**
- **Stateless**: Server doesn't store session data
- **Scalable**: Works across multiple server instances
- **Self-contained**: Token carries all needed info
- **No database lookup**: Just decode and verify signature
