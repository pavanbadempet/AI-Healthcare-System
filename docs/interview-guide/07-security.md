# 07 — Security & Compliance

> Every security concept in your project explained from scratch with examples.

---

## Q: How do you handle authentication and authorization?

First, understand the difference:
- **Authentication** = WHO are you? (Login with username + password)
- **Authorization** = WHAT can you do? (Admin can see all patients; patient can only see their own records)

### Authentication Flow (Step by Step):

```
Step 1: User enters username + password on the login page
            ↓
Step 2: Frontend sends POST /login with credentials
        Body: username=pavan&password=secret123
        Format: application/x-www-form-urlencoded (this is the OAuth2 spec format,
                not JSON — because OAuth2 standard requires form-encoded login)
            ↓
Step 3: Backend receives the request
        Looks up "pavan" in the database
        Finds: hashed_password = "$2b$12$LJ3qPe7x8Vk9J4..."
            ↓
Step 4: bcrypt.checkpw("secret123", stored_hash)
        bcrypt takes the entered password, applies the SAME salt
        from the stored hash, hashes it, and compares.
        If they match → password is correct
        If not → return 401 Unauthorized
            ↓
Step 5: Create JWT token
        payload = {
            "sub": "pavan",       # Who this token belongs to
            "role": "patient",    # What they can do
            "exp": 1718000000     # When this token expires (24 hours from now)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        # SECRET_KEY = a long random string only the server knows
        # HS256 = HMAC-SHA256 signing algorithm
            ↓
Step 6: Return token to frontend
        {"access_token": "eyJhbGciOiJIUzI1NiJ9.eyJ...", "token_type": "bearer"}
            ↓
Step 7: Frontend stores token in localStorage
        Every future request includes:
        Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJ...
            ↓
Step 8: On every API call, backend middleware:
        a) Extracts the token from Authorization header
        b) Decodes it with SECRET_KEY
        c) Checks if it's expired
        d) Extracts username and role
        e) Now knows WHO is making the request and WHAT they can do
```

### What is JWT? (JSON Web Token)

A JWT is a string with 3 parts separated by dots:

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYXZhbiIsImV4cCI6MTcxOH0.abc123signature
↑ HEADER                ↑ PAYLOAD                              ↑ SIGNATURE

HEADER (base64 encoded):
{
    "alg": "HS256",     # Algorithm used for signing
    "typ": "JWT"        # Token type
}

PAYLOAD (base64 encoded):
{
    "sub": "pavan",     # Subject (who this token is for)
    "role": "patient",  # User's role
    "exp": 1718000000   # Expiry timestamp (Unix epoch)
}

SIGNATURE:
HMAC-SHA256(
    base64(header) + "." + base64(payload),
    SECRET_KEY   # Only the server knows this string
)
```

**Why is the signature important?** If someone intercepts the token and changes "patient" to "admin" in the payload, the signature won't match anymore. The server recalculates the signature using the secret key and compares — if they don't match, the token is rejected. You can't forge a valid token without knowing the SECRET_KEY.

**Why JWT over sessions?**

| Feature | JWT (your project) | Sessions |
|---|---|---|
| Where stored | Client (localStorage) | Server (in memory or database) |
| Server state | Stateless — nothing stored | Stateful — session table |
| Scaling | Easy — any server can verify | Hard — need shared session store |
| Database hit per request | None (just decode token) | Yes (lookup session ID) |
| Revocation | Hard (wait for expiry) | Easy (delete from server) |
| Mobile-friendly | Yes (just send header) | Harder (cookies are complex on mobile) |

**JWT code in your project:**
```python
# backend/auth.py

from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
ALGORITHM = "HS256"

def create_token(username: str, role: str) -> str:
    """Create a JWT token after successful login."""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decode JWT and return the current user. Called on every protected route."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

---

### What is bcrypt? (Password Hashing)

**The problem**: If you store passwords as plain text and your database gets hacked:

```
BAD — plain text passwords:
| username | password    |
|----------|-------------|
| pavan    | secret123   |  ← Hacker reads this directly
| alice    | mypassword  |  ← Every password exposed

GOOD — bcrypt hashed passwords:
| username | hashed_password                                          |
|----------|----------------------------------------------------------|
| pavan    | $2b$12$LJ3qPe7x8Vk9J4nZ1mD5Oe3xYz.KN1aBc2dEf3gH4iJ5kL |
| alice    | $2b$12$Mn5oP1qR2sT3uV4wX5yZ6a7bC8dE9fG0hI1jK2lM3nO4pQ5r |
```

**How bcrypt works (step by step):**

```
1. SIGNUP — User enters password "secret123"
        ↓
2. bcrypt generates a RANDOM SALT: "$2b$12$LJ3qPe7x8Vk9J4nZ1mD5O"
   (Salt = random string added to the password before hashing.
    This means even if two users have the SAME password "secret123",
    their hashes will be DIFFERENT because different salts.)
        ↓
3. bcrypt hashes: hash("secret123" + salt) using Blowfish cipher
   This takes ~100ms ON PURPOSE (see "Why intentionally slow?" below)
        ↓
4. Store in database: "$2b$12$LJ3qPe7x8Vk9J4nZ1mD5Oe3xYz.KN1aBc..."
   The stored string contains: algorithm ($2b) + cost ($12) + salt + hash
        ↓
5. LOGIN — User enters password "secret123" again
        ↓
6. bcrypt extracts the salt from the stored hash
   Re-hashes: hash("secret123" + same_salt)
   Compares: does the new hash match the stored hash?
   If yes → password correct. If no → wrong password.
```

