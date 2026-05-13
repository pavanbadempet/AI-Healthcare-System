# Chapter 1 - Foundations: Every Concept Explained From Scratch

> This file explains EVERY technical term used in your projects from absolute zero.
> Read this FIRST before anything else. If you understand everything here, you can explain anything in an interview.

---

## PART 1: MACHINE LEARNING FUNDAMENTALS

### What is Machine Learning?

Instead of writing explicit rules ("if BMI > 30 AND age > 50 â†' diabetes risk"), you give the computer EXAMPLES and let it figure out the rules itself.

```
Traditional Programming:    Rules + Data â†' Answer
Machine Learning:           Data + Answers â†' Rules (model)
```

**Example from your project:**
- You have 253,680 patient records
- Each record has 9 health measurements (BMI, age, blood pressure, etc.)
- Each record is labeled: 0 = healthy, 1 = diabetic
- XGBoost looks at all 253K examples and learns: "when BMI > 32 AND blood pressure is high AND age > 45... the patient tends to be diabetic"
- Now when a NEW patient enters their health data, the model predicts: "87% chance of diabetes"

---

### What is Classification?

Classification = the model predicts a CATEGORY, not a number.

```
Binary Classification (your project):
    Input: {BMI: 35, age: 55, blood_pressure: 1, ...}
    Output: "Diabetic" or "Not Diabetic"  (two categories)

Multi-class Classification:
    Input: {image pixels}
    Output: "Cat" or "Dog" or "Bird"  (three+ categories)

Regression (NOT your project):
    Input: {bedrooms: 3, sqft: 1500, ...}
    Output: $425,000  (a number, not a category)
```

Your project does BINARY CLASSIFICATION â€" every model predicts one of two outcomes: sick or healthy.

---

### What is a Training Set vs Test Set?

```
253,680 patient records
    â"œâ"€â"€ 80% â†' Training Set (202,944 records)
    â"‚         The model LEARNS from these
    â"‚
    â""â"€â"€ 20% â†' Test Set (50,736 records)
              The model is TESTED on these
              It has NEVER seen these before
```

**Why split?** If you test the model on the SAME data it trained on, it just memorizes the answers. That's like giving a student the exam answers during practice and testing them with the same exam â€" of course they'll score 100%, but they haven't actually learned anything.

**Real example from your code:**
```python
# backend/train_diabetes.py
from sklearn.model_selection import train_test_split

X = data[feature_columns]   # The health measurements (inputs)
y = data["Diabetes_binary"]  # The diagnosis (output: 0 or 1)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2,      # 20% for testing
    random_state=42      # Same split every time (reproducible)
)
```

---

### What is Class Imbalance? (THE KEY CONCEPT)

**The problem**: In your diabetes dataset, most people are healthy. Very few have diabetes.

```
253,680 total records
â"œâ"€â"€ 218,334 records (86.1%) â†' Label 0 = HEALTHY     â-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-ˆâ-'
â""â"€â"€  35,346 records (13.9%) â†' Label 1 = DIABETIC    â-ˆâ-ˆâ-ˆâ-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'â-'
```

**Ratio**: 218,334 / 35,346 = **6.16 healthy people for every 1 diabetic person**

### Why is this a problem?

Imagine you build a model that ALWAYS predicts "Healthy" for every single person. What's its accuracy?

```
Total: 253,680
Correct predictions: 218,334 (it said "healthy" and they ARE healthy)
Wrong predictions: 35,346 (it said "healthy" but they have diabetes)

Accuracy = 218,334 / 253,680 = 86.1%

86.1% accuracy... but it MISSED EVERY SINGLE DIABETIC PATIENT!
```

**86.1% accuracy sounds great, but the model is completely useless.** It never catches the disease. It's like a smoke detector that never goes off â€" great for avoiding false alarms, catastrophic for actual fires.

This is the **accuracy paradox** â€" high accuracy can be meaningless when classes are imbalanced.

### How the Model Gets Fooled by Imbalance

During training, the model learns from examples. When it sees 6 healthy people for every 1 diabetic person, it learns:

```
"If I just predict HEALTHY every time, I'm right 86% of the time!"
```

The model is LAZY. It takes the shortcut. Predicting "healthy" is almost always correct, so why bother learning the complex patterns that distinguish diabetic patients?

---

### What is scale_pos_weight? (THE FIX)

`scale_pos_weight` tells XGBoost: **"Getting a diabetic patient wrong is 6.16x worse than getting a healthy patient wrong."**

```python
# Without scale_pos_weight:
model = XGBClassifier()
# Model thinks: healthy wrong = -1 penalty, diabetic wrong = -1 penalty
# So it plays it safe: predict healthy always

# With scale_pos_weight:
model = XGBClassifier(scale_pos_weight=6.16)
# Model thinks: healthy wrong = -1 penalty, diabetic wrong = -6.16 penalty!
# Now missing a diabetic patient is VERY costly
# So the model MUST learn to catch diabetic patients
```

**How the number 6.16 is calculated:**
```python
# It's just the ratio of healthy to sick
negative_count = 218334   # Healthy (class 0 = "negative")
positive_count = 35346    # Diabetic (class 1 = "positive")

scale_pos_weight = negative_count / positive_count
# scale_pos_weight = 218334 / 35346 = 6.16

# For heart disease: 9.61 (even more imbalanced)
# For kidney disease: calculated similarly
```

**Analogy**: Imagine you're training a security guard. Without scale_pos_weight, every mistake costs $1 â€" whether they let a thief in or turn away a legitimate visitor. With scale_pos_weight=6.16, letting a thief in costs $6.16 but turning away a visitor costs $1. Now the guard will be MUCH more careful about letting potential thieves in, even if it means occasionally stopping a legitimate visitor.

---

### What is XGBoost? (Explained Simply)

XGBoost = **eXtreme Gradient Boosting**. Let's break that down:

**Boosting** = Train many small, weak models (decision trees) one after another. Each new tree focuses on fixing the mistakes of the previous trees.

```
Tree 1: Makes predictions. Gets 70% right.
         Identifies which patients it got WRONG.
             â†"
Tree 2: Focuses specifically on the patients Tree 1 got wrong.
         Combined accuracy: 78%.
             â†"
Tree 3: Focuses on the remaining mistakes.
         Combined accuracy: 83%.
             â†"
... (100-1000 trees later)
             â†"
Final: All trees vote together. Combined accuracy: 89%.
```

