# Chapter 1 - Foundations: Every Concept Explained From Scratch

> This file explains EVERY technical term used in your projects from absolute zero.
> Read this FIRST before anything else. If you understand everything here, you can explain anything in an interview.

---

## PART 1: MACHINE LEARNING FUNDAMENTALS

### What is Machine Learning?

Instead of writing explicit rules ("if BMI > 30 AND age > 50 ' diabetes risk"), you give the computer EXAMPLES and let it figure out the rules itself.

```
Traditional Programming:    Rules + Data ' Answer
Machine Learning:           Data + Answers ' Rules (model)
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

Your project does BINARY CLASSIFICATION " every model predicts one of two outcomes: sick or healthy.

---

### What is a Training Set vs Test Set?

```
253,680 patient records
    """ 80% ' Training Set (202,944 records)
    "         The model LEARNS from these
    "
    """" 20% ' Test Set (50,736 records)
              The model is TESTED on these
              It has NEVER seen these before
```

**Why split?** If you test the model on the SAME data it trained on, it just memorizes the answers. That's like giving a student the exam answers during practice and testing them with the same exam " of course they'll score 100%, but they haven't actually learned anything.

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
""" 218,334 records (86.1%) ' Label 0 = HEALTHY     ---------------------'
""""  35,346 records (13.9%) ' Label 1 = DIABETIC    ----'-'-'-'-'-'-'-'-'-'-'-'-'-'-'-'-'-'
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

**86.1% accuracy sounds great, but the model is completely useless.** It never catches the disease. It's like a smoke detector that never goes off " great for avoiding false alarms, catastrophic for actual fires.

This is the **accuracy paradox** " high accuracy can be meaningless when classes are imbalanced.

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

**Analogy**: Imagine you're training a security guard. Without scale_pos_weight, every mistake costs $1 " whether they let a thief in or turn away a legitimate visitor. With scale_pos_weight=6.16, letting a thief in costs $6.16 but turning away a visitor costs $1. Now the guard will be MUCH more careful about letting potential thieves in, even if it means occasionally stopping a legitimate visitor.

---

### What is XGBoost? (Explained Simply)

XGBoost = **eXtreme Gradient Boosting**. Let's break that down:

**Boosting** = Train many small, weak models (decision trees) one after another. Each new tree focuses on fixing the mistakes of the previous trees.

```
Tree 1: Makes predictions. Gets 70% right.
         Identifies which patients it got WRONG.
             "
Tree 2: Focuses specifically on the patients Tree 1 got wrong.
         Combined accuracy: 78%.
             "
Tree 3: Focuses on the remaining mistakes.
         Combined accuracy: 83%.
             "
... (100-1000 trees later)
             "
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
| **XGBoost** | Fast, handles imbalance natively (scale_pos_weight), works great on tabular data | Needs hyperparameter tuning | **YES " primary choice** |
| **Random Forest** | Simple, hard to overfit | No native imbalance handling, slower | Close second, but no scale_pos_weight |
| **Logistic Regression** | Simple, interpretable | Can't capture complex non-linear patterns | Too simple for 9+ features |
| **Neural Networks** | Best for images/text/huge datasets | Overfits on 253K tabular data, needs much more data, hard to interpret | **NO " proven worse on tabular data** |
| **SVM** | Good for small datasets, clear decision boundary | Slow on large datasets, sensitive to scaling | Used for kidney/lungs (smaller datasets) |

**The research backing**: The Grinsztajn et al. (2022) NeurIPS benchmark paper compared tree-based models (XGBoost, Random Forest) vs deep learning on 45 tabular datasets. Result: **tree-based models won on medium-sized tabular data** like yours.

---

### What is predict_proba? (How Confidence Works)

When the model predicts, it doesn't just say "Diabetic" or "Not Diabetic." It gives a PROBABILITY.

```python
model.predict([patient_data])
# Returns: [1]   Just "Diabetic" (not useful alone)

model.predict_proba([patient_data])
# Returns: [[0.06, 0.94]]
#            '       '
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
        "                                 "                               "
   "I don't know enough"          "I learned the real patterns"   "I memorized, not learned"
```