**Why intentionally slow?** At 100ms per hash, an attacker can only try ~10 passwords per second. With a fast hash like MD5 (which takes microseconds), an attacker could try BILLIONS of passwords per second. The slowness IS the security.

```python
# Your code in backend/auth.py:
import bcrypt

# During signup:
password = "secret123"
salt = bcrypt.gensalt()  # Random salt, different each time
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
# Store 'hashed' in the database

# During login:
entered_password = "secret123"
stored_hash = user.hashed_password.encode('utf-8')  # From database

if bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash):
    # Password correct → create JWT token
    token = create_token(user.username, user.role)
    return {"access_token": token}
else:
    raise HTTPException(status_code=401, detail="Incorrect password")
```

---

### Authorization (Role-Based Access Control)

After authentication tells us WHO the user is, authorization determines WHAT they can do:

```python
# Patient can only see THEIR OWN records:
@router.get("/my-records")
def get_my_records(
    current_user: User = Depends(get_current_user),  # Auth check
    db: Session = Depends(get_db)
):
    # Filter by current_user.id — can NEVER see another patient's data
    return db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id
    ).all()

# Admin can see ALL records:
@router.get("/admin/all-records")
def get_all_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(HealthRecord).all()
```

**The key**: A patient calling `/admin/all-records` gets 403 Forbidden. A patient calling `/my-records` only gets THEIR records because the query always filters by `current_user.id`.

---

## Q: How do you prevent common web attacks?

| Attack | What It Is (Simply) | How Your System Prevents It |
|---|---|---|
| **SQL Injection** | Attacker puts SQL code in input fields: `username = "'; DROP TABLE users; --"`. If you build SQL strings with user input, the attacker's SQL executes. | **SQLAlchemy ORM** — NEVER builds SQL strings from user input. All values are parameterized: `WHERE username = ?` (the `?` is filled in safely by the database driver). |
| **XSS (Cross-Site Scripting)** | Attacker injects JavaScript into your page: `<script>steal(cookies)</script>`. If the page renders this, the script runs in every visitor's browser. | **React auto-escapes** — All text rendered via JSX is escaped. `<script>` becomes `&lt;script&gt;` (visible text, not executable code). |
| **CSRF (Cross-Site Request Forgery)** | Attacker tricks your browser into making requests to your API while you're logged in (e.g., a hidden form on an evil site that submits to your `/delete-account` endpoint). Works because browsers auto-attach cookies. | **JWT in headers, not cookies** — Your API doesn't use cookies. The JWT token is sent in the `Authorization` header, which browsers don't auto-attach. A malicious site can't add custom headers to cross-origin requests. |
| **Clickjacking** | Attacker loads your site in an invisible iframe, puts fake buttons on top. User thinks they're clicking "Play Video" but actually clicking "Delete My Account" on your hidden site. | **`X-Frame-Options: DENY`** header — Browsers refuse to load your site in any iframe. The SecurityHeadersMiddleware adds this to every response. |
| **Brute Force** | Attacker tries thousands of password combinations rapidly until one works. | **Rate limiting** — After too many requests from the same IP, further requests are blocked. Also, **bcrypt is slow by design** — each password check takes ~100ms, limiting attacker to ~10 attempts/second. |
| **Information Disclosure** | Attacker triggers an error to see stack traces, file paths, or database queries in the error response. This reveals your tech stack, file structure, and potential vulnerabilities. | **ExceptionMiddleware** catches ALL unhandled errors. Returns a UUID error ID to the user: `{"detail": "Error: a1b2c3d4"}`. The actual stack trace is logged server-side only. No file paths, no SQL queries, no PII in the response. |
| **Password Theft** | Attacker gets database access (SQL injection, backup theft, insider). If passwords are in plain text, every account is compromised. | **bcrypt hashing** — Even with full database access, attacker sees `$2b$12$LJ3q...`, NOT the actual password. The hash is one-way — you cannot reverse it back to the password. |
| **Token Theft** | Attacker intercepts the JWT token (network sniffing, XSS). | **HTTPS in production** encrypts all traffic — tokens can't be intercepted. **24-hour expiry** limits the damage window. **No sensitive data in token** — even if stolen, it only contains username and role, not passwords or health data. |

---

## Q: What is HIPAA and how does your system address it?

**HIPAA** (Health Insurance Portability and Accountability Act) is a US law that says: "If you handle patient health data, you MUST protect it." Violating HIPAA can result in fines up to $1.5 million per incident.

HIPAA has three types of safeguards:

### 1. Technical Safeguards (what your CODE does):