**Gradient** = The mathematical technique used to figure out "how wrong was I?" and "how should the next tree adjust?" It uses calculus (gradients) to minimize the error function.

**eXtreme** = It's a very optimized, fast, production-grade implementation with extra features like:
- Regularization (prevents overfitting)
- scale_pos_weight (handles class imbalance)
- Missing value handling (automatically routes missing values)
- Parallel tree construction (uses all CPU cores)

### Why XGBoost Over Other Options?

| Algorithm | Strengths | Weaknesses | For Your Data? |
|---|---|---|---|
| **XGBoost** | Fast, handles imbalance natively (scale_pos_weight), works great on tabular data | Needs hyperparameter tuning | **YES â€" primary choice** |
| **Random Forest** | Simple, hard to overfit | No native imbalance handling, slower | Close second, but no scale_pos_weight |
| **Logistic Regression** | Simple, interpretable | Can't capture complex non-linear patterns | Too simple for 9+ features |
| **Neural Networks** | Best for images/text/huge datasets | Overfits on 253K tabular data, needs much more data, hard to interpret | **NO â€" proven worse on tabular data** |
| **SVM** | Good for small datasets, clear decision boundary | Slow on large datasets, sensitive to scaling | Used for kidney/lungs (smaller datasets) |

**The research backing**: The Grinsztajn et al. (2022) NeurIPS benchmark paper compared tree-based models (XGBoost, Random Forest) vs deep learning on 45 tabular datasets. Result: **tree-based models won on medium-sized tabular data** like yours.

---

### What is predict_proba? (How Confidence Works)

When the model predicts, it doesn't just say "Diabetic" or "Not Diabetic." It gives a PROBABILITY.

```python
model.predict([patient_data])
# Returns: [1]  â† Just "Diabetic" (not useful alone)

model.predict_proba([patient_data])
# Returns: [[0.06, 0.94]]
#            â†'       â†'
#         6% chance  94% chance
#         healthy    diabetic
```

**How this probability becomes a confidence score:**
```python
# Your code in backend/prediction.py:
probabilities = model.predict_proba(features)
# probabilities = [[0.06, 0.94]]

positive_probability = probabilities[0][1]  # 0.94 (chance of disease)
confidence = positive_probability * 100      # 94.0%

# Determine risk level
if confidence >= 75:
    risk_level = "High"
elif confidence >= 40:
    risk_level = "Moderate"
else:
    risk_level = "Low"
```

**What the user sees:**
```json
{
    "prediction": "Diabetes Risk Detected",
    "confidence": 94.2,
    "risk_level": "High",
    "medical_disclaimer": "This is AI-generated... consult a healthcare professional."
}
```

---

### What is Overfitting vs Underfitting?

```
UNDERFITTING:                     GOOD FIT:                       OVERFITTING:
Model is too simple.              Model captures real patterns.   Model memorized training data.
Can't even learn training data.   Works on new data too.          Fails on new data.

Training accuracy: 60%            Training accuracy: 89%          Training accuracy: 99%
Test accuracy: 58%                Test accuracy: 85%              Test accuracy: 65%
        â†"                                 â†"                               â†"
   "I don't know enough"          "I learned the real patterns"   "I memorized, not learned"
```

**In your project:**
- Training accuracy: ~89%
- Test accuracy: ~85-89%
- Real-world validation: 77% (48 actual patient records)
- The gap is small â†' Good fit, no overfitting

**How XGBoost prevents overfitting:**
```python
model = XGBClassifier(
    max_depth=6,           # Trees can't grow too deep (limits complexity)
    n_estimators=100,      # Only 100 trees (not 10,000)
    learning_rate=0.1,     # Each tree only contributes a little (cautious learning)
    reg_alpha=0.5,         # L1 regularization (penalizes complexity)
    reg_lambda=1.0,        # L2 regularization (penalizes complexity)
    scale_pos_weight=6.16, # Class imbalance fix
    random_state=42        # Reproducibility
)
```

---

### What are Accuracy, Precision, Recall, Sensitivity, Specificity?

Let's say 100 patients come in. 20 actually have diabetes, 80 don't.

```
Model predictions:
                        ACTUALLY Diabetic    ACTUALLY Healthy
Predicted Diabetic         15 (TP)              5 (FP)
Predicted Healthy           5 (FN)             75 (TN)

TP = True Positive: Model said diabetic, IS diabetic (correct catch)
FP = False Positive: Model said diabetic, is actually healthy (false alarm)
FN = False Negative: Model said healthy, actually HAS diabetes (MISSED!)
TN = True Negative: Model said healthy, IS healthy (correct pass)
```

**Now the metrics:**

```
Accuracy = (TP + TN) / Total = (15 + 75) / 100 = 90%
    "How often is the model correct overall?"

Precision = TP / (TP + FP) = 15 / (15 + 5) = 75%
    "When the model says 'diabetic,' how often is it right?"
    (Important for: avoiding unnecessary panic)

Recall = Sensitivity = TP / (TP + FN) = 15 / (15 + 5) = 75%
    "Of all actual diabetic patients, how many did the model catch?"
    (Important for: NOT MISSING sick patients â€" THIS IS CRITICAL IN HEALTHCARE)

Specificity = TN / (TN + FP) = 75 / (75 + 5) = 93.75%
    "Of all healthy patients, how many did the model correctly identify as healthy?"

F1 Score = 2 * (Precision * Recall) / (Precision + Recall) = 75%
    "Harmonic mean of precision and recall â€" balances both"
```

**In healthcare, RECALL (Sensitivity) is the most important metric.** Missing a diabetic patient (FN) is much worse than a false alarm (FP). A false alarm means one extra doctor visit. A missed diagnosis means untreated disease.

**That's exactly why scale_pos_weight matters** â€" it pushes the model toward higher recall by penalizing missed positives.

---

## PART 2: DATA ENGINEERING FUNDAMENTALS

### What is ETL? (Extract, Transform, Load)

```
EXTRACT                    TRANSFORM                       LOAD
Get raw data               Clean and reshape it            Put it somewhere useful
â"€â"€â"€â"€â"€â"€â"€â"€â"€                  â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€              â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
Download CSV from CDC  â†'   Rename columns            â†'     Save as Parquet file
                          Handle missing values              â†"
                          Convert types                  Train ML model
                          Feature engineering                â†"
                          Split train/test              Save as .pkl file
                                                           â†"
                                                       Load at API startup
```