**In your project:**
- Training accuracy: ~89%
- Test accuracy: ~85-89%
- Real-world validation: 77% (48 actual patient records)
- The gap is small ' Good fit, no overfitting

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
    (Important for: NOT MISSING sick patients " THIS IS CRITICAL IN HEALTHCARE)

Specificity = TN / (TN + FP) = 75 / (75 + 5) = 93.75%
    "Of all healthy patients, how many did the model correctly identify as healthy?"

F1 Score = 2 * (Precision * Recall) / (Precision + Recall) = 75%
    "Harmonic mean of precision and recall " balances both"
```

**In healthcare, RECALL (Sensitivity) is the most important metric.** Missing a diabetic patient (FN) is much worse than a false alarm (FP). A false alarm means one extra doctor visit. A missed diagnosis means untreated disease.

**That's exactly why scale_pos_weight matters** " it pushes the model toward higher recall by penalizing missed positives.

---

## PART 2: DATA ENGINEERING FUNDAMENTALS

### What is ETL? (Extract, Transform, Load)

```
EXTRACT                    TRANSFORM                       LOAD
Get raw data               Clean and reshape it            Put it somewhere useful
"""""""""                  """"""""""""""""""              """"""""""""""""""""
Download CSV from CDC  '   Rename columns            '     Save as Parquet file
                          Handle missing values              "
                          Convert types                  Train ML model
                          Feature engineering                "
                          Split train/test              Save as .pkl file
                                                           "
                                                       Load at API startup
```

**Your Healthcare ETL:**
```
CDC BRFSS CSV (raw, 253K rows, messy column names)
    " EXTRACT
Read into Pandas DataFrame
    " TRANSFORM
    """ Rename: "HighBP" ' "hypertension"
    """ Rename: "HighChol" ' "high_chol"
    """ Convert: age codes ' age buckets (1-13)
    """ Drop: irrelevant columns
    """ Handle: missing values (fill or drop)
    """" Split: 80% train, 20% test
    " LOAD
    """ Train XGBoost model
    """ Save model to diabetes_model.pkl
    """" Load model in FastAPI at startup
```

### What is ELT? (And How It Differs)

```
ETL: Extract ' Transform ' Load
     Transform happens OUTSIDE the target (in Spark, Python, etc.)
     Used when: transformation is complex, target is simple storage

ELT: Extract ' Load ' Transform
     Transform happens INSIDE the target (in Snowflake, BigQuery, etc.)
     Used when: target has powerful compute
```

**Your Nissan project used ELT:**
```
Raw CSV files ' Load into Snowflake ' Transform using Snowflake SQL
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
Types: Embedded (int64, float64, string " no parsing needed)
Statistics: Min/max per column chunk ' skip irrelevant data
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
Your Frontend (React)  '  Your Backend (FastAPI)  '  Your Database (SQLite)

The frontend doesn't talk to the database directly.
It sends HTTP requests to the API, which talks to the database.
```

**REST** = A set of rules for designing APIs:
```
GET    /api/patients/123     ' Read patient 123
POST   /api/predictions      ' Create a new prediction
PUT    /api/patients/123     ' Update patient 123
DELETE /api/patients/123     ' Delete patient 123
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

**The problem**: After a user logs in, how does the server know they're logged in on future requests? The server is stateless " it doesn't remember anything between requests.

**The solution**: Give the user a signed token they include in every request.

```
1. User logs in:
   POST /login {username: "pavan", password: "secret123"}
       "
   Server verifies password (bcrypt compare)
       "
   Server creates JWT token:
   eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYXZhbiIsImV4cCI6MTcxOH0.abc123
   '                      '                                      '
   Header (algorithm)      Payload (user info + expiry)           Signature
       "
   Returns token to frontend

2. Frontend stores token in localStorage

3. Every future request includes the token:
   GET /api/my-records
   Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
       "
   Server decodes token ' extracts username ' knows who's asking
       "
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
| pavan    | secret123   |   Hacker sees the actual password!
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
3. **Slow on purpose**: Takes ~100ms to hash " prevents brute-force attacks (attackers can only try ~10 passwords/second instead of millions)

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
    print("Password correct!")  # "
else:
    print("Wrong password!")
```

---

## PART 3: SYSTEM DESIGN CONCEPTS

### What is Middleware?

Middleware = code that runs BEFORE and AFTER every request, like airport security checkpoints.

```
Client Request
    "
[Middleware 1: CORS]          "Are you allowed to call this API?"
    "
[Middleware 2: Rate Limit]    "Have you made too many requests?"
    "
[Middleware 3: TrustedHost]   "Are you calling from a trusted domain?"
    "
[Middleware 4: Security]      "Let me add security headers to the response"
    "
[Middleware 5: Exception]     "If anything crashes, I'll catch it safely"
    "
[Middleware 6: Request ID]    "Let me give this request a tracking UUID"
    "
[Middleware 7: Timing]        "Let me measure how long this takes"
    "
YOUR ACTUAL ROUTE HANDLER    "Process the request"
    "
[Back through middleware in reverse order]
    "
Client Response (with security headers, timing info, etc.)
```

**Example: CORS middleware (Cross-Origin Resource Sharing)**

```
Your frontend: http://localhost:3000
Your backend:  http://127.0.0.1:8000

Problem: Browser blocks requests between different origins (port 3000   port 8000)
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
    "
How does the NavBar component know? Pass as props?
    "
How does the PredictionForm know? Pass through 5 levels of components?
    "
This is called "prop drilling" " passing data through components that don't need it
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
| 30% | Spark optimization (TCS) | 45 min ' 31 min |
| 60% | Manual effort reduction (Nissan) | Automated with Lambda |
| 25% | Intervention reduction (AutoSys) | Automated dependency chains |
| 2+ years | Professional experience | TCS, Nov 2023 " Present |


---


## One-Line Definitions

| Term | Definition |
|---|---|
| **FastAPI** | Async Python web framework with automatic docs and Pydantic validation |
| **Next.js** | React framework with server-side rendering, file-based routing, Turbopack |
| **XGBoost** | Gradient-boosted decision tree algorithm " best for tabular data |
| **SVM** | Support Vector Machine " finds optimal boundary, good for small datasets |
| **Random Forest** | Ensemble of decision trees " reduces overfitting via bagging |
| **JWT** | JSON Web Token " stateless auth token (header.payload.signature) |
| **bcrypt** | One-way password hashing with salt " industry standard |
| **OAuth2** | Authentication framework " we use Password grant + Bearer tokens |
| **CORS** | Cross-Origin Resource Sharing " controls which domains call your API |
| **SSE** | Server-Sent Events " server pushes data to client over HTTP |
| **WebSocket** | Full-duplex bidirectional communication " more complex than SSE |
| **RAG** | Retrieval-Augmented Generation " inject relevant docs into AI prompts |
| **Pydantic** | Data validation library using Python type hints |
| **SQLAlchemy** | Python ORM " maps classes to database tables |
| **Zustand** | Lightweight React state management (alternative to Redux) |
| **Framer Motion** | React animation library for smooth transitions |
| **scale_pos_weight** | XGBoost parameter " weights minority class to handle imbalance |
| **predict_proba** | Returns class probabilities instead of binary 0/1 |
| **StandardScaler** | Normalizes features to mean=0, std=1 (required for SVM) |
| **Parquet** | Columnar file format " 10x faster reads than CSV |
| **Uvicorn** | ASGI server that runs FastAPI applications |
| **ASGI** | Async Server Gateway Interface " Python's async web standard |
| **Middleware** | Code that runs between request and response (auth, logging, etc.) |
| **Dependency Injection** | FastAPI auto-provides function args (db sessions, auth) |
| **Lifespan** | FastAPI startup/shutdown hook for loading models |
| **ORM** | Object-Relational Mapping " write Python, not SQL |
| **HIPAA** | US law governing health data privacy and security |
| **PII** | Personally Identifiable Information " names, DOBs, health data |
| **Sensitivity** | True positive rate " % of sick patients correctly identified |
| **Specificity** | True negative rate " % of healthy patients correctly identified |

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
        * HTTP + SSE
FastAPI Backend (7 middleware layers, JWT auth, Pydantic validation)
        *
3 services:
  1. ML Prediction (5 XGBoost/SVM models ' confidence + risk + disclaimer)
  2. AI Chat (RAG + Gemini ' SSE streaming)
  3. Data (SQLAlchemy + SQLite/PostgreSQL)
```

---

## When Asked "Why X over Y?"

| Question | Answer Template |
|---|---|
| Why Next.js over React? | App Router layouts, SSR, file routing, Turbopack |
| Why FastAPI over Flask? | Async, auto-docs, Pydantic, 10x faster |
| Why FastAPI over Django? | Django too heavy for REST API " don't need admin/templates |
| Why XGBoost over neural nets? | Tabular data, handles imbalance, fast training |
| Why SVM over XGBoost (kidney/lungs)? | Small datasets " SVM generalizes better |
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
' Fixing class imbalance: one parameter (`scale_pos_weight=6.16`) took disease detection from 0% to ~60%.

**"What's your biggest failure?"**
' Initially shipped with 86.7% accuracy thinking it was great, only to discover it detected zero diseases. Taught me that accuracy alone is meaningless.

**"How do you handle deadlines?"**
' I prioritize: get core prediction working first, then add auth, then frontend polish, then tests. Each phase is independently deployable.

**"How do you learn new technologies?"**
' I build. This project forced me to learn FastAPI, Next.js App Router, XGBoost tuning, SSE streaming, and RAG " all by implementing them in a real system.


---


> Every concept a DE interviewer expects you to know, with clear explanations and examples.

---

## DATA PIPELINE FUNDAMENTALS

### Q: What is idempotency and why does it matter?

**Idempotent** = Running the same operation multiple times produces the same result.

```python
# NOT idempotent " appends duplicates:
df.write.mode("append").parquet("output/")
# Run twice ' 2x data!

# Idempotent " safe to re-run:
df.write.mode("overwrite").parquet("output/partition_date=2024-06-15/")
# Run twice ' same result

# Even better " DELETE + INSERT pattern:
DELETE FROM target WHERE batch_date = '2024-06-15';
INSERT INTO target SELECT * FROM staging WHERE batch_date = '2024-06-15';
# Run twice ' same result
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
| In my work | Healthcare raw data | Nissan ' Snowflake | Nova ' Delta Lake |

---

### Q: What is the medallion architecture (Bronze/Silver/Gold)?

I implemented this in Nova:

```
BRONZE (Raw)          SILVER (Validated)      GOLD (Curated)
""""""""""""          """"""""""""""""""      """"""""""""""
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

**Slowly Changing Dimension Type 2** " Track history of dimension changes.

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

**C**onsistency " Every read returns the latest write
**A**vailability " Every request gets a response
**P**artition tolerance " System works despite network failures

**You can only have 2 of 3:**

| System | Choice | Trade-off |
|---|---|---|
| PostgreSQL | CP | Consistent, but single node = not always available |
| Cassandra | AP | Always available, but reads might be stale |
| MongoDB | CP (default) | Consistent reads, but writes pause during elections |

**In my projects:**
- Healthcare (SQLite/PostgreSQL): CP " consistency matters for patient data
- Nova (Delta Lake): CP " ACID writes ensure data integrity

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
""""""""""""""""""""""              """"""""""""""""""""""
"  id  " name " age  "              " id   " id   " id   "
"  1   " John "  25  "              "  1   "  2   "  3   "
"  2   " Jane "  30  "              """"""""""""""""""""""
"  3   " Bob  "  35  "              " name " name " name "
"""""""""""""""""""""""              " John " Jane " Bob  "
                                    """"""""""""""""""""""
Row: reads ALL columns              " age  " age  " age  "
Good for: SELECT * WHERE id=1       "  25  "  30  "  35  "
                                    """""""""""""""""""""""
                                    
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
    " Extract
data/raw/diabetes.csv
    " Column rename (HighBP ' hypertension)
data/processed/diabetes.parquet
    " Train/test split, class balancing
diabetes_model.pkl
    " predict_proba()
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
- Streaming: Nova behavior events (Kafka ' Spark Structured Streaming ' Delta)

### Q: What is Kafka and how does it work?

```
Producer ' Topic (partitioned) ' Consumer Group
```

- **Producer**: Sends messages (events) to a topic
- **Topic**: Ordered log of messages, split into partitions
- **Partition**: Unit of parallelism. Messages within a partition are ordered.
- **Consumer Group**: Multiple consumers reading from different partitions in parallel
- **Offset**: Position in the partition. Consumer tracks where it left off.

**In Nova:**
```
Frontend (click/view event) ' Kafka topic: nova.content_events ' 
    Spark Structured Streaming ' gold.fact_content_event (Delta table)
```

### Q: What is exactly-once semantics?

Three delivery guarantees:
- **At-most-once**: Fire and forget. Messages might be lost.
- **At-least-once**: Retry until confirmed. Messages might be duplicated.
- **Exactly-once**: Each message processed exactly once. No loss, no duplication.

**How to achieve exactly-once:**
- Kafka: Idempotent producers + transactional consumers
- Spark Structured Streaming: Checkpointing + WAL
- Application level: Idempotent writes (what I do " safe to re-process)

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
> "Snowflake separated compute from storage " we could scale down warehouses at night (saving cost) and scale up during batch windows. Its COPY INTO command made S3 ' Snowflake loading simple. The VARIANT type handled our semi-structured data without pre-flattening."

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
> "Pandas for anything under ~5GB that fits in RAM " fast prototyping, data exploration, simple transforms. Spark for anything bigger, anything that needs to scale, or anything that runs in production with reliability requirements. At Nomura, all production ETL was Spark. For local data exploration and testing, I used Pandas."

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
| Developed by | Databricks | Netflix ' Apache | Uber ' Apache |
| Storage | Parquet + JSON log | Parquet + metadata | Parquet + timeline |
| ACID | Yes | Yes | Yes |
| Time travel | Yes (version history) | Yes (snapshots) | Yes (timeline) |
| Schema evolution | Yes | Excellent | Yes |
| Merge/Upsert | MERGE INTO | MERGE INTO | Upsert natively |
| Community | Large (Databricks) | Growing fast | Smaller |
| My experience | **Nova project** | Aware | Aware |

**When asked "Why Delta Lake?"**
> "Delta Lake adds ACID transactions to Parquet " I can do MERGE operations, time travel, and Change Data Feed. In Nova, I use Delta for the medallion architecture: Bronze (raw ingest with ACID), Silver (validated with MERGE), Gold (curated with SCD Type 2). The transaction log prevents corrupt partial writes."

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

---

### What is Schema Evolution?

Schema evolution means changing the structure of your data (adding columns, renaming fields, changing types) WITHOUT breaking existing pipelines or downstream consumers.

**Why this matters:** In production, source systems change ALL the time. A vendor adds a new field, a team renames a column, a data type changes from string to integer. Your pipeline either handles this gracefully or breaks at 2 AM.

**The 3 types of schema changes:**

| Change type | Example | Risk level | How to handle |
|---|---|---|---|
| **Additive** (safe) | New column added | Low | Ignore new column, or add it with a default |
| **Rename** (medium) | `user_id` -> `customer_id` | Medium | Column mapping in ETL, don't use `SELECT *` |
| **Breaking** (dangerous) | Column deleted, type changed | High | Schema validation catches it, pipeline halts, alert fires |

**How Delta Lake handles this:**
```python
# Delta Lake schema evolution: auto-merge new columns
df.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("gold/movies")
# If the new data has extra columns, Delta adds them automatically
# Existing rows get NULL for the new columns
```

**How your projects handle this:**
- **Healthcare**: Fixed schema (9-24 features per model). Schema changes require model retraining.
- **Nova**: Delta Lake `mergeSchema=true` for additive changes. Breaking changes caught by Silver layer validation and quarantined.

**Interview answer pattern:**
> "I handle schema evolution at three levels: (1) Prevention -- use explicit column selection, never SELECT *, schema contracts with upstream. (2) Detection -- Bronze layer validates incoming schema against expected, alerts on drift. (3) Adaptation -- Delta Lake's mergeSchema for safe additive changes, manual review for breaking changes."

---

## PART 8: DATA ENGINEERING DEEP-DIVE (The Core of Your Interview)

> Everything below is what separates a "developer who writes SQL" from a Data Engineer.

---

### What is Apache Airflow?

**Airflow** is a workflow orchestration tool. You define tasks and their dependencies as a DAG (Directed Acyclic Graph) in Python, and Airflow runs them in the right order, retries failures, and alerts you.

**Think of it like this:** You have 10 tasks that need to run every day:
1. Download file from S3
2. Validate schema
3. Transform data
4. Run quality checks
5. Load to Snowflake

Some depend on others (can't transform before downloading). Airflow manages this automatically.

**You used AutoSys at TCS (same concept, enterprise version).** Airflow is the open-source equivalent that every startup and mid-size company uses.

**Core Airflow concepts:**

| Concept | What it is | AutoSys equivalent |
|---|---|---|
| **DAG** | A Python file defining tasks and their order | JIL (Job Information Language) file |
| **Task** | A single unit of work (run a script, call an API) | A job definition |
| **Operator** | The TYPE of task (BashOperator, PythonOperator, etc.) | Job type (command, file watcher) |
| **Sensor** | A task that WAITS for a condition (file arrives, API responds) | File trigger / event trigger |
| **XCom** | How tasks pass small data between each other | No direct equivalent |
| **Connection** | Credentials for external systems (S3, Snowflake, etc.) | Machine/profile definitions |
| **Schedule** | Cron expression for when the DAG runs | Calendar/schedule definition |
| **Backfill** | Re-run a DAG for past dates (replay history) | Rerun with date override |

**Example DAG (what you'd write in an interview):**

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime, timedelta

# Default args: retry 3 times, wait 5 min between retries, alert on failure
default_args = {
    'owner': 'data-engineering',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email': ['data-team@company.com'],
}

# The DAG definition
with DAG(
    dag_id='daily_trade_etl',
    default_args=default_args,
    schedule_interval='0 6 * * *',   # Run at 6 AM UTC daily
    start_date=datetime(2024, 1, 1),
    catchup=False,                    # Don't backfill old dates
    tags=['production', 'trades'],
) as dag:

    # Task 1: Wait for source file to arrive in S3
    wait_for_file = S3KeySensor(
        task_id='wait_for_source_file',
        bucket_name='raw-data',
        bucket_key='trades/{{ ds }}/trades.parquet',  # ds = execution date
        timeout=3600,           # Wait up to 1 hour
        poke_interval=300,      # Check every 5 minutes
    )

    # Task 2: Validate schema
    def validate_schema(**context):
        import pandas as pd
        df = pd.read_parquet(f"s3://raw-data/trades/{context['ds']}/trades.parquet")
        expected_cols = {'trade_id', 'instrument_id', 'amount', 'trade_date'}
        if not expected_cols.issubset(set(df.columns)):
            raise ValueError(f"Schema mismatch: missing {expected_cols - set(df.columns)}")
        context['ti'].xcom_push(key='row_count', value=len(df))

    validate = PythonOperator(
        task_id='validate_schema',
        python_callable=validate_schema,
    )

    # Task 3: Transform with Spark (submit to EMR/K8s)
    def run_spark_transform(**context):
        from airflow.providers.amazon.aws.hooks.emr import EmrHook
        # Submit Spark job to EMR cluster
        hook = EmrHook()
        hook.add_job_flow_steps(cluster_id='j-XXXXX', steps=[{
            'Name': 'transform_trades',
            'ActionOnFailure': 'CONTINUE',
            'HadoopJarStep': {
                'Jar': 'command-runner.jar',
                'Args': ['spark-submit', 's3://scripts/transform_trades.py',
                         '--date', context['ds']]
            }
        }])

    transform = PythonOperator(
        task_id='spark_transform',
        python_callable=run_spark_transform,
    )

    # Task 4: Load to Snowflake
    load = SnowflakeOperator(
        task_id='load_to_snowflake',
        sql="""
            COPY INTO trades_staging
            FROM @s3_stage/trades/{{ ds }}/
            FILE_FORMAT = (TYPE = PARQUET)
        """,
        snowflake_conn_id='snowflake_prod',
    )

    # Task 5: Quality checks
    quality_check = SnowflakeOperator(
        task_id='quality_checks',
        sql="""
            -- Fail if no rows loaded
            SELECT CASE WHEN COUNT(*) = 0
                THEN 1/0  -- Intentional error to fail task
                ELSE 1 END
            FROM trades_staging
            WHERE trade_date = '{{ ds }}'
        """,
        snowflake_conn_id='snowflake_prod',
    )

    # DEFINE THE ORDER (the DAG structure)
    wait_for_file >> validate >> transform >> load >> quality_check
    # This means: wait_for_file runs first, then validate, then transform, etc.
```

**Key Airflow interview questions:**

**Q: "What's the difference between `schedule_interval` and `start_date`?"**
> `start_date` is when the DAG BEGINS being eligible to run. `schedule_interval` is HOW OFTEN it runs after that. A DAG with `start_date=Jan 1` and `schedule_interval='@daily'` will first run on Jan 2 (for the Jan 1 data period).

**Q: "What is `catchup`?"**
> If `catchup=True` and you deploy a DAG with `start_date` 30 days ago, Airflow will run 30 backfill executions to "catch up." Usually set to `False` in production to avoid accidental mass runs.

**Q: "How do you handle task failures?"**
> 1. `retries=3` with `retry_delay=timedelta(minutes=5)` -- automatic retry
> 2. `email_on_failure=True` -- alert the team
> 3. `on_failure_callback` -- custom Python function for Slack/PagerDuty
> 4. Airflow UI shows failed tasks in red -- click to see logs and re-trigger

**Q: "What are XComs?"**
> XCom = Cross-Communication. Tasks can push/pull small values between each other. Example: Task 1 pushes `row_count=50000`, Task 3 pulls it to validate. NOT for large data -- use S3/GCS for that.

**How to bridge AutoSys to Airflow:**
> "At TCS I used AutoSys for job scheduling -- same concept as Airflow. The difference is Airflow defines DAGs in Python code (version-controlled, testable), while AutoSys uses JIL configuration files. I managed 50+ daily job chains in AutoSys with dependency management and failure recovery. Airflow is the same workflow orchestration paradigm -- I'd ramp up in days, not weeks."

**Airflow Counter-Question Drill-Down (they go 5 levels deep):**

**Level 3:** "How do you pass data between tasks?"
> "XComs (cross-communication). Task A pushes a value, Task B pulls it. But XComs are for SMALL data only (stored in Airflow's metadata DB). For large data, Task A writes to S3, pushes the S3 path via XCom, Task B reads from S3."

**Level 4:** "Your DAG has 50 tasks. One fails at 3 AM. What happens?"
> "Airflow retries based on default_args (e.g., 3 retries, 5-min delay). If all retries fail, on_failure_callback triggers (Slack/PagerDuty alert). Downstream tasks are skipped (upstream_failed state). I fix the issue, then manually trigger the failed task from the Airflow UI -- only that task re-runs, not the whole DAG."

**Level 5:** "How do you test DAGs before deploying to production?"
> "Three layers: (1) Unit test the Python functions that tasks call. (2) DAG integrity test -- import the DAG and verify it has no import errors and correct dependencies. (3) Run against a staging environment with test data. I never deploy untested DAGs to production."

**Why Airflow not Cron?** Cron has no dependency management, no retry logic, no monitoring UI, no backfill. For a single script, cron is fine. For 50 interconnected tasks with failure handling, Airflow.

**Memory trick:** Airflow = **A**utomates **I**nterdependent **R**unnable **F**lows, **L**ogs **O**utput, **W**atches failures

---

### What is dbt (data build tool)?

**dbt** transforms data INSIDE your warehouse using SQL. Instead of writing ad-hoc SQL scripts, you write modular SQL models that dbt compiles, runs, and tests.

**Think of it like this:** dbt is to SQL what React is to HTML. It adds structure, reusability, and testing to what would otherwise be a mess of SQL files.

**Why companies love dbt:**
1. SQL transformations are version-controlled (Git)
2. Built-in testing (not null, unique, accepted values)
3. Auto-generated documentation and lineage graphs
4. Modular: models reference other models with `ref()`
5. Jinja templating for dynamic SQL

**Example dbt project structure:**
```
models/
  staging/
    stg_trades.sql          -- Clean raw data
    stg_instruments.sql     -- Clean reference data
  marts/
    fct_daily_pnl.sql       -- Business metric: daily P&L
    dim_instruments.sql     -- Dimension table
  schema.yml                -- Tests and documentation
```

**Example dbt model (what you'd write):**

```sql
-- models/marts/fct_daily_pnl.sql
-- This model calculates daily P&L per instrument

WITH trades AS (
    SELECT * FROM {{ ref('stg_trades') }}
    -- ref() creates a dependency: stg_trades runs BEFORE fct_daily_pnl
),

instruments AS (
    SELECT * FROM {{ ref('stg_instruments') }}
),

daily_aggregates AS (
    SELECT
        t.trade_date,
        t.instrument_id,
        i.instrument_name,
        i.asset_class,
        SUM(t.amount) AS total_amount,
        COUNT(*) AS trade_count,
        AVG(t.amount) AS avg_trade_size
    FROM trades t
    JOIN instruments i ON t.instrument_id = i.instrument_id
    GROUP BY 1, 2, 3, 4
)

SELECT
    *,
    SUM(total_amount) OVER (
        PARTITION BY instrument_id
        ORDER BY trade_date
    ) AS cumulative_pnl
FROM daily_aggregates
```

**Example dbt tests (schema.yml):**
```yaml
# models/schema.yml
version: 2

models:
  - name: fct_daily_pnl
    description: "Daily P&L aggregated by instrument"
    columns:
      - name: instrument_id
        tests:
          - not_null        # Fails if any NULL instrument_id
          - relationships:  # Foreign key check
              to: ref('dim_instruments')
              field: instrument_id
      - name: total_amount
        tests:
          - not_null
      - name: trade_date
        tests:
          - not_null
          - unique          # One row per instrument per day
```

**dbt commands:**
```bash
dbt run              # Execute all models (build the tables)
dbt test             # Run all tests
dbt docs generate    # Generate documentation website
dbt run --select fct_daily_pnl+   # Run one model and all downstream
dbt run --full-refresh            # Drop and rebuild tables
```

**How to bridge to your experience:**
> "I haven't used dbt directly, but the concept maps to what I do in PySpark. dbt transforms data in the warehouse with SQL; I transform data in Spark with PySpark/SQL. Both use modular code, testing, and version control. The difference is dbt runs SQL inside Snowflake/BigQuery (push-down), while Spark pulls data out and processes it in a cluster. For SQL-heavy ELT workloads, dbt is simpler. For complex transformations with ML features, Spark is more powerful. I'd pick up dbt quickly."

**dbt Counter-Question Drill-Down:**

**"What does ref() actually do?"**
> "ref('stg_trades') does two things: (1) resolves the actual table name in the target warehouse, and (2) creates a dependency -- dbt knows stg_trades must run BEFORE any model that ref()s it. It's like Python's import statement -- it both loads and declares a dependency."

**"How do you handle incremental models in dbt?"**
> "With the `incremental` materialization. Instead of rebuilding the full table, dbt only processes new rows since the last run. You define `is_incremental()` in Jinja to add a WHERE clause filtering by a timestamp. This turns a 2-hour full rebuild into a 5-minute incremental append."

**"dbt vs stored procedures?"**
> "Stored procedures live inside the database -- no version control, no tests, no lineage, hard to review. dbt models are SQL files in Git -- versioned, tested with schema.yml, auto-documented, with lineage graphs. It's the difference between writing scripts in production vs having a proper SDLC."

**Analogy:** dbt is to SQL what React is to HTML. It adds components (models), imports (ref()), testing (schema.yml), and build tools (dbt run) to what would otherwise be a mess of raw SQL files.

**Memory trick:** dbt = **d**efined, **b**uildable, **t**ested SQL

---

### Data Lake vs Data Warehouse vs Lakehouse

This is asked in EVERY DE interview. Know the tradeoffs cold:

| | Data Warehouse | Data Lake | Data Lakehouse |
|---|---|---|---|
| **What it is** | Structured storage optimized for analytics | Raw storage for any data type | Combines both: raw storage + warehouse features |
| **Examples** | Snowflake, Redshift, BigQuery | S3 + Parquet files, HDFS | Delta Lake, Apache Iceberg, Apache Hudi |
| **Schema** | Schema-on-write (define before loading) | Schema-on-read (define when querying) | Schema-on-write with evolution |
| **Data types** | Structured only (tables) | Any (structured, semi, unstructured) | Any, with table abstraction |
| **ACID** | Yes (transactional) | No (files can be corrupted mid-write) | Yes (Delta Lake adds transactions) |
| **Cost** | Expensive (compute + storage coupled) | Cheap (just S3/GCS storage) | Cheap storage + compute-on-demand |
| **Performance** | Fast (optimized engine) | Slow (no indexing, no stats) | Fast (Z-ordering, file skipping, caching) |
| **Best for** | BI/reporting, dashboards | ML training data, raw archives | Modern analytics + ML on one platform |

**Your experience spans all three:**
- **Warehouse**: Snowflake at Nissan (structured analytics)
- **Lake**: S3/Parquet at Nomura (raw trade data)
- **Lakehouse**: Delta Lake in Nova (medallion architecture)

**Interview answer:**
> "I've worked with all three patterns. At Nissan, we loaded clean data into Snowflake for reporting -- classic warehouse. At Nomura, trade data landed as Parquet in S3 -- a data lake that Spark queried directly. In my Nova project, I used Delta Lake which is a lakehouse -- raw data in Bronze (lake), validated data in Silver (warehouse-like), and ML-ready features in Gold. The lakehouse gives you cheap storage with ACID transactions and time travel."

**Counter-questions:**

**"Why not just use a data warehouse for everything?"**
> "Warehouses are expensive for raw/unstructured data. You don't want to pay Snowflake compute prices to store raw JSON logs. A lakehouse keeps raw data cheap (S3) and only pays for compute when you query it."

**"What's the medallion architecture?"**
> "Three layers. Bronze = raw data, exactly as received (your insurance policy). Silver = cleaned, deduplicated, validated (your reliable source). Gold = business-ready aggregations (what analysts query). Think of it as: pantry (Bronze) -> prepped ingredients (Silver) -> plated dish (Gold)."

**"Why keep Bronze if you have Silver?"**
> "Because cleaning logic has bugs. If your Silver transformation drops 5% of records due to a bad filter, you can re-derive Silver from Bronze. Without Bronze, you'd have to re-extract from the source system -- which may not have history or may have changed."

**Analogy:** Lake = a reservoir (stores everything, no treatment). Warehouse = a water treatment plant (clean, filtered, ready to drink). Lakehouse = a reservoir WITH a treatment plant built on top.

**Memory trick:** **B**ronze = **B**ackup, **S**ilver = **S**anitized, **G**old = **G**o-to-market

---

### Batch vs Streaming -- When to Use Which

| | Batch Processing | Stream Processing |
|---|---|---|
| **What it is** | Process data in chunks at scheduled intervals | Process data as it arrives, continuously |
| **Latency** | Minutes to hours | Milliseconds to seconds |
| **Tools** | Spark (batch), dbt, Airflow | Kafka, Spark Structured Streaming, Flink |
| **Complexity** | Simpler (process, done) | Harder (state management, ordering, exactly-once) |
| **Cost** | Lower (run once, stop) | Higher (always running) |
| **Use when** | Daily reports, model training, backfills | Real-time dashboards, fraud detection, alerts |

**Your experience:**
- **Batch**: Everything at Nomura (daily trade processing), Healthcare (model training), Nissan (daily ETL)
- **Streaming**: Nova's Kafka event ingestion (user views, clicks, ratings)

**The hybrid pattern (most common in production):**
```
Source -> Kafka (streaming buffer) -> Spark Structured Streaming (micro-batch)
                                          |
                                     Delta Lake (ACID writes)
                                          |
                                     Gold tables (batch analytics)
```
> "Most production systems are hybrid. We stream events into Kafka for low-latency capture, then Spark Structured Streaming processes them in micro-batches (every 30 seconds) and writes to Delta Lake. Downstream analytics still runs as daily batch. This gives us near-real-time data capture without the complexity of true event-at-a-time processing."

**Counter-questions:**

**"When would you choose streaming over batch?"**
> "When the business NEEDS low-latency data: fraud detection (seconds matter), real-time pricing, live dashboards for trading desks. If 'real-time' means 'fresher than daily,' I'd try hourly batch first -- it's 10x simpler and cheaper."

**"What's the hardest part of streaming?"**
> "State management. In batch, you process a file and you're done. In streaming, you need to track: what events have I seen? How do I handle late arrivals? How do I maintain running aggregations across restarts? This is why Spark Structured Streaming's checkpoint mechanism and Delta Lake's ACID writes are so valuable -- they handle state recovery automatically."

**"What's micro-batch vs true streaming?"**
> "Micro-batch: collect events for 30 seconds, process the batch. Latency = seconds. Spark Structured Streaming does this. True streaming: process each event individually as it arrives. Latency = milliseconds. Flink does this. Tradeoff: throughput vs latency. Micro-batch has higher throughput because it amortizes overhead across many events."

**Analogy:** Batch = taking the bus (scheduled, efficient, wait for it). Streaming = taking a taxi (on-demand, immediate, expensive). Micro-batch = a shuttle that leaves every 30 seconds (good compromise).

**Memory trick:** Batch = **B**ig chunks, **A**fter the fact. Stream = **S**mall events, **T**his instant.

---

### What is Idempotency? (Critical DE concept)

**Idempotent** = running the same operation multiple times produces the same result as running it once.

**Why it matters:** Pipelines WILL fail and be re-run. If your pipeline isn't idempotent, re-running creates duplicates or corrupts data.

**Bad (not idempotent):**
```python
# Running this twice creates DUPLICATE rows
df.write.mode("append").save("output/")
```

**Good (idempotent):**
```python
# Running this twice produces the SAME result
# Method 1: Delete then insert
spark.sql(f"DELETE FROM target WHERE batch_date = '{date}'")
df.write.mode("append").save("output/")

# Method 2: Overwrite partition
df.write.mode("overwrite").partitionBy("batch_date").save("output/")

# Method 3: Delta Lake MERGE (best)
target.merge(source, "target.id = source.id") \
    .whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll() \
    .execute()
```

**Your implementation at Nissan:**
```python
def process_batch(date, data):
    existing = snowflake.query(f"SELECT COUNT(*) FROM target WHERE batch_date = '{date}'")
    if existing > 0:
        snowflake.execute(f"DELETE FROM target WHERE batch_date = '{date}'")
    data.write.mode("append").save("snowflake://target")
# Safe to re-run: always produces the same result
```

**Counter-questions:**

**"Why is idempotency important?"**
> "Because pipelines WILL fail and be re-run. Network blip at 3 AM? Re-run. Upstream data arrived late? Re-run. If re-running creates duplicates or corrupts data, you have a production incident. Idempotent pipelines make re-runs SAFE."

**"What if two pipeline instances run simultaneously?"**
> "Delta Lake's MERGE uses optimistic concurrency control. If two jobs try to MERGE the same partition, one succeeds and the other gets a ConcurrentAppendException and retries. At the file level, S3's atomic PUT ensures no partial files."

**"Isn't DELETE then INSERT risky? What if it crashes between them?"**
> "Yes! That's why Delta Lake MERGE is better -- it's atomic. The DELETE+INSERT pattern works if wrapped in a transaction (Snowflake supports this). Without a transaction, you risk a window where data is deleted but not yet re-inserted."

**Analogy:** Idempotent = a light switch. Flipping it twice = same as flipping once. The room is lit either way. Non-idempotent = a coin counter. Running through twice = doubled count.

**Memory trick:** **I**dempotent = **I**dentical results, **D**espite **E**xtra runs

---

### Data Partitioning Strategies

**Partitioning** = splitting a large table into smaller pieces based on a column value. Each partition is stored as a separate folder/file.

```
trades/
  trade_date=2024-01-01/
    part-00000.parquet  (500MB)
  trade_date=2024-01-02/
    part-00000.parquet  (480MB)
  trade_date=2024-01-03/
    part-00000.parquet  (520MB)
```

**Why partition?**
- Query `WHERE trade_date = '2024-01-01'` reads only ONE folder instead of all
- On 1 year of daily data, this skips 364/365 = 99.7% of the data

**Choosing the partition key:**
| Good partition key | Bad partition key | Why |
|---|---|---|
| `trade_date` (daily) | `trade_id` (unique per row) | Too many partitions = "small files problem" |
| `region` (10 values) | `user_id` (millions) | Each partition should have meaningful data volume |
| `year/month` (24 values for 2 years) | `timestamp` (unique) | Partition pruning only works with WHERE filters |

**Rule of thumb:** Partition key should have 10-1000 distinct values. More = too many small files. Less = partitions too large.

**The Small Files Problem:**
```
BAD: 10,000 partitions x 1MB each = 10,000 small files
     Spark opens 10,000 file handles = SLOW
     S3 lists 10,000 objects = SLOW

GOOD: 365 partitions x 30MB each = 365 reasonably-sized files
     Spark opens 365 file handles = FAST
```

**Fix:** Delta Lake `OPTIMIZE` compaction merges small files into larger ones:
```sql
OPTIMIZE delta.`/data/trades/`              -- Compact small files
OPTIMIZE delta.`/data/trades/` ZORDER BY (instrument_id)  -- Also co-locate related data
```

**Z-Ordering** arranges data within files so that rows with similar values are stored near each other. This makes filter queries faster because Spark can skip entire file sections.

**Partitioning Counter-Question Drill-Down:**

**"How do you choose a partition key?"**
> "Pick the column you filter by most. If 90% of queries have WHERE date = ..., partition by date. Bad partition keys: high-cardinality columns (user_id with 100M unique values = 100M tiny files). Rule: partition should create 100-1000 partitions, each 128MB-1GB."

**"What's the small files problem?"**
> "Too many small files (<10MB each) kills performance: slow S3 LIST operations, too many file handles for Spark, poor compression. Cause: over-partitioning, frequent appends. Fix: Delta Lake OPTIMIZE compacts small files into 128MB targets. Run OPTIMIZE daily."

**"Z-ordering vs partitioning -- when to use which?"**
> "Partition by the column with FEW distinct values that you ALWAYS filter by (date, region). Z-order by columns with MANY values that you SOMETIMES filter by (customer_id, product_id). You can partition by date AND Z-order by customer_id -- they're complementary."

**Analogy:** Partitioning = organizing a library by floor (Fiction on floor 1, Science on floor 2). Z-ordering = organizing bookshelves within each floor by author AND genre so you can find books by either.

**Memory trick:** Partition = **P**hysical folders. Z-Order = **Z**one within folders.

---

### Data Contracts

**Data contracts** = formal agreements between data producers and consumers about schema, quality, and SLAs.

**The problem without contracts:** Upstream team changes a column name. Your pipeline breaks at 2 AM. No one told you.

**The solution:**
```yaml
# data_contract.yml
contract:
  name: trade_feed
  owner: trading-team
  consumer: data-engineering
  schema:
    - name: trade_id
      type: string
      nullable: false
      description: "Unique trade identifier"
    - name: amount
      type: decimal(18,2)
      nullable: false
      constraints:
        - "amount > 0"
    - name: trade_date
      type: date
      nullable: false
  sla:
    delivery_time: "06:00 UTC"
    freshness: "< 4 hours"
  quality:
    completeness: "> 99%"
    uniqueness: "trade_id must be unique"
```

**Your implementation:** You already do this informally:
- Healthcare: Pydantic schema validation on every API request
- Nova: Silver layer validates against expected schema, quarantines bad records
- Nissan: Schema validation Lambda before processing

**Interview answer:**
> "I implement data contracts through schema validation at the ingestion layer. At Nissan, the first Lambda in our Step Function pipeline validates incoming files against an expected schema -- column names, types, and not-null constraints. In Nova, the Bronze-to-Silver transformation enforces schema contracts: records that don't match are quarantined with quality metadata, not silently dropped. This is the same principle as formal data contracts -- just implemented at the pipeline level rather than as a separate governance tool."

---

### Data Observability

**Data observability** = monitoring the health of your data (not just your infrastructure).

**The 5 pillars:**
| Pillar | What it monitors | Example alert |
|---|---|---|
| **Freshness** | Is data arriving on time? | "trades table hasn't been updated in 6 hours" |
| **Volume** | Is the expected amount of data arriving? | "Only 1K rows today vs usual 50K" |
| **Schema** | Has the structure changed? | "New column 'risk_score' appeared" |
| **Distribution** | Are values within expected ranges? | "Average trade amount jumped from $10K to $10M" |
| **Lineage** | Where did this data come from? Which tables depend on it? | "Table X feeds 15 downstream reports" |

**Tools:** Monte Carlo, Great Expectations, Elementary, Soda

**Your implementation:**
- CloudWatch metrics on Lambda execution (Nissan) = freshness + volume monitoring
- Silver layer quality scoring (Nova) = distribution + schema monitoring
- 7-layer middleware with logging (Healthcare) = freshness monitoring
- Test suite with 141 tests (Healthcare) = schema + distribution validation

---

### Kimball vs Inmon (Data Warehouse Design)

Two competing philosophies for designing a data warehouse:

| | Kimball (Bottom-Up) | Inmon (Top-Down) |
|---|---|---|
| **Approach** | Build one star schema at a time, for each business process | Design the entire enterprise data model first |
| **Structure** | Star schemas (fact + dimension tables) | 3NF normalized enterprise data warehouse |
| **Speed** | Fast to deliver first results (weeks) | Slow to start (months) but comprehensive |
| **Complexity** | Simpler (denormalized, fewer joins) | More complex (normalized, more joins) |
| **Best for** | Analytics, BI, dashboards | Enterprise-wide single source of truth |
| **Your experience** | Nomura used star schema (Kimball) | N/A |

**Star Schema (what you used at Nomura):**
```
                    dim_instruments
                         |
dim_counterparties -- fct_trades -- dim_dates
                         |
                    dim_currencies
```

**Fact table** = the measurements/events (trades, with amounts and quantities)
**Dimension tables** = the context (WHO traded, WHAT instrument, WHEN, in what CURRENCY)

```sql
-- Star schema query: Daily P&L by asset class
SELECT
    d.trade_date,
    i.asset_class,
    SUM(f.trade_amount) AS total_pnl,
    COUNT(*) AS trade_count
FROM fct_trades f
JOIN dim_instruments i ON f.instrument_id = i.instrument_id
JOIN dim_dates d ON f.date_key = d.date_key
WHERE d.trade_date >= '2024-01-01'
GROUP BY 1, 2
ORDER BY 1, 2;
```

**Why Kimball for Nomura:**
> "We used Kimball's star schema because capital markets analytics is query-heavy -- portfolio managers need fast aggregations (daily P&L, risk exposure by desk). Denormalized dimensions mean fewer joins, which means faster queries. The trade-off is some data redundancy in dimensions, but for analytics that's acceptable."

**Counter-questions:**

**"What's a surrogate key?"**
> "A surrogate key is an auto-generated integer (1, 2, 3...) used as the primary key in a dimension table, INSTEAD of the natural business key. Why? Because natural keys can change (customer email changes), but surrogate keys never change. SCD Type 2 requires surrogate keys -- same customer_id has multiple rows with different surrogate keys."

**"What's a degenerate dimension?"**
> "A dimension that lives IN the fact table, not in a separate dimension table. Example: order_number in fct_orders. It's dimensional (you can filter by it), but creating a separate table for it adds no useful attributes. Common in transactional data."

**"Snowflake schema vs star schema?"**
> "A snowflake schema normalizes dimensions further. dim_products has a foreign key to dim_categories, which has a foreign key to dim_departments. Star schema denormalizes: dim_products has category_name and department_name directly. Star = fewer joins, faster queries, slightly more storage. Snowflake = more joins, slower queries, less storage. In analytics, query speed wins."

**Analogy:** Star schema = a compass (fact at center, dimensions pointing outward, simple to navigate). Snowflake schema = a family tree (branches upon branches, harder to traverse).

**Memory trick:** **F**act = **F**igures (numbers). **D**imension = **D**escriptors (context).

---

### Slowly Changing Dimensions -- All 4 Types (Complete Reference)

| Type | Strategy | Example | When to use |
|---|---|---|---|
| **Type 0** | Never update | Country codes, US states | Reference data that truly never changes |
| **Type 1** | Overwrite | Fix a typo: "Jonh" -> "John" | Corrections where history doesn't matter |
| **Type 2** | Add new row | Rating changes: 8.5 -> 8.8 | When you MUST track history (regulatory, HIPAA) |
| **Type 3** | Add column | `current_city`, `previous_city` | When you only need ONE previous value |

**Type 1 -- Overwrite (simplest):**
```sql
-- Customer moved from NYC to SF. Just update:
UPDATE dim_customers SET city = 'San Francisco' WHERE customer_id = 123;
-- History lost. We no longer know they were in NYC.
```

**Type 2 -- New Row (what you use in Nova):**
```sql
-- Step 1: Close the current record
UPDATE dim_movies
SET valid_to = CURRENT_DATE, is_current = false
WHERE movie_id = 123 AND is_current = true;

-- Step 2: Insert new record
INSERT INTO dim_movies (movie_id, title, rating, valid_from, valid_to, is_current)
VALUES (123, 'Inception', 8.8, CURRENT_DATE, NULL, true);
```

Result:
```
| movie_id | title     | rating | valid_from | valid_to   | is_current |
|----------|-----------|--------|------------|------------|------------|
| 123      | Inception | 8.5    | 2024-01-01 | 2024-06-15 | false      |
| 123      | Inception | 8.8    | 2024-06-15 | NULL       | true       |
```

**Type 3 -- Previous Value Column:**
```sql
ALTER TABLE dim_customers ADD COLUMN previous_city VARCHAR;

UPDATE dim_customers
SET previous_city = city, city = 'San Francisco'
WHERE customer_id = 123;
```

Result:
```
| customer_id | city          | previous_city |
|-------------|---------------|---------------|
| 123         | San Francisco | New York      |
```

**SCD Counter-Question Drill-Down:**

**"How do you decide which SCD type to use?"**
> "Ask: 'Do we need history?' No → Type 1 (overwrite). Yes, full history → Type 2 (new row). Only previous value → Type 3 (extra column). For regulatory data (healthcare, finance), always Type 2 -- auditors need the full trail."

**"How does Type 2 affect query performance?"**
> "More rows per entity means larger dimension tables. A customer active for 5 years with monthly address changes = 60 rows. Fix: always filter by `is_current = true` for current-state queries. Add an index on (entity_id, is_current) for fast lookups."

**"How do you implement SCD Type 2 at scale in Spark?"**
> "Delta Lake MERGE. Match on business key. When matched AND values changed: update existing row (set valid_to, is_current=false), insert new row (valid_from=today, is_current=true). Atomic operation, handles millions of records."

**Analogy:** Type 0 = carved in stone (never changes). Type 1 = whiteboard (erase and rewrite). Type 2 = photo album (keep all versions). Type 3 = before/after photo (only two snapshots).

**Memory trick:** SCD type number = how many versions you keep. Type 0 = zero changes. Type 1 = one version. Type 2 = two+ versions. Type 3 = three columns (current + previous + original).

---

### Common DE System Design Questions

**Q: "Design a real-time analytics pipeline for an e-commerce company."**

```
User clicks/views/purchases
        |
    [Kafka Topics]
    user-events, order-events
        |
    [Spark Structured Streaming]
    - Deduplicate events
    - Sessionize user activity
    - Compute metrics (GMV, conversion rate)
        |
    [Delta Lake Gold Tables]
    fct_sessions, fct_orders, dim_products
        |
    [Snowflake / Redshift]  <-- BI/dashboards (Tableau, Looker)
        |
    [Redis Cache]           <-- Real-time metrics API
```

**Key decisions to mention:**
1. **Kafka** for event capture (durability, replay, decoupling)
2. **Spark Structured Streaming** for processing (micro-batch, exactly-once with Delta)
3. **Delta Lake** for storage (ACID, time travel, schema evolution)
4. **Separate serving layer** (Snowflake for BI, Redis for real-time API)

**Q: "How would you handle late-arriving data?"**
> "Late data means events that arrive after the processing window has closed. For example, a mobile app event from Tuesday that arrives on Thursday due to the device being offline. I handle this with three techniques:
> 1. **Watermarking** in Spark Structured Streaming -- define how late is acceptable (e.g., 24 hours)
> 2. **Idempotent writes** -- if we re-process, Delta Lake MERGE prevents duplicates
> 3. **Reprocessing** -- for very late data, trigger a backfill of the affected partition"

**Q: "Design a data quality monitoring system."**

```
Data Pipeline Output
        |
    [Great Expectations / Custom Checks]
    - Row count within expected range?
    - Null percentage below threshold?
    - Column values within valid range?
    - Schema matches expected?
    - Freshness: updated within SLA?
        |
    +---------+---------+
    |                   |
  PASS                FAIL
    |                   |
  Continue          [Alert System]
  pipeline          - Slack notification
                    - PagerDuty for P0
                    - Quarantine bad data
                    - Block downstream
```

---

### The DE Interview Cheat Sheet -- Numbers to Know

| Concept | Typical value | Your value |
|---|---|---|
| Parquet vs CSV read speed | 10-100x faster | "Our Spark jobs read Parquet 95% faster than CSV" |
| Broadcast join threshold | < 10MB default, tunable to ~100MB | "We broadcast dimension tables under 100MB" |
| Spark partition size | 128MB-256MB ideal | "We target ~200MB per partition" |
| Kafka retention | 7 days default | "We retain events for 14 days for replay" |
| Delta Lake OPTIMIZE | Run daily or when >1000 small files | "Nova compacts during off-peak hours" |
| Snowflake warehouse size | XS for dev, M-L for production | "Nissan used medium warehouse for daily loads" |
| Airflow DAG count | 50-500 per organization | "I managed 50+ AutoSys job chains at Nomura" |
| Data freshness SLA | 1-4 hours for batch, <1 min for streaming | "Nissan SLA was data ready by 6 AM" |
| Data quality threshold | >99% completeness for production | "Silver layer enforces >99% non-null for key fields" |

---

### Kafka Deep-Dive (Every DE Must Know This)

**Analogy:** Kafka is like a post office with infinite mailboxes. Producers drop off letters (events). Consumers pick up letters whenever they're ready. The post office keeps letters for 7 days so anyone who missed them can catch up.

**Core concepts:**

| Concept | What it is | Analogy |
|---|---|---|
| **Topic** | A named feed of messages | A mailbox labeled "trades" or "user-clicks" |
| **Partition** | A topic split into ordered segments | Multiple slots in the mailbox for parallelism |
| **Producer** | Sends messages to a topic | The person mailing a letter |
| **Consumer** | Reads messages from a topic | The person checking the mailbox |
| **Consumer Group** | Multiple consumers sharing the work | A team of mail sorters splitting the load |
| **Offset** | Position of a message within a partition | Page number in a logbook |
| **Broker** | A Kafka server | One post office branch |
| **Replication** | Copies of data across brokers | Backup copies at other branches |

**Why Kafka instead of just writing to a database?**
1. **Decoupling**: Producer doesn't need to know who consumes. Add new consumers without changing producer.
2. **Buffering**: If downstream is slow, Kafka holds messages. Database writes would back-pressure the producer.
3. **Replay**: Consumer crashed? Restart and replay from the offset. Database INSERT is gone forever.
4. **Fan-out**: One event goes to 5 different systems. Without Kafka, producer writes to 5 databases.

**Q: "Explain Kafka's delivery guarantees."**

| Guarantee | Meaning | Config | Use when |
|---|---|---|---|
| **At-most-once** | Message might be lost, never duplicated | `acks=0` | Logging, metrics (losing one is OK) |
| **At-least-once** | Message never lost, might be duplicated | `acks=all` | Most pipelines (dedup downstream) |
| **Exactly-once** | Message delivered exactly once | `enable.idempotence=true` + transactions | Financial transactions, billing |

**Your Nova implementation:**
> "In Nova, user behavior events (views, clicks, ratings) flow through Kafka topics. Spark Structured Streaming consumes them in micro-batches and writes to Delta Lake Bronze tables. We use at-least-once delivery with deduplication at the Silver layer -- Delta Lake MERGE on event_id ensures no duplicates even if Kafka replays."

**Kafka Counter-Question Drill-Down:**

**Level 3:** "Explain partitions and consumer groups."
> "A topic is split into partitions for parallelism. Within a consumer group, each partition is read by exactly one consumer. So 10 partitions + 10 consumers = max parallelism. Add an 11th consumer? It sits idle."

**Level 4:** "What happens if a consumer crashes mid-processing?"
> "Depends on commit strategy. Auto-commit: might lose events (at-most-once). Manual commit after processing: might reprocess events (at-least-once). For exactly-once: use Kafka transactions + idempotent producer + consumer offset management."

**Level 5:** "How do you guarantee exactly-once end-to-end?"
> "Kafka alone gives exactly-once within Kafka. For end-to-end, the consumer must also be idempotent. In Nova, we use Delta Lake MERGE as the consumer -- even if Kafka replays events, the MERGE on event_id prevents duplicates."

**Why Kafka not RabbitMQ?** RabbitMQ deletes messages after consumption. Kafka retains. RabbitMQ is for task queues (send email, process image), Kafka for event streaming (replay, fan-out, audit trail).

**Memory trick:** Kafka = **K**eeps **A**ll **F**acts, **K**onsumers **A**ccess anytime

---

### Docker and Kubernetes (What DE Needs to Know)

**Docker analogy:** A Docker container is like a shipping container for software. Everything your app needs (code, libraries, Python version) is packed inside. It runs identically on your laptop, in CI/CD, and in production.

**Why Docker matters for DE:**
```
WITHOUT Docker:
  "It works on my machine" -> Fails in production
  Python 3.9 locally, Python 3.11 on server -> Library incompatibility

WITH Docker:
  Same container everywhere -> Same behavior everywhere
```

**Your Healthcare project Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Kubernetes analogy:** If Docker is a shipping container, Kubernetes is the shipping port -- it decides which ship (server) carries which containers, replaces broken containers, and scales up during high demand.

**K8s concepts for DE:**

| Concept | What it does | Your experience |
|---|---|---|
| **Pod** | Smallest unit -- runs 1+ containers | Each Spark executor runs as a K8s pod |
| **Deployment** | Manages replicas of pods | "Run 3 copies of my API" |
| **Service** | Stable network endpoint for pods | API accessible at `api-service:8000` |
| **ConfigMap/Secret** | External configuration | Database URLs, API keys |
| **HPA** | Auto-scales pods based on CPU/memory | Scale Spark executors based on queue depth |

**Your YARN-to-K8s migration answer:**
> "At Nomura, I migrated Spark from YARN to Kubernetes. Think of it as moving from a dedicated office building (YARN on fixed hardware) to a flexible coworking space (K8s with auto-scaling). The challenges were: (1) packaging Spark JARs into Docker images, (2) configuring S3A connectors for MinIO instead of HDFS, (3) translating YARN's memory model to K8s resource requests/limits. The result: same Spark jobs, now portable between on-prem and cloud."

**Docker/K8s Counter-Question Drill-Down:**

**"What's a multi-stage Docker build?"**
> "Build the app in one stage (with compilers, dev tools), copy only the artifact to the final stage (slim image). Result: 1.2GB image becomes 200MB. Smaller images = faster deploys, smaller attack surface."

**"How do you handle secrets in Kubernetes?"**
> "Never bake secrets into Docker images. Use K8s Secrets (stored in etcd, base64 encoded) or external secret managers (AWS Secrets Manager, Vault). Mount secrets as environment variables or files in the pod."

**"What happens if a pod crashes?"**
> "K8s automatically restarts it (restartPolicy: Always). If it keeps crashing (CrashLoopBackOff), investigate logs: `kubectl logs pod-name`. For Spark: the driver requests a new executor pod from K8s to replace the failed one."

**Analogy:** Docker = a shipping container (same box, different trucks). K8s = the shipping port (routes containers, replaces damaged ones, scales fleet). Dockerfile = the packing instructions.

**Memory trick:** Docker = **D**elivers **O**bjects **C**onsistently, **K**8s = **K**eeps **E**verything **R**unning

---

### CI/CD for Data Pipelines

**Analogy:** CI/CD is like a car assembly line quality check. Every code change goes through automated inspections (tests) before reaching production. No human manually deploys code.

**CI/CD stages for a data pipeline:**
```
Developer pushes code
        |
    [CI: Continuous Integration]
    1. Lint Python code (flake8/ruff)
    2. Run unit tests (pytest)
    3. Validate SQL syntax
    4. Check dbt model compilation
    5. Build Docker image
        |
    [CD: Continuous Deployment]
    6. Deploy to staging
    7. Run integration tests (against test data)
    8. Data quality validation
    9. Promote to production
    10. Smoke test on production data
```

**Your implementation:**
- Healthcare: pytest with 141 tests, GitHub-hosted repo
- Nova: Schema validation + quality gates at each medallion layer

**Q: "How do you test data pipelines?"**

| Test type | What it tests | Example |
|---|---|---|
| **Unit test** | Individual functions | "Does `clean_column()` remove nulls correctly?" |
| **Integration test** | End-to-end pipeline | "Does Bronze->Silver->Gold produce expected output?" |
| **Data quality test** | Output data correctness | "Are there nulls in primary key? Row count in range?" |
| **Contract test** | Schema matches agreement | "Does output have expected columns and types?" |
| **Performance test** | Speed within SLA | "Does pipeline complete in <45 minutes?" |

---

### Every DE Tradeoff (Complete Reference)

**Q: "Walk me through a tradeoff you made."** -- This is the #1 senior-level question.

#### Tradeoff 1: Spark vs Pandas

| | Spark | Pandas |
|---|---|---|
| **Data size** | GB to TB | MB to low GB |
| **Execution** | Distributed cluster | Single machine |
| **Overhead** | High (cluster setup, JVM) | Zero |
| **Learning curve** | Steeper | Easier |
| **When to use** | >1GB, production pipelines | <1GB, exploration, prototyping |

**Analogy:** Pandas is a bicycle -- great for short trips, no setup. Spark is a bus -- overkill for one person, but essential when you're moving 50 people.

**Your answer:** "At Nomura, trade data was hundreds of thousands of rows daily with multi-way joins -- Pandas would run out of memory. Spark distributed the work across executors. But for my Healthcare project's 253K records, Pandas was sufficient for training -- I used Spark only when I needed window functions and complex aggregations."

#### Tradeoff 2: Parquet vs CSV vs JSON vs Avro

| Format | Type | Compression | Read speed | Schema | Best for |
|---|---|---|---|---|---|
| **Parquet** | Columnar | 65-80% | Fastest for analytics | Embedded | Analytics, Spark, data lakes |
| **CSV** | Row | None | Slow | None | Human-readable, small files |
| **JSON** | Row | None | Slow | Flexible | APIs, nested data, config |
| **Avro** | Row | Good | Medium | Schema registry | Kafka messages, streaming |
| **ORC** | Columnar | 60-70% | Fast (Hive) | Embedded | Hive-heavy environments |

**Analogy:** 
- **CSV** = handwritten notes (anyone can read, but slow to search)
- **Parquet** = indexed filing cabinet (fast lookup by column, but can't read with notepad)
- **JSON** = labeled boxes (flexible shape, but wastes space)

**Your answer:** "I use Parquet everywhere. At Nomura, switching from CSV to Parquet cut read times by 95%. The key advantage is columnar storage -- when a query only needs 3 of 50 columns, Parquet reads only those 3. CSV reads all 50."

#### Tradeoff 3: Snowflake vs Redshift vs BigQuery

| | Snowflake | Redshift | BigQuery |
|---|---|---|---|
| **Cloud** | Multi-cloud | AWS only | GCP only |
| **Compute/Storage** | Separated (scale independently) | Coupled (older) / Serverless (newer) | Separated |
| **Pricing** | Per-second compute + storage | Per-node (reserved) or per-query | Per-query (on-demand) |
| **Concurrency** | Excellent (virtual warehouses) | Limited without Serverless | Excellent |
| **Strength** | Multi-cloud, ease of use | AWS ecosystem integration | ML integration, unstructured data |
| **Your experience** | Nissan project | N/A | N/A |

**Your answer:** "I used Snowflake at Nissan because it separates compute and storage -- we could scale our warehouse up during daily loads and scale down after. The multi-cloud support also meant no vendor lock-in. If the company was all-in on AWS, Redshift Serverless would be equally valid."

#### Tradeoff 4: Airflow vs Step Functions vs Prefect vs Dagster

| | Airflow | Step Functions | Prefect | Dagster |
|---|---|---|---|---|
| **Type** | Open-source orchestrator | AWS managed | Modern orchestrator | Modern orchestrator |
| **DAG definition** | Python | JSON/YAML | Python (decorator-based) | Python (asset-based) |
| **Learning curve** | Medium | Low | Low | Medium |
| **Best for** | Complex multi-system ETL | AWS-native simple workflows | Python-first teams | Data-asset-focused teams |
| **Scalability** | High (CeleryExecutor) | Very high (serverless) | High (cloud) | High |
| **Your experience** | AutoSys (similar) | Nissan project | N/A | N/A |

**Your answer:** "At Nissan I used Step Functions because the pipeline was AWS-native (Lambda + S3 + Snowflake) -- serverless orchestration was perfect. For a more complex multi-system pipeline like Nomura's (Spark + HDFS + multiple destinations), I'd use Airflow for its flexibility and Python-based DAGs."

#### Tradeoff 5: Delta Lake vs Apache Iceberg vs Apache Hudi

| | Delta Lake | Apache Iceberg | Apache Hudi |
|---|---|---|---|
| **Creator** | Databricks | Netflix | Uber |
| **ACID** | Yes | Yes | Yes |
| **Time travel** | Yes | Yes | Yes |
| **Engine support** | Spark-native, growing Trino/Flink | Engine-agnostic (Spark, Trino, Flink) | Spark, Flink |
| **Schema evolution** | Excellent | Excellent | Good |
| **Strength** | Spark ecosystem, OPTIMIZE/ZORDER | Engine portability, partition evolution | Upsert-heavy workloads |
| **Your experience** | Nova project | N/A | N/A |

**Your answer:** "I chose Delta Lake for Nova because it's native to the Spark ecosystem we were already using. The OPTIMIZE and ZORDER commands are essential for query performance. If the requirement was engine-agnostic (query with both Spark and Trino), I'd consider Iceberg. If the workload was primarily upserts on streaming data, Hudi would be worth evaluating."

#### Tradeoff 6: Star Schema vs OBT (One Big Table)

| | Star Schema | One Big Table (OBT) |
|---|---|---|
| **Structure** | Fact + dimension tables | Single denormalized table |
| **Joins** | Required (fact JOIN dims) | None |
| **Query speed** | Good (with proper indexing) | Fastest (no joins) |
| **Storage** | Less (normalized dims) | More (repeated dim values) |
| **Maintenance** | More complex (multiple tables) | Simpler (one table) |
| **Best for** | Analytics with many query patterns | Dashboards with fixed queries |

**Your answer:** "At Nomura we used star schema because portfolio managers query the data in many different ways -- by instrument, by desk, by date, by counterparty. An OBT would require pre-deciding the grain. Star schema is more flexible. But for a specific dashboard with known queries, OBT can be simpler and faster."

---

### Data Governance (Know the Vocabulary)

| Term | Meaning | Your implementation |
|---|---|---|
| **Data Catalog** | Searchable inventory of all datasets | Nova: Gold layer tables documented with schema |
| **Data Lineage** | Track where data came from and where it goes | Nova: Bronze->Silver->Gold with transformation metadata |
| **Data Classification** | Label data sensitivity (PII, PHI, public) | Healthcare: patient data never logged (PII protection) |
| **Access Control** | Who can read/write which data | Healthcare: JWT authentication, role-based access |
| **Data Retention** | How long to keep data | Delta Lake time travel: 30-day default retention |
| **Audit Trail** | Log of who accessed what, when | Healthcare: 7-layer middleware logs all API requests |

---

### The "I Haven't Used X" Bridge Framework

When they ask about a tool you haven't used directly:

| They ask about | You bridge to | Script |
|---|---|---|
| **Airflow** | AutoSys | "Same paradigm -- DAGs, dependencies, retries. Airflow uses Python, AutoSys uses JIL. I'd ramp up in days." |
| **dbt** | PySpark SQL | "Same concept -- modular SQL transforms with testing. dbt pushes down to warehouse, I pull into Spark. Both version-controlled." |
| **Flink** | Spark Streaming | "Both process streams. Flink is true event-at-a-time, Spark is micro-batch. I'd learn Flink's API but the concepts transfer." |
| **Terraform** | Docker/K8s YAML | "Infrastructure-as-code principle is the same. I define K8s resources in YAML, Terraform uses HCL for cloud resources." |
| **Great Expectations** | Custom quality checks | "Same validation patterns. GE has a framework; I wrote the same checks manually (null %, range, uniqueness)." |
| **Databricks** | PySpark + Delta Lake | "Databricks is managed Spark + Delta Lake + notebooks. I already use PySpark and Delta Lake -- Databricks wraps these with a UI." |
| **Snowpipe** | Lambda + S3 triggers | "Same pattern: file lands in S3, auto-triggers ingestion. Snowpipe is native to Snowflake, I built the same with Lambda." |
| **Kafka Connect** | Custom producers/consumers | "Connect is managed connectors. I built the same integration manually -- the concepts (sources, sinks, transforms) are identical." |

**The magic phrase:** "I haven't used [X] directly, but the underlying concept is identical to [Y] which I've used extensively. The API would be new, but the engineering principles transfer directly. I'd be productive within [timeframe]."

---

## PART 9: SPARK INTERNALS (The #1 DE Interview Topic)

> If you understand how Spark EXECUTES your code, you can answer any optimization question. This is what separates a "PySpark user" from a "Spark engineer."

### How Spark Executes Your Code (The Full Picture)

```
Your PySpark Code
    |
[Logical Plan] -- What you WANT to do (abstract)
    |
[Catalyst Optimizer] -- Rewrites your plan to be more efficient
    |
[Physical Plan] -- HOW Spark will actually do it
    |
[DAG of Stages] -- Groups of tasks separated by shuffles
    |
[Tasks] -- Individual units of work, one per partition
    |
[Executors] -- JVM processes on worker nodes that run tasks
```

**Analogy:** You write a recipe (logical plan). A chef (Catalyst) rewrites it to be more efficient (physical plan). The kitchen is organized into stations (stages). Each cook (executor) handles one dish (task) at a time.

### Jobs, Stages, and Tasks

**Job** = triggered by an ACTION (`.count()`, `.collect()`, `.write()`)
**Stage** = a group of tasks that can run without shuffling data
**Task** = one unit of work on one partition

```python
# This code creates 1 Job, 2 Stages, and N tasks
df = spark.read.parquet("trades/")          # Stage 1: read
result = df.groupBy("instrument_id")        # <-- SHUFFLE boundary (new stage)
            .agg(sum("amount"))             # Stage 2: aggregate
result.write.parquet("output/")             # ACTION triggers the job
```

**Stage boundaries happen at SHUFFLES.** Shuffles happen when data needs to move between partitions:
- `groupBy()` -- data with same key must go to same partition
- `join()` -- matching rows must be co-located
- `repartition()` -- explicitly redistributing data
- `orderBy()` -- global sort requires all data to move

**Q: "Why are shuffles expensive?"**
> "A shuffle is Spark's most expensive operation. It requires: (1) writing all map-side data to disk, (2) network transfer across nodes, (3) reading and merging on the reduce side. For a 100GB dataset with 200 partitions, a shuffle moves 100GB over the network. I minimize shuffles by: broadcast joins for small tables, pre-partitioning data, and using coalesce instead of repartition when reducing partitions."

### The Catalyst Optimizer (What Makes Spark Smart)

Catalyst automatically optimizes your queries. You don't need to do it manually.

**Predicate Pushdown:** Filters are pushed as close to the data source as possible.
```python
# You write:
df = spark.read.parquet("trades/").filter(col("trade_date") == "2024-01-01")

# Spark actually does:
# Read ONLY the 2024-01-01 partition from Parquet (skips all other files)
# This is predicate pushdown -- the filter happens at read time, not after
```

**Column Pruning:** Only reads the columns you actually use.
```python
# You write:
df = spark.read.parquet("trades/").select("trade_id", "amount")

# Spark actually does:
# Reads ONLY trade_id and amount columns from Parquet (skips 48 other columns)
# Parquet's columnar format makes this extremely efficient
```

**Join Reordering:** Puts the smaller table on the build side of a hash join.

**Constant Folding:** Pre-computes constant expressions at compile time.

### Memory Model (Why Your Jobs OOM)

Each Spark executor has memory divided into:

```
Executor Memory (e.g., 4GB)
|
+-- Execution Memory (shuffle, sort, join) -- 60% default
|     This is where shuffles, joins, and aggregations happen
|     If full: spills to disk (SLOW)
|
+-- Storage Memory (cache, broadcast) -- 40% default
|     Where .cache() and broadcast variables live
|     If full: evicts cached data
|
+-- User Memory (your Python objects) -- 300MB overhead
|     Your UDFs, variables, etc.
|
+-- Reserved (Spark internals) -- 300MB fixed
```

**Q: "Your job is running out of memory. What do you do?"**
> 1. **Check Spark UI**: Are tasks spilling to disk? (look for "Spill (Disk)" in Stages tab)
> 2. **Data skew?** One partition has 10x more data than others. Fix: salted join or repartition
> 3. **Too many partitions cached?** `.unpersist()` DataFrames you no longer need
> 4. **Broadcast too large?** Default 10MB threshold. If broadcasting 500MB table, that's OOM
> 5. **Increase memory**: `spark.executor.memory=8g` (last resort -- fix the root cause first)

### Data Skew (The Silent Killer)

**What is it?** When one partition has much more data than others. One task takes 10x longer, making the whole stage wait.

```
Normal:  Partition 1: 1M rows | Partition 2: 1M rows | Partition 3: 1M rows
Skewed:  Partition 1: 100K    | Partition 2: 100K    | Partition 3: 9.8M   <-- bottleneck!
```

**Common causes:**
- `groupBy("country")` when 80% of data is from one country
- `join` on a key with null values (all nulls go to one partition)
- Uneven partitioning by date (Black Friday has 10x normal volume)

**Solutions:**
```python
# Solution 1: Salted join (split hot key across multiple partitions)
df_skewed = df.withColumn("salt", (rand() * 10).cast("int"))
df_dimension = df_dim.crossJoin(spark.range(10).withColumnRenamed("id", "salt"))
result = df_skewed.join(df_dimension, ["key", "salt"])

# Solution 2: Adaptive Query Execution (Spark 3.0+)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
# AQE detects skew at runtime and splits large partitions automatically

# Solution 3: Broadcast the small side
from pyspark.sql.functions import broadcast
result = big_table.join(broadcast(small_table), "key")
# Sends small_table to every executor -- no shuffle at all
```

### Adaptive Query Execution (AQE) -- Spark 3.0+ Game Changer

**What it does:** Re-optimizes the query plan AT RUNTIME based on actual data statistics (not just estimates).

| Feature | What it does | Before AQE |
|---|---|---|
| **Coalesce shuffle partitions** | Merges small partitions after shuffle | You manually set `spark.sql.shuffle.partitions=200` |
| **Skew join optimization** | Splits skewed partitions automatically | You manually salt keys |
| **Dynamic join strategy** | Switches to broadcast join if table is small enough | You manually add `broadcast()` |

```python
# Enable AQE (should ALWAYS be on in Spark 3.0+)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

**Your interview answer:**
> "I always enable AQE in Spark 3.x. It handles the three most common performance issues automatically: coalescing small partitions after shuffles, splitting skewed partitions, and dynamically switching to broadcast joins. Before AQE, I had to manually tune shuffle partitions and salt skewed keys. AQE does this at runtime with actual data sizes, not estimates."

### Spark Caching Strategy

```python
# When to cache:
df.cache()    # When you reuse a DataFrame multiple times
df.persist(StorageLevel.MEMORY_AND_DISK)  # When data might not fit in memory

# When NOT to cache:
# - DataFrames used only once (caching adds overhead)
# - Very large DataFrames (evicts other useful cached data)
# - Before a filter (cache AFTER filtering to store less data)

# Good pattern:
filtered_df = raw_df.filter(col("active") == True)
filtered_df.cache()    # Cache the FILTERED version (smaller)
filtered_df.count()    # Trigger the cache

# Always unpersist when done:
filtered_df.unpersist()
```

**Spark Counter-Question Drill-Down:**

**Level 4:** "How do you minimize shuffles?"
> "Three ways: (1) Broadcast joins -- send the small table to every executor, no shuffle needed. (2) Pre-partition data by the join key. (3) Use coalesce() instead of repartition() when reducing partitions -- coalesce avoids a full shuffle."

**Level 5:** "What if the 'small' table is 500MB? Is broadcast still viable?"
> "Default broadcast threshold is 10MB, tunable to ~100MB safely. At 500MB, broadcasting to 50 executors means 25GB total memory. I'd either: (1) filter the dimension table first to reduce size, (2) use a sort-merge join with AQE enabled for automatic skew handling, or (3) bucket both tables by the join key so they're pre-co-located."

**Level 5 follow-up:** "What happens when you call .collect() on a 100GB DataFrame?"
> "It tries to pull all 100GB to the driver's memory. The driver has maybe 4-8GB. Result: OutOfMemoryError. Never .collect() large DataFrames. Use .take(10) to sample, .write() to persist results, or aggregate first and THEN collect the small result."

**Level 5 follow-up:** "Explain transformations vs actions."
> "Transformations are LAZY -- they build a plan but don't execute (filter, select, join, groupBy). Actions TRIGGER execution (count, collect, write, show). Spark waits until an action to optimize and run the full chain. This lazy evaluation lets Catalyst optimize the entire pipeline, not just individual steps."

**Memory trick:** SPARK = **S**tages **P**artition **A**cross, **R**eading in **K**lusters

---

## PART 10: AWS SERVICES FOR DATA ENGINEERING

> Your Nissan project used AWS (Lambda, Step Functions, S3, Snowflake). Know these cold.

### AWS Services Comparison (What DE Uses)

| Service | What it does | When to use | Your experience |
|---|---|---|---|
| **S3** | Object storage (files) | Store raw/processed data, data lake | Nissan: landing zone for files |
| **Lambda** | Serverless functions (15 min max) | Small transforms, triggers, validation | Nissan: schema validation |
| **Step Functions** | Workflow orchestration | Multi-step serverless pipelines | Nissan: ETL orchestration |
| **EMR** | Managed Spark/Hadoop cluster | Large-scale data processing | Nomura: Spark on EMR |
| **Glue** | Serverless Spark ETL | Simple ETL without managing clusters | Alternative to EMR for small jobs |
| **Redshift** | Data warehouse | SQL analytics at scale | Alternative to Snowflake |
| **Kinesis** | Real-time streaming | Ingest streaming data | Alternative to Kafka on AWS |
| **Athena** | Serverless SQL on S3 | Ad-hoc queries on data lake files | Query Parquet files without a cluster |
| **CloudWatch** | Monitoring and logging | Pipeline monitoring and alerts | Nissan: Lambda monitoring |
| **IAM** | Access management | Control who can access what | Nissan: Lambda execution roles |

### Q: "Why Lambda + Step Functions instead of Airflow?"

> "The Nissan pipeline was fully AWS-native: S3 triggers, Lambda processing, Snowflake loading. Step Functions was the natural choice because:
> 1. **Serverless**: Zero infrastructure to manage (no Airflow server to maintain)
> 2. **Pay-per-use**: Only pay when steps execute (Airflow runs 24/7)
> 3. **Visual**: Step Functions has a visual workflow designer for non-technical stakeholders
> 4. **AWS integration**: Native integration with Lambda, S3, SNS
>
> Trade-off: Step Functions is limited to AWS. For a multi-cloud or complex pipeline (like Nomura's Spark jobs), I'd use Airflow for its flexibility."

### Q: "S3 vs HDFS?"

> "S3 is object storage (accessed via HTTP, eventual consistency, infinite scale, pay-per-GB). HDFS is file storage (block-based, strong consistency, requires managing a cluster).
>
> At Nomura, we migrated from HDFS to S3-compatible storage (MinIO) during the YARN-to-K8s migration. The benefit: decoupled compute and storage. Spark executors can scale independently from storage. The trade-off: slightly higher latency per read, but the flexibility is worth it."

### Q: "When would you use Glue vs EMR?"

| | AWS Glue | EMR |
|---|---|---|
| **Management** | Fully serverless | You manage the cluster |
| **Cost** | Per-DPU-hour ($0.44) | Per-instance-hour ($0.20+) |
| **Customization** | Limited | Full control |
| **Scale** | Auto-scales | You configure scaling |
| **Best for** | Simple ETL, catalog crawling | Complex processing, ML, custom libs |

> "Glue for simple CSV-to-Parquet transforms and catalog management. EMR for anything requiring custom libraries, complex Spark tuning, or ML workloads. At Nomura, we used EMR because we needed fine-grained Spark configuration and custom JAR dependencies."

### Q: "Explain S3 storage classes."

| Class | Use case | Cost | Retrieval |
|---|---|---|---|
| **S3 Standard** | Frequently accessed data | $0.023/GB | Instant |
| **S3 IA (Infrequent Access)** | Data accessed monthly | $0.0125/GB | Instant |
| **S3 Glacier** | Archive (rarely accessed) | $0.004/GB | Minutes to hours |
| **S3 Glacier Deep Archive** | Long-term archive | $0.00099/GB | 12-48 hours |

> "In a data lake: Bronze layer in S3 Standard (frequently queried). Silver/Gold in S3 Standard. Old partitions (>90 days) lifecycle to S3 IA. Compliance archives (>1 year) to Glacier. This saves ~40% on storage costs."

---

## PART 11: SPARK CONFIGURATION CHEAT SHEET

> The exact configs interviewers ask about. Know what each does and when to tune it.

| Config | Default | What it does | When to change |
|---|---|---|---|
| `spark.executor.memory` | 1g | Memory per executor | Increase for large joins/shuffles |
| `spark.executor.cores` | 1 | CPU cores per executor | 3-5 cores is optimal |
| `spark.executor.instances` | 2 | Number of executors | Scale based on data volume |
| `spark.sql.shuffle.partitions` | 200 | Partitions after shuffle | Reduce for small data, increase for large |
| `spark.sql.adaptive.enabled` | false (2.x), true (3.x) | Enable AQE | ALWAYS set to true |
| `spark.sql.autoBroadcastJoinThreshold` | 10MB | Max table size for broadcast | Increase to 100MB for medium dims |
| `spark.default.parallelism` | 2x cores | Default partitions for RDDs | Match to your data size |
| `spark.memory.fraction` | 0.6 | % of heap for execution+storage | Increase if heavy caching |
| `spark.serializer` | JavaSerializer | How data is serialized | Use KryoSerializer (10x faster) |
| `spark.sql.files.maxPartitionBytes` | 128MB | Max bytes per file partition | Keep at 128-256MB |

**Your standard production config:**
```python
spark = SparkSession.builder \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "4") \
    .config("spark.executor.instances", "10") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .config("spark.sql.adaptive.skewJoin.enabled", "true") \
    .config("spark.sql.autoBroadcastJoinThreshold", "100MB") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .getOrCreate()
```

---

## PART 12: STATISTICS & ANALYTICS (For Data Analyst / Analytics Roles)

> Every DA interview tests statistics. You don't need a PhD -- just these core concepts explained clearly.

### Descriptive Statistics (Know These Cold)

| Measure | What it tells you | When to use | Python |
|---|---|---|---|
| **Mean** | Average value | Symmetric data, no outliers | `df["col"].mean()` |
| **Median** | Middle value (50th percentile) | Skewed data, has outliers | `df["col"].median()` |
| **Mode** | Most frequent value | Categorical data | `df["col"].mode()` |
| **Std Dev** | How spread out values are | Understanding variability | `df["col"].std()` |
| **Variance** | Std dev squared | Statistical calculations | `df["col"].var()` |
| **IQR** | P75 - P25 (middle 50% spread) | Outlier detection | `df["col"].quantile(0.75) - df["col"].quantile(0.25)` |

**Q: "When do you use mean vs median?"**
> "Mean for symmetric data (heights, test scores). Median for skewed data (salaries, house prices). Example: if 10 employees earn $50K and the CEO earns $5M, the mean salary is $500K (misleading), but the median is $50K (accurate). In data quality checks, I compare mean and median -- if they differ by >20%, the distribution is skewed and I investigate outliers."

**Outlier Detection:**
```python
# IQR method (standard approach)
Q1 = df["amount"].quantile(0.25)
Q3 = df["amount"].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
outliers = df[(df["amount"] < lower) | (df["amount"] > upper)]
```

### Correlation (What Moves Together)

| Value | Meaning | Example |
|---|---|---|
| **+1.0** | Perfect positive (both go up) | Height and weight |
| **0.0** | No relationship | Shoe size and salary |
| **-1.0** | Perfect negative (one up, other down) | Price and demand |

```python
# Correlation matrix
df[["bmi", "age", "blood_pressure", "diabetes_risk"]].corr()

# Your Healthcare project:
# BMI and diabetes have correlation ~0.4 (moderate positive)
# This is why BMI is a top feature in your XGBoost model
```

**Q: "Does correlation mean causation?"**
> "No. Ice cream sales and drowning deaths are correlated (both increase in summer), but ice cream doesn't cause drowning. In my Healthcare project, BMI correlates with diabetes risk, but we say 'BMI is ASSOCIATED with higher risk,' not 'BMI CAUSES diabetes.' The model finds patterns, not causes."

### A/B Testing (Every Company Asks This)

**What is it?** Split users into two groups. Group A sees the current version. Group B sees a change. Measure which performs better.

**The process:**
```
1. Hypothesis: "Changing the button color to green will increase clicks by 5%"
2. Split: 50% users see red button (control), 50% see green (treatment)
3. Metric: Click-through rate (CTR)
4. Duration: Run for 2 weeks (enough data for statistical significance)
5. Analyze: Is the difference real or just random noise?
```

**Statistical significance:**
- **p-value < 0.05** = the result is statistically significant (not likely due to chance)
- **p-value > 0.05** = no significant difference (could be random)
- **Confidence interval** = range where the true value likely falls

```python
from scipy import stats

# Two-sample t-test
control_clicks = [12, 15, 14, 13, 16, ...]
treatment_clicks = [18, 20, 17, 19, 21, ...]

t_stat, p_value = stats.ttest_ind(control_clicks, treatment_clicks)
if p_value < 0.05:
    print("Significant! Green button wins.")
else:
    print("Not significant. Keep the red button.")
```

**Q: "What can go wrong with A/B tests?"**
> 1. **Sample size too small**: Not enough data to detect a real difference
> 2. **Running too short**: Weekday vs weekend patterns not captured
> 3. **Multiple comparisons**: Testing 20 metrics, one will be "significant" by chance
> 4. **Selection bias**: Groups not truly random
> 5. **Novelty effect**: Users click the new button just because it's new

### KPIs and Business Metrics (Data Analyst Must-Know)

| KPI | Formula | Domain |
|---|---|---|
| **Conversion Rate** | Purchases / Visitors x 100 | E-commerce |
| **Churn Rate** | Lost Customers / Total Customers x 100 | SaaS, subscription |
| **DAU/MAU** | Daily Active Users / Monthly Active Users | Product engagement |
| **ARPU** | Total Revenue / Total Users | Revenue per user |
| **LTV** | ARPU x Average Customer Lifespan | Customer lifetime value |
| **CAC** | Marketing Spend / New Customers Acquired | Cost to acquire |
| **NPS** | % Promoters - % Detractors | Customer satisfaction |
| **SLA Compliance** | Tasks Within SLA / Total Tasks x 100 | Operations |

**Q: "How do you choose which KPI to track?"**
> "Start with the business question. 'Are we growing?' -> DAU/MAU. 'Are we profitable?' -> LTV:CAC ratio (should be >3:1). 'Are customers happy?' -> NPS and churn rate. I always define KPIs BEFORE building dashboards -- data without context is just numbers."

### Tableau / Power BI Concepts (Know the Vocabulary)

| Concept | What it is | When asked about it |
|---|---|---|
| **Dimension** | Categorical data (region, product, date) | GROUP BY equivalent |
| **Measure** | Numerical data (sales, count, avg) | SUM/AVG equivalent |
| **Calculated Field** | Custom formula in the tool | Like a SQL computed column |
| **LOD Expression** | Level of Detail -- compute at a different grain | FIXED, INCLUDE, EXCLUDE |
| **Filter Order** | Extract -> Data Source -> Context -> Dimension -> Measure | Why filters behave unexpectedly |
| **Dashboard Action** | Click/hover triggers filter/highlight/URL | Interactive dashboards |
| **Data Blending** | Join data from different sources in Tableau | Like a SQL JOIN but visual |

**Your bridge answer:**
> "I've built dashboards using Next.js with custom charts (my Healthcare project has interactive health predictions). The concepts transfer: I understand dimensions vs measures, filtering, aggregation, and drill-down. I'd learn Tableau's specific UI in a week -- the analytical thinking is the same."

---

## PART 13: ML ENGINEERING & MLOPS (For AI/ML Data Engineer Roles)

> If the role mentions "AI" or "ML," they'll test these concepts.

### Model Deployment Patterns

| Pattern | How it works | When to use | Your implementation |
|---|---|---|---|
| **REST API** | Model loaded in FastAPI, predictions via HTTP | Real-time, low latency | Healthcare: FastAPI serves XGBoost predictions |
| **Batch Inference** | Run model on a batch of data, save results | Large-scale scoring, not time-critical | Healthcare: bulk prediction endpoint |
| **Streaming** | Model runs on each event as it arrives | Real-time scoring per event | Nova: could score recommendations per click |
| **Edge** | Model runs on device (mobile, IoT) | No network, low latency | Not applicable to your projects |

**Your Healthcare deployment:**
```python
# Model loaded ONCE at startup (not per-request)
@app.on_event("startup")
def load_models():
    global models
    models = initialize_models()  # Load XGBoost from .pkl files

# Each prediction: ~9ms latency
@app.post("/api/predict/diabetes")
async def predict_diabetes(data: HealthInput):
    features = preprocess(data)
    prediction = models["diabetes"].predict_proba(features)
    return {"risk_score": float(prediction[0][1])}
```

### Experiment Tracking

**What it is:** Track every model training run: hyperparameters, metrics, code version, data version.

**Why it matters:** "Which model did we deploy? What data was it trained on? Can we reproduce last month's results?" Without tracking, it's chaos.

| Tool | What it does | Open source? |
|---|---|---|
| **MLflow** | Track experiments, package models, deploy | Yes |
| **Weights & Biases** | Track experiments, visualize, collaborate | Freemium |
| **Neptune** | Track experiments, compare runs | Freemium |

```python
# MLflow example (what you'd write in an interview):
import mlflow

with mlflow.start_run(run_name="xgboost_diabetes_v3"):
    # Log parameters
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("scale_pos_weight", 3.0)
    mlflow.log_param("train_size", 253680)

    # Train model
    model = XGBClassifier(**params)
    model.fit(X_train, y_train)

    # Log metrics
    mlflow.log_metric("accuracy", 0.85)
    mlflow.log_metric("auc_roc", 0.89)
    mlflow.log_metric("f1_score", 0.78)

    # Log model artifact
    mlflow.xgboost.log_model(model, "diabetes_model")
```

### Feature Stores

**What it is:** A centralized repository of curated features that can be reused across models and teams.

**Analogy:** Like a shared ingredient pantry in a restaurant. Instead of each chef preparing their own garlic, everyone uses the same pre-minced garlic from the pantry. Consistency + efficiency.

| Concept | Meaning |
|---|---|
| **Feature** | A processed input to a model (e.g., "avg_bmi_last_30_days") |
| **Online Store** | Low-latency serving for real-time predictions (Redis/DynamoDB) |
| **Offline Store** | Batch serving for training (S3/data warehouse) |
| **Feature Pipeline** | Code that computes features from raw data |
| **Point-in-Time Join** | Join features AS OF a specific timestamp (prevent data leakage) |

**Your bridge answer:**
> "In my Healthcare project, features are computed inline during prediction (BMI, age, blood pressure directly from user input). In Nova, features are pre-computed in the Gold layer (user_avg_rating, movie_popularity_score). These Gold tables are conceptually a feature store -- a curated set of ML-ready features. For a larger team, I'd formalize this with Feast or Tecton."

### Model Monitoring (Post-Deployment)

| What to monitor | How | Alert threshold |
|---|---|---|
| **Prediction latency** | P50, P95, P99 response times | P95 > 100ms |
| **Prediction distribution** | Are predictions shifting? | >10% change vs baseline |
| **Feature drift** | Are input distributions changing? | PSI > 0.2 |
| **Data quality** | Null rates, out-of-range values | >1% nulls in required fields |
| **Model accuracy** | Compare predictions to actual outcomes | Accuracy drops >5% |

**Your Healthcare project answer:**
> "I monitor model health through the 7-layer middleware stack. Every prediction is logged with latency metrics. If prediction distributions shift (e.g., suddenly predicting 80% positive instead of the usual 30%), an alert fires. For retraining, I'd compare the BRFSS training distribution against recent API inputs to detect feature drift."

---

## PART 14: DATA ANALYST SPECIFIC PATTERNS

### The "Walk Me Through Your Analysis" Framework (CRISP-DM)

Every DA answer should follow this structure:

```
1. BUSINESS UNDERSTANDING: What problem are we solving?
   "The marketing team wants to reduce churn by identifying at-risk customers."

2. DATA UNDERSTANDING: What data do we have?
   "Customer table (demographics), transactions (last 12 months), support tickets."

3. DATA PREPARATION: How did you clean and transform?
   "Joined 3 tables, handled nulls (15% in phone number -- not impactful),
    created features: days_since_last_purchase, total_spend_90d, support_ticket_count."

4. ANALYSIS: What did you find?
   "Customers with 0 purchases in 60 days AND >2 support tickets have 78% churn rate.
    That's 3x the overall churn rate of 26%."

5. PRESENTATION: How did you communicate results?
   "Built a dashboard with churn risk tiers. Shared with marketing in a 15-min presentation.
    Recommended a targeted retention campaign for the 'high risk' tier (2,300 customers)."

6. ACTION: What happened?
   "Marketing ran the campaign. Churn in the targeted segment dropped from 78% to 45%.
    Estimated revenue saved: $340K over 6 months."
```

### Common DA Interview Questions

**Q: "You have a dataset of 1M customer transactions. Where do you start?"**
> 1. **Shape and size**: How many rows, columns? `df.shape`
> 2. **Data types**: Are dates stored as strings? Are numeric columns correct? `df.dtypes`
> 3. **Nulls**: Which columns have missing data? How much? `df.isnull().sum()`
> 4. **Distributions**: Are there outliers? Is data skewed? `df.describe()`
> 5. **Cardinality**: How many unique values per column? `df.nunique()`
> 6. **Sample**: Look at 5-10 rows. Does the data make sense? `df.head(10)`

**Q: "Sales dropped 15% last month. What do you investigate?"**
> 1. **Is it real?** Check data quality -- any missing data, pipeline issues, duplicate removals?
> 2. **Is it seasonal?** Compare to same month last year, not just last month
> 3. **Where is the drop?** Slice by region, product, channel, customer segment
> 4. **What changed?** New competitor? Price increase? Marketing campaign ended?
> 5. **How big is the impact?** Is 15% within normal variation or truly anomalous?
> 6. **Present findings**: "Sales dropped 15% overall, but it's concentrated in the West region (-32%). East and Central are flat. The West region's top sales rep left in March."

**Q: "How do you handle missing data?"**

| Strategy | When to use | Code |
|---|---|---|
| **Drop rows** | <5% missing, missing at random | `df.dropna()` |
| **Fill with mean/median** | Numeric, missing at random | `df["col"].fillna(df["col"].median())` |
| **Fill with mode** | Categorical data | `df["col"].fillna(df["col"].mode()[0])` |
| **Forward fill** | Time series (use last known value) | `df["col"].fillna(method="ffill")` |
| **Flag as missing** | Missingness itself is informative | `df["col_missing"] = df["col"].isnull().astype(int)` |
| **Model-based imputation** | Complex patterns | `from sklearn.impute import KNNImputer` |

> "In my Healthcare project, I analyzed missing patterns before deciding. Some features had <1% missing (dropped those rows). Age had 0% missing. The BRFSS dataset was already clean, but I validated this explicitly in my test suite (141 tests include null checks)."

---

## PART 15: SNOWFLAKE DEEP-DIVE (You Used This at Nissan)

### Snowflake Architecture

```
[Cloud Services Layer]  -- Query optimization, metadata, security
         |
[Virtual Warehouses]    -- Compute (XS, S, M, L, XL, 2XL...)
         |
[Storage Layer]         -- Compressed columnar storage (micro-partitions)
```

**Key concept:** Compute and storage are SEPARATED. You can scale your warehouse up for a big job, then scale down. You only pay for compute when queries are running.

### Snowflake Concepts Every DE Must Know

| Concept | What it is | Your Nissan experience |
|---|---|---|
| **Virtual Warehouse** | A compute cluster (XS to 4XL) | "We used Medium for daily loads, XS for ad-hoc queries" |
| **Database/Schema** | Logical grouping of tables | "RAW schema for landing, CLEAN for transformed" |
| **Stage** | Location for files before loading (internal or S3) | "S3 external stage pointing to our landing zone" |
| **COPY INTO** | Bulk load from stage to table | "Our primary ingestion command" |
| **Micro-partitions** | 50-500MB compressed columnar chunks (automatic) | "Snowflake auto-partitions, no manual config" |
| **Clustering Key** | Hint to co-locate similar data | "Clustered by trade_date for time-range queries" |
| **Time Travel** | Query data as of a past timestamp (1-90 days) | "Used for debugging data issues" |
| **Zero-Copy Clone** | Instant copy of a table (no data duplicated) | "Cloned production to dev for testing" |
| **Streams** | CDC (change data capture) on a table | "Track INSERTs/UPDATEs/DELETEs for incremental processing" |
| **Tasks** | Scheduled SQL execution (like a mini-Airflow) | "Hourly aggregation tasks" |
| **Snowpipe** | Auto-ingest files as they land in S3 | "Alternative to our Lambda trigger" |
| **Data Sharing** | Share tables with other Snowflake accounts (no copy) | "Not used at Nissan, but know the concept" |

### Key Snowflake Interview Questions

**Q: "How does Snowflake handle concurrency?"**
> "Each virtual warehouse is an independent compute cluster. If two teams run heavy queries simultaneously, you create separate warehouses so they don't compete for resources. This is Snowflake's killer feature vs Redshift -- no query queuing, just spin up another warehouse."

**Q: "What are micro-partitions?"**
> "Snowflake automatically divides table data into 50-500MB compressed chunks called micro-partitions. Each partition stores column-level metadata (min/max, null count, distinct count). When you query `WHERE date = '2024-01-01'`, Snowflake checks metadata and skips partitions that can't contain that date. This is called PRUNING -- similar to Spark's predicate pushdown with Parquet."

**Q: "When do you use a clustering key?"**
> "When your table is large (>1TB) and queries consistently filter on a specific column (like date or region). Clustering co-locates similar values in the same micro-partitions, improving pruning. For our daily trade data at Nissan, we clustered by trade_date because 95% of queries filtered by date range."

**Q: "Explain Snowflake's Time Travel."**
```sql
-- Query data as it was 1 hour ago
SELECT * FROM trades AT (OFFSET => -3600);

-- Query data as of a specific timestamp
SELECT * FROM trades AT (TIMESTAMP => '2024-01-01 06:00:00');

-- Restore a dropped table
UNDROP TABLE trades;
```

**Snowflake Counter-Question Drill-Down:**

**Level 5:** "How do you optimize a slow Snowflake query?"
> "Step 1: Check the query profile (Snowflake UI). Look for: (a) full table scans (add clustering key or WHERE clause), (b) spilling to storage (increase warehouse size), (c) large joins (filter before joining), (d) high remote I/O (data not pruned). Step 2: EXPLAIN the query. Step 3: Consider materializing complex CTEs as temp tables."

**Why Snowflake not Redshift?** Snowflake separates compute/storage (scale independently), handles concurrency natively (separate warehouses), and is multi-cloud. Redshift couples compute/storage (older model) and requires manual concurrency management.

**Analogy:** Traditional warehouse (Redshift) = owning a factory (pay 24/7). Snowflake = renting factory time by the hour. Need a bigger factory? Scale up for one hour, scale back down.

**Memory trick:** Snowflake = **S**eparated **N**odes, **O**n-demand **W**arehouses, **F**ast **L**oads, **A**uto **K**lustering, **E**lastic
> "I used Time Travel at Nissan for debugging. When a data issue was reported, I'd compare current data with yesterday's snapshot to find when the problem was introduced."

---

## PART 16: DATA ARCHITECTURE PATTERNS

### Lambda Architecture

```
[Source Data]
    |
+---+---+
|       |
[Batch Layer]           [Speed Layer]
Spark batch job         Spark Structured Streaming
Runs daily              Runs continuously
Complete + accurate     Approximate + fast
    |                       |
    +-------+-------+-------+
            |
    [Serving Layer]
    Merge batch + real-time views
    Query: use real-time until batch catches up
```

**When to use:** When you need both historical accuracy AND real-time data. The batch layer re-computes everything daily (always correct). The speed layer handles what happened since the last batch run (fast but approximate).

**Trade-off:** Complex -- you maintain two codepaths (batch AND streaming) for the same data.

### Kappa Architecture (Simpler Alternative)

```
[Source Data]
    |
[Kafka]
    |
[Stream Processing Only]
    Spark Structured Streaming / Flink
    Process everything as a stream
    Replay from Kafka for reprocessing
    |
[Serving Layer]
```

**When to use:** When streaming can handle all processing. No separate batch layer. Replay Kafka for historical reprocessing.

**Trade-off:** Simpler architecture, but requires Kafka retention long enough for replays. Not suitable if batch corrections are frequent.

**Your answer:** "Nova uses a Kappa-like pattern: events flow through Kafka into Spark Structured Streaming into Delta Lake. For reprocessing, we replay from Kafka. We don't maintain a separate batch path because Delta Lake's ACID guarantees give us the correctness that Lambda's batch layer provides."

### Data Mesh (Organizational Pattern)

**What it is:** Instead of one central data team owning all pipelines, each domain team owns their own data products.

| Centralized (traditional) | Data Mesh |
|---|---|
| One data team builds all pipelines | Each team builds their own |
| Bottleneck: data team is overwhelmed | Distributed: teams move independently |
| Consistent tooling | Standardized interfaces, varied implementation |
| Data warehouse is the product | "Data products" are the product |

**The 4 principles:**
1. **Domain ownership**: Trading team owns trade data, not the central data team
2. **Data as a product**: Treat datasets like API products (SLAs, docs, quality)
3. **Self-serve platform**: Central team provides tools, not pipelines
4. **Federated governance**: Standards set centrally, implementation decentralized

**Your answer:** "I haven't worked in a formal data mesh, but the principle maps to my experience. At Nomura, the trading desk owned their data definitions, and I built pipelines that consumed their data as a product. The key challenge is governance -- without central standards, you get inconsistent schemas and quality."

### ELT vs ETL

| | ETL (Extract-Transform-Load) | ELT (Extract-Load-Transform) |
|---|---|---|
| **Transform where?** | Before loading (Spark, Python) | After loading (in the warehouse) |
| **Tools** | Spark, custom scripts | dbt, Snowflake SQL |
| **Best when** | Complex transforms, ML features | SQL-heavy transforms, warehouse is powerful |
| **Your experience** | Nomura (Spark transforms before loading) | Nissan (load to Snowflake, transform with SQL) |

---

## PART 17: DISTRIBUTED SYSTEMS CONCEPTS

### CAP Theorem (Know This for System Design)

**You can only have 2 of 3:**

| Property | Meaning |
|---|---|
| **Consistency** | Every read gets the most recent write |
| **Availability** | Every request gets a response (even if stale) |
| **Partition Tolerance** | System works even if network splits nodes |

**In practice:** Network partitions WILL happen, so you choose between CP or AP:
- **CP (Consistency + Partition Tolerance)**: HBase, ZooKeeper -- always correct, might reject requests
- **AP (Availability + Partition Tolerance)**: Cassandra, DynamoDB -- always responds, might be stale

**DE context:** "Kafka is AP -- it prioritizes availability. Delta Lake adds consistency on top of S3 (which is eventually consistent). Snowflake is CP for queries but AP for writes (eventual consistency between warehouses)."

### Eventual Consistency vs Strong Consistency

**Analogy:** You post on Instagram. Your friend in another country sees it 2 seconds later. That's eventual consistency -- the data propagates, just not instantly.

| | Strong | Eventual |
|---|---|---|
| **Guarantee** | Reads always see latest write | Reads might see stale data temporarily |
| **Latency** | Higher (must confirm all replicas) | Lower (write to one, propagate later) |
| **Examples** | PostgreSQL, Snowflake queries | S3, DynamoDB, Cassandra |

---

## PART 18: LINUX & GIT COMMANDS (Quick-Fire Round)

### Linux Commands DEs Use Daily

```bash
# File operations
ls -la           # List files with details
head -n 20 file  # First 20 lines
tail -f log.txt  # Watch a log file in real-time (follow mode)
wc -l file.csv   # Count lines in a file
du -sh folder/   # Folder size (human readable)

# Text processing
grep "ERROR" log.txt          # Find lines containing "ERROR"
grep -c "ERROR" log.txt       # COUNT lines with "ERROR"
awk -F',' '{print $1,$3}' f   # Print columns 1 and 3 from CSV
sort file.txt | uniq -c       # Count unique values
cut -d',' -f1,3 data.csv      # Extract columns 1 and 3

# Process management
ps aux | grep spark            # Find Spark processes
kill -9 <PID>                  # Force kill a process
nohup python job.py &          # Run in background, survive logout
top                            # Monitor CPU/memory usage

# Networking
curl -X GET http://api/health  # Test an API endpoint
netstat -tlnp                  # Show listening ports
```

### Git Commands for DE

```bash
git log --oneline -10          # Last 10 commits (compact)
git diff HEAD~1                # Changes since last commit
git stash / git stash pop      # Temporarily save/restore changes
git blame file.py              # Who changed each line and when
git bisect start               # Binary search for which commit broke something
git rebase -i HEAD~3           # Clean up last 3 commits before push
```

---

## PART 19: COST OPTIMIZATION (Senior-Level Topic)

> Senior DEs are expected to think about cost, not just functionality.

### Where Data Pipelines Waste Money

| Waste | Fix | Savings |
|---|---|---|
| Spark cluster running 24/7 | Auto-scaling, shut down when idle | 40-60% |
| Processing all data daily | Incremental / CDC processing | 70-90% |
| Storing hot data forever | S3 lifecycle policies (Standard -> IA -> Glacier) | 30-50% |
| Over-provisioned Snowflake warehouse | Right-size, auto-suspend after 5 min | 50% |
| Reading all columns from Parquet | Column pruning (SELECT only what you need) | 30-40% |
| Full table scans | Partitioning + predicate pushdown | 80-90% |
| Redundant data copies | Delta Lake sharing / Snowflake data sharing | 30% |

**Your Nissan answer:**
> "At Nissan, I reduced pipeline costs by: (1) Using Lambda (pay-per-invocation) instead of an always-on server, (2) Snowflake warehouse auto-suspend after 5 minutes of inactivity, (3) S3 lifecycle policies moving old partitions to Infrequent Access after 90 days. This reduced our monthly data platform cost by approximately 40%."

### The Cost Optimization Interview Question

**Q: "Your Spark pipeline costs $50K/month. How do you reduce it?"**

> 1. **Profile first**: Where is money spent? Compute? Storage? Data transfer?
> 2. **Right-size executors**: Are we using 4XL instances but only using 30% CPU? Downsize.
> 3. **Spot/preemptible instances**: Use for non-critical batch jobs (60-80% cheaper)
> 4. **Incremental processing**: Don't reprocess 30 days of data when only today changed
> 5. **Caching intermediate results**: Cache frequently-recomputed DataFrames
> 6. **Optimize file formats**: Ensure Parquet with Snappy compression (not CSV/JSON)
> 7. **Partition pruning**: Make sure queries are leveraging partition filters
> 8. **Schedule off-peak**: Run big jobs during off-peak hours (cheaper spot prices)

---

## PART 20: SQL DEEP CONCEPTS (Frequently Asked, Often Missed)

### Indexing (Clustered vs Non-Clustered)

**What is an index?** A data structure that speeds up lookups, like a book's index. Without it, the database scans every row (full table scan).

| Type | What it does | Analogy | When to use |
|---|---|---|---|
| **Clustered** | Physically reorders table rows by the index column | A phone book (sorted by last name) | Primary key, columns used in range queries (date ranges) |
| **Non-clustered** | Creates a separate lookup table pointing to rows | A book's back-of-book index | Columns used in WHERE/JOIN but not the primary sort |
| **Composite** | Index on multiple columns | Phone book sorted by (last name, first name) | Multi-column WHERE clauses |
| **Covering** | Index includes all columns needed by the query | Index has the answer, no need to read the table | Frequently-run queries with few columns |

```sql
-- Create an index on trade_date for fast date range queries
CREATE INDEX idx_trades_date ON trades (trade_date);

-- Composite index for queries that filter by BOTH columns
CREATE INDEX idx_trades_date_inst ON trades (trade_date, instrument_id);

-- Check if your query uses the index
EXPLAIN SELECT * FROM trades WHERE trade_date = '2024-01-01';
-- Look for "Index Scan" (good) vs "Seq Scan" (bad - full table scan)
```

**Counter-questions:**

**"When should you NOT add an index?"**
> "Indexes slow down writes (INSERT/UPDATE/DELETE must update the index too). Don't index: columns rarely queried, low-cardinality columns (boolean has only 2 values), or tables that are write-heavy with rare reads."

**"What's the difference between clustered and non-clustered?"**
> "A table can have only ONE clustered index (because data can only be physically sorted one way). It can have MANY non-clustered indexes. Clustered is faster for range queries (sequential disk reads). Non-clustered is faster for point lookups."

**Analogy:** Clustered = a dictionary (words sorted A-Z, the data IS the index). Non-clustered = a book index at the back (separate from the content, points to page numbers).

**Memory trick:** **C**lustered = **C**ontent sorted. **N**on-clustered = **N**ote pointing to content.

### WHERE vs HAVING (Asked in Every SQL Screen)

```sql
-- WHERE filters BEFORE grouping (filters individual rows)
SELECT department, AVG(salary)
FROM employees
WHERE hire_date > '2020-01-01'    -- Filter rows BEFORE aggregation
GROUP BY department;

-- HAVING filters AFTER grouping (filters aggregated results)
SELECT department, AVG(salary) AS avg_sal
FROM employees
GROUP BY department
HAVING AVG(salary) > 80000;       -- Filter groups AFTER aggregation
```

**Rule:** Use WHERE for columns. Use HAVING for aggregates (SUM, AVG, COUNT).

**Counter-question:** "Can you use WHERE instead of HAVING?"
> "No. WHERE runs before GROUP BY, so it can't reference aggregated values. HAVING runs after GROUP BY, so it CAN filter on aggregates. Common mistake: `WHERE COUNT(*) > 5` -- this errors. Must be `HAVING COUNT(*) > 5`."

**Memory trick:** **W**HERE = **W**hich rows to include. **H**AVING = **H**ow many/much after grouping.

### NULL Handling (Causes More Bugs Than Anything)

```sql
-- NULL is NOT equal to anything, not even NULL
SELECT * FROM orders WHERE status = NULL;       -- WRONG: returns 0 rows
SELECT * FROM orders WHERE status IS NULL;      -- CORRECT

-- NULL in aggregations: ignored by SUM, COUNT(col), AVG
SELECT AVG(salary) FROM employees;              -- Ignores NULLs
SELECT COUNT(salary) FROM employees;            -- Counts non-NULL only
SELECT COUNT(*) FROM employees;                 -- Counts ALL rows including NULL

-- COALESCE: replace NULL with a default value
SELECT COALESCE(phone, email, 'no contact') AS contact FROM customers;
-- Returns phone if not NULL, else email, else 'no contact'

-- NVL (Oracle) / IFNULL (MySQL) / ISNULL (SQL Server):
SELECT ISNULL(salary, 0) FROM employees;        -- Replace NULL salary with 0
```

**Counter-question:** "What happens when you JOIN on a NULL key?"
> "NULL = NULL evaluates to UNKNOWN (not TRUE). So rows with NULL keys NEVER match in a JOIN. All NULLs go to the same partition in Spark, causing massive data skew. Fix: filter out NULLs before joining, or use COALESCE to replace NULLs with a default value."

**Memory trick:** NULL = **N**ot **U**sual **L**ogic **L**ength -- nothing equals NULL, not even NULL.

### Normalization (1NF through BCNF)

| Form | Rule | Example violation | Fix |
|---|---|---|---|
| **1NF** | Every cell has a single value (no arrays) | tags = "python, spark, sql" | Split into a separate tags table |
| **2NF** | 1NF + no partial dependencies (non-key depends on FULL primary key) | In (order_id, product_id) -> customer_name depends only on order_id | Move customer_name to orders table |
| **3NF** | 2NF + no transitive dependencies (non-key depends on another non-key) | zip_code -> city (city depends on zip, not on PK) | Move city to a zip_codes table |
| **BCNF** | 3NF + every determinant is a candidate key | Rare edge case | Usually 3NF is sufficient |

**When to normalize (OLTP):** Transaction systems (e-commerce orders, user accounts). Reduces data redundancy, ensures consistency.

**When to denormalize (OLAP):** Analytics systems (dashboards, reports). Fewer joins = faster queries. Trade storage for speed.

**Counter-question:** "Why do we denormalize for analytics?"
> "A normalized database with 10 tables requires 10 JOINs for one dashboard query. That's slow. A denormalized star schema puts everything in 2-3 tables with 1-2 JOINs. We sacrifice storage (repeating 'customer_name' in every row) for query speed. Storage is cheap; analyst time is expensive."

**Analogy:** Normalization = organizing your closet by category (shirts here, pants there, socks in a drawer). Efficient storage, slower to get dressed. Denormalization = laying out tomorrow's outfit on a chair. Redundant, but fast in the morning.

**Memory trick:** 1NF = **1** value per cell. 2NF = **2**nd: no **p**artial deps. 3NF = **3**rd: no **t**ransitive deps.

---

## PART 21: SPARK CONCEPTS OFTEN MISSED

### Narrow vs Wide Transformations

| | Narrow | Wide |
|---|---|---|
| **Data movement** | Within same partition | Across partitions (SHUFFLE) |
| **Examples** | map, filter, select, withColumn | groupBy, join, repartition, orderBy |
| **Cost** | Cheap (no network) | Expensive (network + disk I/O) |
| **Stage boundary?** | No | Yes (creates new stage) |

```python
# Narrow: each partition processes independently, no data moves
df.filter(col("amount") > 0)      # Narrow -- stays in same partition
df.select("id", "amount")          # Narrow
df.withColumn("tax", col("amount") * 0.1)  # Narrow

# Wide: data must move between partitions
df.groupBy("category").sum()       # Wide -- all same-category rows must co-locate
df.join(other_df, "key")           # Wide -- matching keys must co-locate
df.orderBy("amount")               # Wide -- global sort requires all data to move
```

**Counter-question:** "Why does this matter?"
> "Narrow transformations can be pipelined (chained without writing to disk). Wide transformations force a shuffle -- disk write, network transfer, disk read. A pipeline with 5 narrows and 1 wide has 2 stages. A pipeline with 5 wides has 6 stages and 5 shuffles. Minimizing wide transformations = faster jobs."

**Analogy:** Narrow = each worker does their own task at their own desk. Wide = everyone has to get up, walk to a different room, and reorganize.

### repartition() vs coalesce()

| | repartition() | coalesce() |
|---|---|---|
| **Can increase partitions?** | Yes | No (only decrease) |
| **Full shuffle?** | Yes (expensive) | No (merges adjacent partitions) |
| **Use when** | Need specific partition count or partition by column | Reducing partitions before write |

```python
# BAD: Full shuffle just to reduce partitions
df.repartition(10).write.parquet("output/")       # Shuffles ALL data

# GOOD: Merge adjacent partitions, no shuffle
df.coalesce(10).write.parquet("output/")           # Just merges, no shuffle

# WHEN to use repartition:
df.repartition("customer_id")                      # Partition BY a column for co-located joins
df.repartition(200)                                # When you need MORE partitions (can't coalesce UP)
```

**Counter-question:** "When would coalesce cause problems?"
> "If you coalesce from 1000 partitions to 10, each output partition holds 100x more data. This might cause OOM if partitions become too large. Also, coalesce creates uneven partitions (it merges existing ones, not rebalances). If evenness matters, use repartition."

**Memory trick:** **C**oalesce = **C**heap (no shuffle). **R**epartition = **R**edistribute (full shuffle).

### Spark SQL Query Optimization

**Q: "Your Spark SQL query is slow. How do you debug it?"**

> Step-by-step:
> 1. **Check the query plan**: `df.explain(True)` -- look for BroadcastHashJoin (good) vs SortMergeJoin (potentially slow)
> 2. **Check the Spark UI**: Stages tab -- which stage takes longest? Is it a shuffle?
> 3. **Check partition sizes**: `df.rdd.getNumPartitions()` -- too few partitions = too much data per task. Too many = overhead.
> 4. **Check for data skew**: In Spark UI, look at task durations. If one task takes 10x longer, you have skew.
> 5. **Check for full table scans**: Is predicate pushdown working? Are filters pushed to the Parquet/Delta level?

```python
# See the full query plan
df.explain("formatted")

# Good plan:
# +- BroadcastHashJoin [id], [id]    <-- Small table broadcast, no shuffle
#    +- FileScan parquet [trade_date = 2024-01-01]  <-- Predicate pushdown

# Bad plan:
# +- SortMergeJoin [id], [id]        <-- Full shuffle on both sides
#    +- FileScan parquet [no pushdown filters]  <-- Reading everything
```

---

## PART 22: BACK-OF-ENVELOPE ESTIMATION (System Design Must-Know)

> In system design rounds, they expect you to do quick math to justify your architecture choices.

### Numbers Every DE Should Know

| Metric | Value | Use for |
|---|---|---|
| 1 KB | ~1 short text record | Estimating message sizes |
| 1 MB | ~1000 records | Small file size |
| 1 GB | ~1M records (1KB each) | Medium dataset |
| 1 TB | ~1B records | Large dataset |
| 1 Parquet row (avg) | ~100-500 bytes | Estimating storage |
| S3 read latency | ~10-50ms per file | Why too many small files is bad |
| Kafka throughput | ~1M messages/sec per broker | Sizing Kafka clusters |
| Spark task | processes ~128MB per task | Sizing partition count |
| Network throughput | ~1 Gbps (125 MB/s) per node | Shuffle estimation |

### Example Estimation: "How much storage for 1 year of clickstream data?"

```
Given: 10K events/second peak, 100 bytes per event average

Daily volume: 10,000 events/sec x 86,400 sec/day = 864M events/day
Daily storage (raw): 864M x 100 bytes = 86.4 GB/day
Daily storage (Parquet compressed ~5x): 86.4 / 5 = ~17 GB/day
Yearly storage: 17 GB x 365 = ~6.2 TB/year

With 3 copies (Bronze + Silver + Gold): ~18 TB/year
With S3 Standard pricing ($0.023/GB): ~$400/month

"So we need about 18TB/year, costing roughly $400/month in S3. This is manageable -- no need for special cost optimization at this scale."
```

### Example Estimation: "How many Spark executors for a 1TB join?"

```
Data: 1TB
Target partition size: 200MB
Partitions needed: 1TB / 200MB = 5,000 partitions

Executor config: 4 cores each
Tasks per executor: 4 (one per core)
Executors needed: 5,000 / 4 = 1,250 (but tasks run in waves)

With 50 executors: 5,000 / (50 x 4) = 25 waves
Time per wave: ~30 seconds (read + transform)
Total: 25 x 30s = ~12.5 minutes

"A 1TB join with 50 executors takes roughly 12 minutes. If SLA is 30 minutes, 50 executors is sufficient."
```

---

## PART 23: PATTERNS OFTEN MISSED

### Write-Audit-Publish (WAP) Pattern

**What it is:** Don't write data directly to production tables. Write to staging, audit quality, THEN publish to production.

```
Pipeline Output
    |
[WRITE to staging table]    -- Isolated, not visible to users
    |
[AUDIT quality checks]     -- Row count, nulls, distributions, freshness
    |
    +--- PASS --> [PUBLISH to production]  (atomic swap or MERGE)
    |
    +--- FAIL --> [ALERT + QUARANTINE]     (production unchanged)
```

**Why it matters:** Without WAP, bad data goes directly to production dashboards. With WAP, production is NEVER corrupted -- the bad data stays in staging.

**Your answer:** "In my Healthcare project, the prediction pipeline validates inputs before serving results. This is the same principle as WAP -- never expose unvalidated data to users."

### Horizontal vs Vertical Scaling

| | Vertical (Scale UP) | Horizontal (Scale OUT) |
|---|---|---|
| **How** | Bigger machine (more CPU/RAM) | More machines |
| **Cost** | Gets expensive fast (16GB->128GB = 8x cost) | Linear (add more $200 nodes) |
| **Limit** | Physical hardware limit | Theoretically unlimited |
| **Complexity** | Simple (same code) | Complex (distributed systems) |
| **Examples** | Bigger Snowflake warehouse | More Spark executors |
| **Your experience** | "First attempt: bigger instance" | "Production: Spark cluster scales out" |

**Counter-question:** "Which do you try first?"
> "Vertical first. It's the cheapest and fastest fix. If a Spark job is slow, try doubling executor memory before adding more executors. If you're already at the maximum instance size or need fault tolerance, scale horizontally."

**Analogy:** Vertical = getting a bigger truck. Horizontal = getting more trucks. At some point, you can't build a bigger truck.

### OLTP vs OLAP (The Most Basic Question They'll Ask)

| | OLTP | OLAP |
|---|---|---|
| **Purpose** | Run the business (transactions) | Analyze the business (reporting) |
| **Operations** | Many small reads/writes | Few large reads |
| **Schema** | Normalized (3NF) | Denormalized (Star schema) |
| **Storage** | Row-oriented (PostgreSQL, MySQL) | Column-oriented (Snowflake, Parquet) |
| **Latency** | Milliseconds | Seconds to minutes |
| **Users** | Application users | Analysts, data scientists |
| **Your experience** | Healthcare: SQLite stores user data | Nissan: Snowflake for reporting |

**Counter-question:** "Can you use one system for both?"
> "Not well. OLTP is optimized for writes (row storage, indexes on primary key). OLAP is optimized for reads (columnar storage, no write optimization). Trying to run analytics on an OLTP database kills performance for both workloads. That's why we extract data from OLTP systems and load it into OLAP systems."

**Memory trick:** OL**T**P = **T**ransactions (write-heavy). OL**A**P = **A**nalytics (read-heavy).

### SQL Execution Order (Why Your Query Doesn't Work)

```sql
-- You WRITE it in this order:
SELECT department, COUNT(*) AS cnt    -- 5. Select
FROM employees                         -- 1. From (which table?)
WHERE salary > 50000                   -- 2. Where (filter rows)
GROUP BY department                    -- 3. Group By (aggregate)
HAVING COUNT(*) > 5                    -- 4. Having (filter groups)
ORDER BY cnt DESC                      -- 6. Order By (sort)
LIMIT 10;                              -- 7. Limit (top N)
```

**Execution order: FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT**

**Why this matters:** You can't use a column alias in WHERE (it doesn't exist yet). You CAN use it in ORDER BY (SELECT runs before ORDER BY).

```sql
-- WRONG: alias not available in WHERE
SELECT salary * 12 AS annual FROM employees WHERE annual > 100000;

-- CORRECT: use the expression
SELECT salary * 12 AS annual FROM employees WHERE salary * 12 > 100000;

-- CORRECT: use alias in ORDER BY (SELECT runs before ORDER BY)
SELECT salary * 12 AS annual FROM employees ORDER BY annual DESC;
```

**Memory trick:** "**F**red **W**ants **G**ood **H**ot **S**oup **O**rdered **L**ast" = FROM WHERE GROUP HAVING SELECT ORDER LIMIT

---

## PART 24: AZURE DATA ENGINEERING

> Many companies use Azure instead of AWS. Know the service mappings.

### Azure Services Mapped to AWS (What You Already Know)

| AWS Service | Azure Equivalent | What it does | Your bridge |
|---|---|---|---|
| **S3** | **Azure Blob / ADLS Gen2** | Object/file storage | "Same as S3 but with hierarchical namespace" |
| **Lambda** | **Azure Functions** | Serverless compute | "Same event-driven model as Lambda" |
| **Step Functions** | **Azure Data Factory (ADF)** | Workflow orchestration | "ADF is like Step Functions + Glue combined" |
| **EMR** | **Azure HDInsight / Synapse Spark** | Managed Spark | "Same Spark engine, different management UI" |
| **Glue** | **Azure Data Factory** | Serverless ETL | "ADF handles both orchestration and ETL" |
| **Redshift** | **Azure Synapse Analytics** | Data warehouse | "Synapse = Redshift equivalent with Spark built in" |
| **Kinesis** | **Azure Event Hubs** | Real-time streaming | "Same as Kinesis, Kafka-compatible API" |
| **Athena** | **Azure Synapse Serverless SQL** | Serverless SQL on files | "Query Parquet files without a cluster" |
| **CloudWatch** | **Azure Monitor** | Monitoring/logging | "Same observability model" |
| **IAM** | **Azure Active Directory (AAD)** | Identity management | "RBAC + service principals" |

### Azure-Specific Interview Questions

**Q: "What is ADLS Gen2?"**
> "Azure Data Lake Storage Gen2. It's Blob Storage with a hierarchical namespace (real directories, not just prefixes like S3). This enables atomic directory operations, better Spark performance (file listing is faster), and fine-grained POSIX-style ACLs. It's the standard storage for Azure data lakes."

**Q: "What is Azure Data Factory?"**
> "ADF is Azure's orchestration AND ETL tool. It combines what AWS does with Step Functions (orchestration) and Glue (data movement). It has visual pipeline designer, 90+ built-in connectors (Salesforce, SAP, SQL Server), and native integration with Synapse and Databricks."

**Q: "Synapse vs Databricks on Azure?"**

| | Azure Synapse | Databricks on Azure |
|---|---|---|
| **Best for** | SQL-heavy analytics, BI | Spark-heavy processing, ML |
| **SQL engine** | Dedicated SQL pools (MPP) | Spark SQL |
| **Integration** | Tight with Power BI, ADF | Better notebook experience |
| **Cost model** | DWU-based (can be expensive) | DBU-based (pay per compute) |
| **Your bridge** | "Like Snowflake + Spark in one" | "Managed Spark + Delta Lake" |

**Your bridge answer:**
> "I haven't used Azure directly, but every Azure service maps 1:1 to an AWS service I've used. ADLS Gen2 = S3 with hierarchical namespace. ADF = Step Functions + Glue. Synapse = Redshift with Spark. The data engineering principles -- partitioning, Delta Lake, Airflow orchestration, idempotent pipelines -- are identical across clouds. I'd be productive on Azure within a week."

---

## PART 25: DATABRICKS DATA ENGINEERING

> Databricks is the #1 platform companies hire DEs for. Know it cold.

### What is Databricks?

**In one sentence:** Databricks is a managed platform that wraps Apache Spark + Delta Lake + MLflow with a notebook UI, auto-scaling clusters, and Unity Catalog for governance.

**Analogy:** If Spark is a car engine, Databricks is the entire car -- engine (Spark) + dashboard (notebooks) + GPS (Unity Catalog) + mechanic (managed clusters).

### Databricks Concepts Every DE Must Know

| Concept | What it is | Your bridge |
|---|---|---|
| **Workspace** | Shared environment with notebooks, repos, jobs | "Like Jupyter Hub but for teams" |
| **Cluster** | Managed Spark cluster (auto-terminates, auto-scales) | "Like EMR but zero-config" |
| **Notebook** | Interactive code editor (Python, SQL, Scala, R) | "Like Jupyter notebooks" |
| **Job** | Scheduled notebook/pipeline execution | "Like an Airflow DAG" |
| **Delta Live Tables (DLT)** | Declarative ETL framework | "You define WHAT, Databricks handles HOW" |
| **Unity Catalog** | Centralized governance (access control, lineage) | "Like AWS Lake Formation" |
| **Medallion Architecture** | Bronze -> Silver -> Gold pattern | "ALREADY USE THIS in Nova" |
| **Photon** | C++ execution engine (faster than JVM Spark) | "2-8x faster, zero code changes" |
| **DBFS** | Databricks File System (abstraction over cloud storage) | "Mount point for S3/ADLS/GCS" |
| **Repos** | Git integration in Databricks | "Version control for notebooks" |

### Databricks Interview Questions

**Q: "What are Delta Live Tables (DLT)?"**
> "DLT is a declarative ETL framework. Instead of writing imperative Spark code ('read this, transform that, write here'), you declare the table definition and quality expectations. Databricks handles the orchestration, incremental processing, and error handling automatically."

```python
# Traditional Spark ETL (imperative):
df = spark.read.parquet("raw/events/")
df_clean = df.filter(col("event_id").isNotNull()).dropDuplicates(["event_id"])
df_clean.write.format("delta").mode("overwrite").save("silver/events/")

# Delta Live Tables (declarative):
@dlt.table
@dlt.expect_or_drop("valid_event_id", "event_id IS NOT NULL")
def silver_events():
    return dlt.read("bronze_events").dropDuplicates(["event_id"])
# Databricks handles: scheduling, incremental, retries, lineage
```

**Q: "What is Unity Catalog?"**
> "Centralized governance for all data assets across workspaces. It provides: (1) fine-grained access control (column-level, row-level), (2) data lineage (which tables feed which), (3) data discovery (search for tables across the organization), (4) audit logging (who accessed what). It's Databricks' answer to 'who owns this data and who can see it?'"

**Q: "What is Photon?"**
> "A C++ vectorized execution engine that replaces the JVM for Spark SQL. It's 2-8x faster for scan-heavy queries, with zero code changes. You just enable it on the cluster. It's especially fast for Delta Lake operations (MERGE, OPTIMIZE, Z-ORDER)."

**Your bridge answer:**
> "I already use the core technologies that Databricks wraps: PySpark, Delta Lake, and the Medallion architecture. My Nova project implements Bronze->Silver->Gold with Delta MERGE and OPTIMIZE -- these are the same primitives Databricks uses. The Databricks-specific additions (notebooks, DLT, Unity Catalog, Photon) are management layers on top of what I already know. I'd be productive in Databricks within days."

---

## PART 26: ON-PREMISES DATA ENGINEERING

> Some companies (finance, healthcare, government) run everything on-prem. This is your Nomura experience.

### On-Prem vs Cloud

| | On-Premises | Cloud |
|---|---|---|
| **Hardware** | You own and maintain servers | Cloud provider manages |
| **Scaling** | Buy more servers (weeks/months) | Spin up instances (minutes) |
| **Cost model** | CapEx (buy upfront) | OpEx (pay as you go) |
| **Control** | Full control over hardware and network | Limited to provider's offerings |
| **Security** | Data never leaves your building | Data in provider's data center |
| **Your experience** | Nomura: Hadoop/Spark on bare metal | Nissan: AWS Lambda + Snowflake |

### On-Prem Stack Mapping

| On-Prem Tool | Cloud Equivalent | Your experience |
|---|---|---|
| **HDFS** | S3 / ADLS Gen2 | Nomura: HDFS for trade data |
| **YARN** | K8s / EMR | Nomura: YARN resource management |
| **Hadoop MapReduce** | Spark on EMR/Databricks | Legacy, migrated to Spark |
| **Oozie** | Airflow / Step Functions | Legacy orchestration |
| **Hive** | Athena / Synapse Serverless | SQL on Hadoop |
| **HBase** | DynamoDB / Cosmos DB | NoSQL on Hadoop |
| **Kafka (on-prem)** | Confluent Cloud / MSK | Same Kafka, self-managed |
| **MinIO** | S3 | S3-compatible on-prem storage |

### On-Prem Interview Questions

**Q: "You migrated from on-prem to cloud. Walk me through it."**
> "At Nomura, I migrated Spark from YARN to Kubernetes:
> 1. **Storage migration**: HDFS -> MinIO (S3-compatible). Changed `hdfs://` paths to `s3a://` in Spark configs.
> 2. **Compute migration**: YARN -> K8s. Packaged Spark jobs as Docker images. Translated YARN memory configs to K8s resource requests/limits.
> 3. **Orchestration**: Kept Airflow (cloud-agnostic). Updated connection configs for new storage endpoints.
> 4. **Testing**: Ran parallel pipelines (YARN + K8s) for 2 weeks. Compared outputs. Validated within 0.01% tolerance.
> 5. **Cutover**: Decommissioned YARN cluster after 1 month of stable K8s operation."

**Q: "Why would a company stay on-prem?"**
> "Three reasons: (1) **Regulatory**: Healthcare (HIPAA) and finance (PCI-DSS, SOX) may require data to stay on-premise. (2) **Latency**: Trading systems need microsecond latency -- can't afford network hops to cloud. (3) **Cost at scale**: If you run 24/7 at massive scale, owning hardware can be cheaper than cloud. The trend is hybrid: sensitive data on-prem, analytics in cloud."

**Q: "What's the biggest challenge of on-prem?"**
> "Capacity planning. In cloud, you scale in minutes. On-prem, ordering and setting up new servers takes weeks. If you underestimate Black Friday traffic, you can't spin up 100 extra nodes. I mitigate this with: (1) auto-scaling within existing capacity, (2) 30% headroom in provisioning, (3) workload prioritization (kill non-critical jobs to free resources for critical ones)."

**Memory trick:** On-prem = **O**wn everything, **N**o elastic scaling, **P**hysical hardware, **R**egulatory compliance, **E**xpensive upfront, **M**ore control.

---

## PART 27: SNOWFLAKE DE (Deep Interview Coverage)

> You used Snowflake at Nissan. Here are the questions that go beyond basics.

### Advanced Snowflake Questions

**Q: "What are Snowflake Streams and Tasks?"**
> "Streams track changes (INSERT/UPDATE/DELETE) on a table -- like CDC. Tasks are scheduled SQL jobs. Together, they create an incremental pipeline without Airflow:
> 
> Stream watches `raw_trades` table -> detects new inserts -> Task runs every 15 minutes -> processes new rows -> writes to `clean_trades`.
> 
> This is Snowflake-native orchestration. For simple pipelines, it replaces Airflow entirely."

```sql
-- Create a stream to track changes on raw_trades
CREATE STREAM raw_trades_stream ON TABLE raw_trades;

-- Create a task that runs every 15 minutes
CREATE TASK process_trades
  WAREHOUSE = 'ETL_WH'
  SCHEDULE = '15 MINUTE'
WHEN SYSTEM$STREAM_HAS_DATA('raw_trades_stream')
AS
  INSERT INTO clean_trades
  SELECT trade_id, instrument_id, amount, trade_date
  FROM raw_trades_stream
  WHERE amount > 0 AND trade_id IS NOT NULL;

-- Start the task
ALTER TASK process_trades RESUME;
```

**Q: "What's the difference between transient and permanent tables?"**
> "Permanent tables have Fail-Safe (7 days of data protection after Time Travel expires). Transient tables skip Fail-Safe. Use transient for staging/temp tables -- saves storage cost. Permanent for production tables -- data protection."

**Q: "How do you load semi-structured data (JSON) into Snowflake?"**
```sql
-- Load raw JSON into a VARIANT column
CREATE TABLE raw_events (data VARIANT);

COPY INTO raw_events
FROM @my_s3_stage/events/
FILE_FORMAT = (TYPE = 'JSON');

-- Query nested JSON with dot notation
SELECT
    data:user_id::STRING AS user_id,
    data:event_type::STRING AS event_type,
    data:metadata.browser::STRING AS browser,
    data:timestamp::TIMESTAMP AS event_time
FROM raw_events;
```

**Q: "What's Snowflake's query result caching?"**
> "Snowflake caches query results for 24 hours. If you run the same query twice, the second execution returns instantly from cache (no warehouse compute needed). This means: (1) dashboards that refresh every hour don't re-query data, (2) you pay ZERO compute for repeated queries. Cache invalidates when underlying data changes."