| Requirement | What It Means | Your Implementation |
|---|---|---|
| Access controls | Only authorized people can access data | JWT + role-based auth: patients see only their records |
| Audit trail | Log who accessed what and when | LoggingMiddleware logs every request with timestamp and user ID |
| Encryption in transit | Data encrypted while traveling over the network | HTTPS in production (TLS certificate) |
| Encryption at rest | Data encrypted while stored | PostgreSQL encryption (Neon manages this) |
| Automatic logoff | Sessions expire after inactivity | JWT tokens expire after 24 hours |
| Unique user identification | Each user has a unique identity | Username + hashed password, unique user ID |

### 2. Administrative Safeguards (NOT in your code, but know about them):
- Employee training on data handling
- Designated privacy officer
- Regular risk assessments
- Business associate agreements with third parties (like Neon for database)

### 3. Physical Safeguards (NOT in your code):
- Locked server rooms
- Screen locks on workstations
- Secure disposal of hardware

**Your honest answer in an interview:**
> "My system implements the technical safeguards: JWT auth with role-based access control, bcrypt password hashing, HTTPS encryption, audit logging, and PII protection in error messages. Full HIPAA compliance also requires administrative and physical safeguards — staff training, risk assessments, and third-party audits — which are organizational, not code. I'm aware of the full picture, but my focus was on building the technical foundation."

---

## Q: How do you handle PII (Personally Identifiable Information)?

**PII** = Any data that can identify a specific person. In healthcare: names, dates of birth, health conditions, medical history.

**Your rules (from AGENTS.md):**
> "Never log or expose PII in error messages or debug output."

```python
# BAD — PII in error log (HIPAA violation):
logger.error(f"Failed prediction for {user.full_name}, DOB: {user.dob}, "
             f"health data: {patient_data}")
# If logs are compromised, attacker sees: "John Smith, DOB: 1980-05-15, BMI: 35"

# GOOD — generic error with tracking ID:
error_id = str(uuid.uuid4())[:8]  # Generate: "a1b2c3d4"
logger.error(f"Prediction error [{error_id}]: model={disease_type}, "
             f"user_id={user.id}")
# Log shows: "Prediction error [a1b2c3d4]: model=diabetes, user_id=42"
# No name, no DOB, no health data. Use error_id to find details in secure logs.

# Return to user:
return JSONResponse(
    status_code=500,
    content={"detail": f"Internal error. Reference: {error_id}"}
)
# User sees: "Internal error. Reference: a1b2c3d4"
# They can report this ID to support. Support can look up the secure server log.
```

**Where PII protection is enforced:**

| Location | Protection |
|---|---|
| API error responses | UUID error ID, never stack traces |
| Server logs | User ID only, never names/DOB/health data |
| AI chat responses | Medical disclaimers required |
| Database | Passwords bcrypt-hashed, health data access-controlled |
| Frontend | React auto-escapes, no PII in URL parameters |
| Git repository | `.env` file in `.gitignore`, secrets never committed |

---

## Q: What are your 7 middleware layers?

**Middleware** = Code that runs BEFORE your route handler processes a request and AFTER it sends a response. Like security checkpoints at an airport — every request passes through all of them.

```
                                    Request arrives from client
                                              ↓
Layer 1: CORS Middleware
         "Is this request coming from an ALLOWED origin?"
         Your frontend (localhost:3000) is allowed.
         A random malicious site (evil.com) is blocked.
         CORS = Cross-Origin Resource Sharing.
                                              ↓
Layer 2: Rate Limiting Middleware
         "Has this IP made too many requests recently?"
         If yes → 429 Too Many Requests (blocks brute force attacks)
         If no → let it through
                                              ↓
Layer 3: TrustedHost Middleware
         "Is the Host header a trusted domain?"
         Allows: localhost, 127.0.0.1, your-app.render.com
         Blocks: Host header attacks where attacker sets Host to evil.com
                                              ↓
Layer 4: Security Headers Middleware
         Adds defensive headers to EVERY response:
         X-Frame-Options: DENY          (prevent clickjacking)
         X-Content-Type-Options: nosniff (prevent MIME sniffing)
         X-XSS-Protection: 1           (legacy XSS filter)
                                              ↓
Layer 5: Exception Middleware
         Wraps everything in try/catch.
         If ANY unhandled error occurs anywhere:
         → Log the full stack trace server-side
         → Return generic error with UUID to client
         → NEVER expose internal details to the user
                                              ↓
Layer 6: Request ID Middleware
         Generates a UUID for this request: "req-a1b2c3d4"
         Attaches it to logs, headers, and error messages.
         If user reports a bug: "I got error a1b2c3d4"
         You can search logs for exactly that request.
                                              ↓
Layer 7: Timing Middleware
         Records: start_time = now()
         After response: elapsed = now() - start_time
         Adds header: X-Process-Time: 0.009
         Logs: "GET /predict/diabetes completed in 9ms"
         This is how you know prediction takes ~9ms.
                                              ↓
                                    YOUR ROUTE HANDLER
                                    (predict_diabetes, login, etc.)
                                              ↓
                                    Response goes back through
                                    all layers in reverse order
                                              ↓
                                    Client receives response
```