**Your Healthcare ETL:**
```
CDC BRFSS CSV (raw, 253K rows, messy column names)
    â†" EXTRACT
Read into Pandas DataFrame
    â†" TRANSFORM
    â"œâ"€â"€ Rename: "HighBP" â†' "hypertension"
    â"œâ"€â"€ Rename: "HighChol" â†' "high_chol"
    â"œâ"€â"€ Convert: age codes â†' age buckets (1-13)
    â"œâ"€â"€ Drop: irrelevant columns
    â"œâ"€â"€ Handle: missing values (fill or drop)
    â""â"€â"€ Split: 80% train, 20% test
    â†" LOAD
    â"œâ"€â"€ Train XGBoost model
    â"œâ"€â"€ Save model to diabetes_model.pkl
    â""â"€â"€ Load model in FastAPI at startup
```

### What is ELT? (And How It Differs)

```
ETL: Extract â†' Transform â†' Load
     Transform happens OUTSIDE the target (in Spark, Python, etc.)
     Used when: transformation is complex, target is simple storage

ELT: Extract â†' Load â†' Transform
     Transform happens INSIDE the target (in Snowflake, BigQuery, etc.)
     Used when: target has powerful compute
```

**Your Nissan project used ELT:**
```
Raw CSV files â†' Load into Snowflake â†' Transform using Snowflake SQL
```

---

### What is Parquet? (And Why Not CSV?)

```
CSV (row-based):
id,name,age,bmi,diagnosis
1,John,55,35.2,1
2,Jane,42,28.1,0
3,Bob,67,31.5,1
... (253,680 rows)

File size: ~25 MB
Read speed: Slow (reads EVERY column even if you only need "age")
Types: None (everything is string, must parse)
```

```
Parquet (column-based):
Stores data by COLUMN, not by row:
Column "id":   [1, 2, 3, ...]
Column "age":  [55, 42, 67, ...]
Column "bmi":  [35.2, 28.1, 31.5, ...]
Column "diagnosis": [1, 0, 1, ...]

File size: ~3 MB (compressed!)
Read speed: Fast (reads ONLY the columns you need)
Types: Embedded (int64, float64, string â€" no parsing needed)
Statistics: Min/max per column chunk â†' skip irrelevant data
```

**Why your project uses Parquet:**
```python
# Reading CSV: reads ALL columns, parses all types (slow)
df = pd.read_csv("data.csv")  # 2.5 seconds

# Reading Parquet: reads only needed columns, types pre-parsed (fast)
df = pd.read_parquet("data.parquet", columns=["age", "bmi"])  # 0.1 seconds
```

---

### What is an API? What is REST? What is FastAPI?

**API (Application Programming Interface)** = A way for programs to talk to each other.

```
Your Frontend (React)  â†â†'  Your Backend (FastAPI)  â†â†'  Your Database (SQLite)

The frontend doesn't talk to the database directly.
It sends HTTP requests to the API, which talks to the database.
```

**REST** = A set of rules for designing APIs:
```
GET    /api/patients/123     â†' Read patient 123
POST   /api/predictions      â†' Create a new prediction
PUT    /api/patients/123     â†' Update patient 123
DELETE /api/patients/123     â†' Delete patient 123
```

**FastAPI** = A Python framework for building APIs:
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/predict/diabetes")
async def predict_diabetes(bmi: float, age: int, blood_pressure: int):
    # Load model, run prediction, return result
    prediction = model.predict([[bmi, age, blood_pressure]])
    return {"prediction": "High Risk" if prediction[0] == 1 else "Low Risk"}
```

**Why FastAPI over Flask/Django?**
| | FastAPI | Flask | Django |
|---|---|---|---|
| Speed | Fastest (async) | Medium | Slowest |
| Type checking | Built-in (Pydantic) | Manual | Manual |
| Auto docs | Swagger UI auto-generated | None | None |
| Async | Native | Add-on | Add-on |
| Learning curve | Easy | Easy | Hard |

---

### What is JWT? (JSON Web Token)

**The problem**: After a user logs in, how does the server know they're logged in on future requests? The server is stateless â€" it doesn't remember anything between requests.

**The solution**: Give the user a signed token they include in every request.

```
1. User logs in:
   POST /login {username: "pavan", password: "secret123"}
       â†"
   Server verifies password (bcrypt compare)
       â†"
   Server creates JWT token:
   eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYXZhbiIsImV4cCI6MTcxOH0.abc123
   â†'                      â†'                                      â†'
   Header (algorithm)      Payload (user info + expiry)           Signature
       â†"
   Returns token to frontend

2. Frontend stores token in localStorage

3. Every future request includes the token:
   GET /api/my-records
   Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
       â†"
   Server decodes token â†' extracts username â†' knows who's asking
       â†"
   Returns ONLY that user's records
```

**The token contains:**
```json
{
    "sub": "pavan",           // Username
    "exp": 1718000000,        // Expires at (Unix timestamp)
    "role": "patient"         // User role
}
```

**Why is it secure?** The signature is created using a SECRET_KEY that only the server knows. If anyone tampers with the payload (e.g., changes "patient" to "admin"), the signature won't match and the server rejects it.

---

### What is bcrypt? (Password Hashing)

**The problem**: If you store passwords as plain text and your database gets hacked, every password is exposed.

```
BAD: users table
| username | password    |
|----------|-------------|
| pavan    | secret123   |  â† Hacker sees the actual password!
| alice    | mypassword  |
```

**bcrypt** converts passwords into irreversible hashes:

```
GOOD: users table
| username | hashed_password                                    |
|----------|----------------------------------------------------|
| pavan    | $2b$12$LJ3qPe7x8Vk9J4nZ1mD5Oe3xYz.KN1aBc2dEf3gH4 |
| alice    | $2b$12$Mn5oP1qR2sT3uV4wX5yZ6a7bC8dE9fG0hI1jK2lM3n |
```

**Key properties:**
1. **One-way**: You CANNOT reverse the hash back to the password
2. **Salted**: Even if two users have the same password, their hashes are different
3. **Slow on purpose**: Takes ~100ms to hash â€" prevents brute-force attacks (attackers can only try ~10 passwords/second instead of millions)

```python
import bcrypt

# Registration: hash the password
password = "secret123"
salt = bcrypt.gensalt()  # Random salt
hashed = bcrypt.hashpw(password.encode(), salt)
# hashed = b'$2b$12$LJ3qPe7x8Vk9J4nZ...'

# Login: compare the password
entered_password = "secret123"
if bcrypt.checkpw(entered_password.encode(), hashed):
    print("Password correct!")  # âœ"
else:
    print("Wrong password!")
```

---

## PART 3: SYSTEM DESIGN CONCEPTS

### What is Middleware?

Middleware = code that runs BEFORE and AFTER every request, like airport security checkpoints.

```
Client Request
    â†"
[Middleware 1: CORS]          "Are you allowed to call this API?"
    â†"
[Middleware 2: Rate Limit]    "Have you made too many requests?"
    â†"
[Middleware 3: TrustedHost]   "Are you calling from a trusted domain?"
    â†"
[Middleware 4: Security]      "Let me add security headers to the response"
    â†"
[Middleware 5: Exception]     "If anything crashes, I'll catch it safely"
    â†"
[Middleware 6: Request ID]    "Let me give this request a tracking UUID"
    â†"
[Middleware 7: Timing]        "Let me measure how long this takes"
    â†"
YOUR ACTUAL ROUTE HANDLER    "Process the request"
    â†"
[Back through middleware in reverse order]
    â†"
Client Response (with security headers, timing info, etc.)
```

**Example: CORS middleware (Cross-Origin Resource Sharing)**

```
Your frontend: http://localhost:3000
Your backend:  http://127.0.0.1:8000

Problem: Browser blocks requests between different origins (port 3000 â‰  port 8000)
Solution: CORS middleware tells the browser "yes, localhost:3000 is allowed to call me"
```

### What is Dependency Injection?

Instead of a function CREATING what it needs, it RECEIVES what it needs from outside.

```python
# WITHOUT Dependency Injection (bad):
def get_records():
    db = Database.connect()  # Function creates its own database connection
    records = db.query("SELECT * FROM records")
    db.close()
    return records
# Problem: Can't test without a real database. Can't swap database implementations.

# WITH Dependency Injection (good):
def get_records(db: Session = Depends(get_db)):
    return db.query(Record).all()
# The database session is INJECTED from outside
# In tests: inject a test database
# In production: inject the real database
# The function doesn't care which one it gets
```

---

## PART 4: FRONTEND CONCEPTS

### What is SSE? (Server-Sent Events)

Normally, HTTP is request-response: client asks, server answers, connection closes.

SSE keeps the connection OPEN so the server can push data continuously:

```
Normal HTTP:
Client: "Give me the AI response"
Server: [waits 5 seconds to generate full response]
Server: "Here's the complete 500-word response" (all at once)

SSE (your project):
Client: "Give me the AI response"
Server: "For"          (50ms later)
Server: " diabetes"   (100ms later)
Server: " management" (150ms later)
Server: ","           (200ms later)
Server: " I"          (250ms later)
Server: " recommend"  (300ms later)
... (tokens appear one by one, like ChatGPT typing)
```

**User experience**: The response appears to "type itself" in real-time, instead of showing a blank screen for 5 seconds then dumping all text at once.

### What is Zustand? (State Management)

**The problem**: In a React app, different components need to share data. Without state management:

```
LoginPage component knows the user is logged in
    â†"
How does the NavBar component know? Pass as props?
    â†"
How does the PredictionForm know? Pass through 5 levels of components?
    â†"
This is called "prop drilling" â€" passing data through components that don't need it
```

**Zustand creates a global store** that any component can read/write:

```typescript
// Create store (one place)
const useAuthStore = create((set) => ({
    user: null,
    token: null,
    login: (user, token) => set({ user, token }),
    logout: () => set({ user: null, token: null }),
}));

// NavBar reads from store (no props needed)
function NavBar() {
    const user = useAuthStore(state => state.user);
    return <div>Welcome, {user?.name}</div>;
}

// LoginPage writes to store
function LoginPage() {
    const login = useAuthStore(state => state.login);
    // After successful API login:
    login(userData, token);
}
```

---

## PART 5: YOUR PROJECT NUMBERS (MEMORIZE THESE)

| Number | What It Means | Where It Comes From |
|---|---|---|
| 253,680 | Training records for diabetes | BRFSS 2015 CDC dataset |
| 86.1% | Healthy patients in diabetes data | 218,334 / 253,680 |
| 13.9% | Diabetic patients | 35,346 / 253,680 |
| 6.16 | scale_pos_weight for diabetes | 218,334 / 35,346 |
| 9.61 | scale_pos_weight for heart disease | Even more imbalanced |
| 5 | Number of disease models | Diabetes, heart, kidney, liver, lungs |
| 9 features | Diabetes model input | BMI, age, blood pressure, etc. |
| 24 features | Kidney model input | Most features of any model |
| ~9ms | Prediction latency | Model inference time |
| 141 | Unit tests passing | pytest test suite |
| 28 | Integration tests passing | API endpoint tests |
| 48 | Real-world validation records | Actual patient data tested |
| 77% | Real-world accuracy | 37/48 matched ground truth |
| 7 | Middleware layers | CORS, rate limit, host, security, exception, request ID, timing |
| 21 | Frontend routes | Next.js App Router pages |
| 1M+ | Movie records (Nova project) | TMDB/Kaggle dataset |
| 50K+ | Movies in serving catalog (Nova) | After quality filtering |
| 30% | Spark optimization (TCS) | 45 min â†' 31 min |
| 60% | Manual effort reduction (Nissan) | Automated with Lambda |
| 25% | Intervention reduction (AutoSys) | Automated dependency chains |
| 2+ years | Professional experience | TCS, Nov 2023 â€" Present |


---


## One-Line Definitions

| Term | Definition |
|---|---|
| **FastAPI** | Async Python web framework with automatic docs and Pydantic validation |
| **Next.js** | React framework with server-side rendering, file-based routing, Turbopack |
| **XGBoost** | Gradient-boosted decision tree algorithm â€" best for tabular data |
| **SVM** | Support Vector Machine â€" finds optimal boundary, good for small datasets |
| **Random Forest** | Ensemble of decision trees â€" reduces overfitting via bagging |
| **JWT** | JSON Web Token â€" stateless auth token (header.payload.signature) |
| **bcrypt** | One-way password hashing with salt â€" industry standard |
| **OAuth2** | Authentication framework â€" we use Password grant + Bearer tokens |
| **CORS** | Cross-Origin Resource Sharing â€" controls which domains call your API |
| **SSE** | Server-Sent Events â€" server pushes data to client over HTTP |
| **WebSocket** | Full-duplex bidirectional communication â€" more complex than SSE |
| **RAG** | Retrieval-Augmented Generation â€" inject relevant docs into AI prompts |
| **Pydantic** | Data validation library using Python type hints |
| **SQLAlchemy** | Python ORM â€" maps classes to database tables |
| **Zustand** | Lightweight React state management (alternative to Redux) |
| **Framer Motion** | React animation library for smooth transitions |
| **scale_pos_weight** | XGBoost parameter â€" weights minority class to handle imbalance |
| **predict_proba** | Returns class probabilities instead of binary 0/1 |
| **StandardScaler** | Normalizes features to mean=0, std=1 (required for SVM) |
| **Parquet** | Columnar file format â€" 10x faster reads than CSV |
| **Uvicorn** | ASGI server that runs FastAPI applications |
| **ASGI** | Async Server Gateway Interface â€" Python's async web standard |
| **Middleware** | Code that runs between request and response (auth, logging, etc.) |
| **Dependency Injection** | FastAPI auto-provides function args (db sessions, auth) |
| **Lifespan** | FastAPI startup/shutdown hook for loading models |
| **ORM** | Object-Relational Mapping â€" write Python, not SQL |
| **HIPAA** | US law governing health data privacy and security |
| **PII** | Personally Identifiable Information â€" names, DOBs, health data |
| **Sensitivity** | True positive rate â€" % of sick patients correctly identified |
| **Specificity** | True negative rate â€" % of healthy patients correctly identified |

---

## Key Numbers to Remember

| Metric | Value |
|---|---|
| Total datasets | 5 |
| Largest dataset | 253,680 records (BRFSS) |
| Total training records | ~538K |
| Frontend routes | 21 |
| Backend modules | 40+ |
| Unit tests | 141 |
| Integration checks | 28 |
| Real-world validation | 48 records, 77% accuracy |
| Model total size | ~1.6 MB |
| API response time | ~9ms per prediction |
| Middleware layers | 7 |
| Class imbalance ratio | Up to 9.6:1 (heart) |

---

## Architecture Summary (30-second version)

```
Next.js Frontend (21 routes, Zustand auth, Framer Motion animations)
        â†* HTTP + SSE
FastAPI Backend (7 middleware layers, JWT auth, Pydantic validation)
        â†*
3 services:
  1. ML Prediction (5 XGBoost/SVM models â†' confidence + risk + disclaimer)
  2. AI Chat (RAG + Gemini â†' SSE streaming)
  3. Data (SQLAlchemy + SQLite/PostgreSQL)
```

---

## When Asked "Why X over Y?"

| Question | Answer Template |
|---|---|
| Why Next.js over React? | App Router layouts, SSR, file routing, Turbopack |
| Why FastAPI over Flask? | Async, auto-docs, Pydantic, 10x faster |
| Why FastAPI over Django? | Django too heavy for REST API â€" don't need admin/templates |
| Why XGBoost over neural nets? | Tabular data, handles imbalance, fast training |
| Why SVM over XGBoost (kidney/lungs)? | Small datasets â€" SVM generalizes better |
| Why JWT over sessions? | Stateless, scalable, no server-side storage |
| Why SSE over WebSocket? | Unidirectional streaming, simpler, auto-reconnect |
| Why Zustand over Redux? | Less boilerplate, sufficient for auth state |
| Why SQLite over PostgreSQL? | Zero-config dev, switch via env var for prod |
| Why CSS vars over Tailwind config? | Runtime theme control, works with animations |
| Why pickle over ONNX? | Simpler, Python-only deployment, small models |
| Why monolith over microservices? | Single app is simpler at this scale |

---

## Common Follow-up Answers

**"What's your biggest achievement?"**
â†' Fixing class imbalance: one parameter (`scale_pos_weight=6.16`) took disease detection from 0% to ~60%.

**"What's your biggest failure?"**
â†' Initially shipped with 86.7% accuracy thinking it was great, only to discover it detected zero diseases. Taught me that accuracy alone is meaningless.

**"How do you handle deadlines?"**
â†' I prioritize: get core prediction working first, then add auth, then frontend polish, then tests. Each phase is independently deployable.

**"How do you learn new technologies?"**
â†' I build. This project forced me to learn FastAPI, Next.js App Router, XGBoost tuning, SSE streaming, and RAG â€" all by implementing them in a real system.


---


> Every concept a DE interviewer expects you to know, with clear explanations and examples.

---

## DATA PIPELINE FUNDAMENTALS

### Q: What is idempotency and why does it matter?

**Idempotent** = Running the same operation multiple times produces the same result.

```python
# NOT idempotent â€" appends duplicates:
df.write.mode("append").parquet("output/")
# Run twice â†' 2x data!

# Idempotent â€" safe to re-run:
df.write.mode("overwrite").parquet("output/partition_date=2024-06-15/")
# Run twice â†' same result

# Even better â€" DELETE + INSERT pattern:
DELETE FROM target WHERE batch_date = '2024-06-15';
INSERT INTO target SELECT * FROM staging WHERE batch_date = '2024-06-15';
# Run twice â†' same result
```

**Why it matters**: Pipelines WILL fail. When you re-run them, you must not create duplicates. At Nissan, every pipeline I built was idempotent.

---

### Q: What is a data lake vs data warehouse vs data lakehouse?

| | Data Lake | Data Warehouse | Data Lakehouse |
|---|---|---|---|
| Storage | Raw files (S3, HDFS) | Structured tables | Files + table metadata |
| Format | Any (CSV, JSON, Parquet) | Columnar (proprietary) | Parquet + Delta/Iceberg |
| Schema | Schema-on-read | Schema-on-write | Both |
| ACID | No | Yes | Yes (via Delta Lake) |
| Query speed | Slow (full scan) | Fast (indexed) | Fast (partition pruning) |
| Cost | Cheap (just storage) | Expensive (compute + storage) | Medium |
| Example | S3 bucket of CSVs | Snowflake, Redshift | Delta Lake, Apache Iceberg |
| In my work | Healthcare raw data | Nissan â†' Snowflake | Nova â†' Delta Lake |

---

### Q: What is the medallion architecture (Bronze/Silver/Gold)?

I implemented this in Nova:

```
BRONZE (Raw)          SILVER (Validated)      GOLD (Curated)
â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€          â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€      â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
Raw CSV ingestion     Schema validation       Business metrics
No transforms        Null handling            Feature engineering
Append-only           Deduplication           SCD Type 2 history
Full fidelity         Type casting             Aggregates
Source timestamps     Quarantine bad rows      Ready for ML/reporting
```

**Why 3 layers?**
- Bronze = "we never lose raw data"
- Silver = "data is clean and trustworthy"  
- Gold = "data is ready for business use"

If something breaks in Gold, you rebuild from Silver. If Silver is wrong, you rebuild from Bronze. You NEVER re-extract from source.

---

### Q: What is SCD Type 2?

**Slowly Changing Dimension Type 2** â€" Track history of dimension changes.

```sql
-- Without SCD: We lose history
UPDATE movies SET rating = 8.8 WHERE id = 123;
-- Old rating (8.5) is gone forever!

-- With SCD Type 2: We keep history
INSERT INTO dim_movies VALUES (123, 'Inception', 8.8, '2024-06-15', NULL, true);
UPDATE dim_movies SET valid_to = '2024-06-15', is_current = false 
    WHERE id = 123 AND is_current = true;

-- Now we can query: "What was the rating on January 1st?"
SELECT rating FROM dim_movies 
WHERE id = 123 AND '2024-01-01' BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31');
-- Returns: 8.5 (the old value)
```

I used SCD Type 2 in Nova's `gold.dim_movie_scd` table to track how movie metadata changes over time.

---

### Q: What is Change Data Capture (CDC)?

CDC captures only the CHANGES (inserts, updates, deletes) from a source system instead of full snapshots.

**Methods:**
1. **Log-based**: Read database transaction log (WAL in PostgreSQL, binlog in MySQL)
2. **Timestamp-based**: Query `WHERE modified_at > last_run` (what I used at Nissan)
3. **Trigger-based**: Database triggers write changes to a staging table
4. **Delta Lake CDF**: Delta Lake's Change Data Feed tracks row-level changes automatically

**My usage**: 
- Nissan: Timestamp-based incremental processing
- Nova: Delta Lake Change Data Feed for tracking catalog changes

---

## DISTRIBUTED SYSTEMS CONCEPTS

### Q: What is the CAP theorem?

**C**onsistency â€" Every read returns the latest write
**A**vailability â€" Every request gets a response
**P**artition tolerance â€" System works despite network failures

**You can only have 2 of 3:**

| System | Choice | Trade-off |
|---|---|---|
| PostgreSQL | CP | Consistent, but single node = not always available |
| Cassandra | AP | Always available, but reads might be stale |
| MongoDB | CP (default) | Consistent reads, but writes pause during elections |

**In my projects:**
- Healthcare (SQLite/PostgreSQL): CP â€" consistency matters for patient data
- Nova (Delta Lake): CP â€" ACID writes ensure data integrity

---

### Q: What is eventual consistency?

> "If no new updates are made, eventually all reads will return the same value."

Example: After writing to S3, a read might return the old file for a few seconds. Eventually it sees the new file.

**Where I deal with this:**
- S3 has strong read-after-write consistency (since 2020)
- FAISS index reload: Old index serves until new one is fully loaded
- Behavior features in Nova: Refreshed every 60 seconds (TTL-based)

---

### Q: What is sharding?

Splitting a database across multiple servers by a key:

```
Shard 1: customer_id 1-1000
Shard 2: customer_id 1001-2000
Shard 3: customer_id 2001-3000
```

**Spark's equivalent**: Partitioning. Data is split across executors by partition key.

**Snowflake's equivalent**: Micro-partitions. Data is automatically clustered and pruned.

---

## FILE FORMAT KNOWLEDGE

### Q: Compare CSV, JSON, Parquet, Avro, ORC.

| Format | Type | Schema | Compression | Query Speed | Use Case |
|---|---|---|---|---|---|
| CSV | Row | No | None | Slow | Raw data exchange |
| JSON | Row | Self-describing | None | Slow | APIs, config |
| Parquet | Column | Embedded | Snappy/Gzip | Fast | Analytics, ML |
| Avro | Row | Embedded | Snappy | Medium | Streaming, Kafka |
| ORC | Column | Embedded | Zlib | Fast | Hive ecosystem |
| Delta | Column | Managed | Snappy | Fast | Lakehouse (ACID) |

**Why Parquet?**
- Column-oriented = only read columns you need
- Built-in compression = 10x smaller than CSV
- Row group statistics = predicate pushdown skips irrelevant data
- Schema evolution = add columns without breaking reads

**My usage**: 
- Healthcare: Training data stored as Parquet
- Nova: Delta Lake (which uses Parquet underneath + transaction log)

---

### Q: What is columnar vs row-based storage?

```
ROW-BASED (CSV, MySQL):              COLUMNAR (Parquet, Snowflake):
â"Œâ"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"              â"Œâ"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"
â"‚  id  â"‚ name â"‚ age  â"‚              â"‚ id   â"‚ id   â"‚ id   â"‚
â"‚  1   â"‚ John â"‚  25  â"‚              â"‚  1   â"‚  2   â"‚  3   â"‚
â"‚  2   â"‚ Jane â"‚  30  â"‚              â"œâ"€â"€â"€â"€â"€â"€â"¼â"€â"€â"€â"€â"€â"€â"¼â"€â"€â"€â"€â"€â"€â"¤
â"‚  3   â"‚ Bob  â"‚  35  â"‚              â"‚ name â"‚ name â"‚ name â"‚
â""â"€â"€â"€â"€â"€â"€â"´â"€â"€â"€â"€â"€â"€â"´â"€â"€â"€â"€â"€â"€â"˜              â"‚ John â"‚ Jane â"‚ Bob  â"‚
                                    â"œâ"€â"€â"€â"€â"€â"€â"¼â"€â"€â"€â"€â"€â"€â"¼â"€â"€â"€â"€â"€â"€â"¤
Row: reads ALL columns              â"‚ age  â"‚ age  â"‚ age  â"‚
Good for: SELECT * WHERE id=1       â"‚  25  â"‚  30  â"‚  35  â"‚
                                    â""â"€â"€â"€â"€â"€â"€â"´â"€â"€â"€â"€â"€â"€â"´â"€â"€â"€â"€â"€â"€â"˜
                                    
                                    Column: reads only needed columns
                                    Good for: SELECT AVG(age) FROM table
```

---

## DATA QUALITY CONCEPTS

### Q: What are the dimensions of data quality?

| Dimension | Meaning | How I Check |
|---|---|---|
| **Completeness** | No missing values | `df.isnull().mean()` |
| **Accuracy** | Values are correct | Range checks, referential integrity |
| **Consistency** | Same data across systems | Cross-system checksums |
| **Timeliness** | Data arrives on time | Pipeline SLA monitoring (CloudWatch) |
| **Uniqueness** | No duplicates | `df.duplicated().sum()` |
| **Validity** | Values match expected format | Schema validation, regex checks |

---

### Q: What is data lineage?

Tracking WHERE data came from and HOW it was transformed:

```
BRFSS_2015.csv (CDC source)
    â†" Extract
data/raw/diabetes.csv
    â†" Column rename (HighBP â†' hypertension)
data/processed/diabetes.parquet
    â†" Train/test split, class balancing
diabetes_model.pkl
    â†" predict_proba()
API response: {"prediction": "High Risk", "confidence": 94.2}
```

In Nova, the `pipeline_manifest.json` tracks:
- Run ID, run date
- Source file checksums
- Row counts at each stage
- Quality metrics
- Serving contract (expected vs actual artifact sizes)

---

## STREAMING CONCEPTS

### Q: What is the difference between batch and streaming?

| | Batch | Streaming |
|---|---|---|
| Latency | Minutes to hours | Seconds to minutes |
| Processing | Bounded dataset | Unbounded stream |
| State | Stateless (each run independent) | Stateful (maintain windows) |
| Tools | Spark (batch), Airflow | Kafka, Spark Structured Streaming, Flink |
| Cost | Cheaper | More expensive |
| Use case | Daily reports, model training | Real-time alerts, live dashboards |

**My usage:**
- Batch: Healthcare model training, Nova catalog ETL
- Streaming: Nova behavior events (Kafka â†' Spark Structured Streaming â†' Delta)

### Q: What is Kafka and how does it work?

```
Producer â†' Topic (partitioned) â†' Consumer Group
```

- **Producer**: Sends messages (events) to a topic
- **Topic**: Ordered log of messages, split into partitions
- **Partition**: Unit of parallelism. Messages within a partition are ordered.
- **Consumer Group**: Multiple consumers reading from different partitions in parallel
- **Offset**: Position in the partition. Consumer tracks where it left off.

**In Nova:**
```
Frontend (click/view event) â†' Kafka topic: nova.content_events â†' 
    Spark Structured Streaming â†' gold.fact_content_event (Delta table)
```

### Q: What is exactly-once semantics?

Three delivery guarantees:
- **At-most-once**: Fire and forget. Messages might be lost.
- **At-least-once**: Retry until confirmed. Messages might be duplicated.
- **Exactly-once**: Each message processed exactly once. No loss, no duplication.

**How to achieve exactly-once:**
- Kafka: Idempotent producers + transactional consumers
- Spark Structured Streaming: Checkpointing + WAL
- Application level: Idempotent writes (what I do â€" safe to re-process)

---

## ORCHESTRATION

### Q: Compare Airflow, AutoSys, Step Functions, Prefect.

| | Airflow | AutoSys | Step Functions | Prefect |
|---|---|---|---|---|
| Type | Open-source | Enterprise | Serverless | Open-source |
| DAG definition | Python | JIL files | JSON/YAML | Python |
| Hosting | Self-managed/Cloud | Vendor-managed | AWS-managed | Cloud |
| Cost | Free (+ infra) | Expensive license | Per-execution | Free tier |
| Strengths | Flexible, extensible | Enterprise compliance | Serverless, visual | Modern Python API |
| Weaknesses | Complex setup | Old UI, limited | AWS-only | Newer, smaller community |
| My experience | Project knowledge | Nomura (daily) | Nissan (daily) | Aware |


---


> Interviewers LOVE asking "Why X over Y?" Here's every comparison you need.

---

## DATABASES

### Snowflake vs Redshift vs BigQuery vs Databricks SQL

| | Snowflake | Redshift | BigQuery | Databricks SQL |
|---|---|---|---|---|
| Cloud | Multi-cloud | AWS only | GCP only | Multi-cloud |
| Architecture | Separated compute/storage | Shared-nothing cluster | Serverless | Lakehouse (Delta) |
| Scaling | Auto, per-query | Manual cluster resize | Auto | Auto |
| Cost model | Per-second compute | Per-hour cluster | Per-query scan | Per-DBU |
| Concurrency | Excellent (virtual warehouses) | Limited (cluster-bound) | Excellent | Good |
| Semi-structured | VARIANT column (JSON) | Limited | STRUCT/ARRAY | Good |
| My experience | **Nissan project** | Aware | Aware | Aware |

**When asked "Why did you use Snowflake at Nissan?"**
> "Snowflake separated compute from storage â€" we could scale down warehouses at night (saving cost) and scale up during batch windows. Its COPY INTO command made S3 â†' Snowflake loading simple. The VARIANT type handled our semi-structured data without pre-flattening."

---

### PostgreSQL vs MySQL vs MongoDB

| | PostgreSQL | MySQL | MongoDB |
|---|---|---|---|
| Type | Relational | Relational | Document (NoSQL) |
| ACID | Full | Full | Configurable |
| JSON support | JSONB (excellent) | Basic | Native |
| Scalability | Vertical (+read replicas) | Vertical | Horizontal (sharding) |
| Use case | Complex queries, analytics | Web apps, simple CRUD | Flexible schema, high write |
| My usage | Healthcare (production DB) | Aware | Aware |

---

## DATA PROCESSING

### Spark vs Pandas vs Polars vs Dask

| | Spark | Pandas | Polars | Dask |
|---|---|---|---|---|
| Scale | TB+ (distributed) | GB (single machine) | GB+ (single, fast) | TB (distributed) |
| Language | Python/Scala/SQL | Python | Python/Rust | Python |
| Execution | Lazy (DAG) | Eager | Lazy | Lazy |
| Memory | Cluster-distributed | In-memory | In-memory (efficient) | Out-of-core |
| Use case | Production ETL | Prototyping, small data | Medium data, speed | Pandas-like distributed |
| My usage | **Nomura (daily)** | **Both projects** | Aware | Aware |

**When asked "When do you use Spark vs Pandas?"**
> "Pandas for anything under ~5GB that fits in RAM â€" fast prototyping, data exploration, simple transforms. Spark for anything bigger, anything that needs to scale, or anything that runs in production with reliability requirements. At Nomura, all production ETL was Spark. For local data exploration and testing, I used Pandas."

---

### Spark RDD vs DataFrame vs Dataset

| | RDD | DataFrame | Dataset |
|---|---|---|---|
| Type safety | Compile-time (Scala) | Runtime | Compile-time (Scala) |
| Optimization | No Catalyst | Catalyst + Tungsten | Catalyst + Tungsten |
| API | Functional (map/filter) | SQL-like | Typed SQL-like |
| Performance | Slowest | Fast | Fast |
| My usage | Rarely | **Daily at Nomura** | Aware (Scala) |

> "I use DataFrames exclusively. RDDs are lower-level and miss Catalyst optimizations. Datasets are Scala-only. DataFrames give the best balance of performance, readability, and Spark SQL integration."

---

## ORCHESTRATION

### Airflow vs Prefect vs Dagster vs Step Functions

| | Airflow | Prefect | Dagster | Step Functions |
|---|---|---|---|---|
| Language | Python | Python | Python | JSON/YAML |
| Hosting | Self or MWAA | Cloud | Cloud/self | AWS managed |
| DAG definition | Python decorators | Python decorators | Python + assets | State machine JSON |
| UI | Good | Modern | Excellent | AWS Console |
| Strengths | Mature, huge community | Modern, easy to use | Asset-oriented | Serverless, no infra |
| Weaknesses | Complex setup | Newer | Steeper learning curve | AWS only |
| My experience | Project knowledge | Aware | Aware | **Nissan (daily)** |

---

## STREAMING

### Kafka vs RabbitMQ vs AWS SQS vs AWS Kinesis

| | Kafka | RabbitMQ | SQS | Kinesis |
|---|---|---|---|---|
| Model | Log (pull) | Queue (push) | Queue (pull) | Stream (pull) |
| Ordering | Per-partition | FIFO queue | FIFO option | Per-shard |
| Retention | Days-weeks | Until consumed | 14 days max | 7 days default |
| Throughput | 1M+ msg/sec | 10K msg/sec | Unlimited | 1MB/sec/shard |
| Replay | Yes (offset) | No | No | Yes (iterator) |
| Use case | Event streaming, CDC | Task queues | Decoupling services | Real-time analytics |
| My experience | **Nova project** | Aware | Aware | Aware |

---

## STORAGE

### S3 vs HDFS vs MinIO vs GCS

| | S3 | HDFS | MinIO | GCS |
|---|---|---|---|---|
| Type | Object store | Distributed FS | Object store | Object store |
| Cloud | AWS | On-prem | On-prem/cloud | GCP |
| Cost | Pay per GB + request | Hardware cost | Free (self-hosted) | Pay per GB |
| Scalability | Unlimited | Cluster-limited | Hardware-limited | Unlimited |
| POSIX | No | Yes | No | No |
| S3 compatible | Yes (native) | No | Yes | Via interop |
| My experience | **Nissan** | **Nomura (before)** | **Nomura (after)** | Healthcare |

---

## DATA FORMATS

### Delta Lake vs Apache Iceberg vs Apache Hudi

| | Delta Lake | Iceberg | Hudi |
|---|---|---|---|
| Developed by | Databricks | Netflix â†' Apache | Uber â†' Apache |
| Storage | Parquet + JSON log | Parquet + metadata | Parquet + timeline |
| ACID | Yes | Yes | Yes |
| Time travel | Yes (version history) | Yes (snapshots) | Yes (timeline) |
| Schema evolution | Yes | Excellent | Yes |
| Merge/Upsert | MERGE INTO | MERGE INTO | Upsert natively |
| Community | Large (Databricks) | Growing fast | Smaller |
| My experience | **Nova project** | Aware | Aware |

**When asked "Why Delta Lake?"**
> "Delta Lake adds ACID transactions to Parquet â€" I can do MERGE operations, time travel, and Change Data Feed. In Nova, I use Delta for the medallion architecture: Bronze (raw ingest with ACID), Silver (validated with MERGE), Gold (curated with SCD Type 2). The transaction log prevents corrupt partial writes."

---

## CONTAINERIZATION

### Docker vs Kubernetes vs Docker Compose

| | Docker | Docker Compose | Kubernetes |
|---|---|---|---|
| What | Single container runtime | Multi-container on one host | Container orchestration at scale |
| Scale | 1 container | Multiple containers, 1 machine | Multiple containers, many machines |
| Networking | Port mapping | Virtual network | Service discovery, load balancing |
| Use case | Development, single service | Local dev, small apps | Production, auto-scaling |
| My experience | **Both projects** | **Nova** | **Nomura (Spark on K8s)** |

---

## QUICK DECISION MATRIX

**When asked "What would you choose for X?"**

| Scenario | Choose | Why |
|---|---|---|
| ETL on 100GB daily | **Spark** | Distributed, handles scale |
| ETL on 1GB daily | **Pandas/Python** | Simpler, no cluster needed |
| Real-time events | **Kafka** | High throughput, replay |
| Task queue | **SQS/RabbitMQ** | Simpler, managed |
| Orchestration (AWS) | **Step Functions** | Serverless, visual |
| Orchestration (general) | **Airflow** | Flexible, community |
| Data warehouse | **Snowflake** | Multi-cloud, auto-scale |
| Lakehouse | **Delta Lake** | ACID + Parquet + Spark |
| ML model serving | **FastAPI** | Async, fast, auto-docs |
| Password storage | **bcrypt** | One-way, salted, industry standard |
| API auth | **JWT** | Stateless, scalable |
| Vector search | **FAISS** | Sub-ms, battle-tested |

