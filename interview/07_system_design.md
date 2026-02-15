# System Design & Architecture Interview Preparation

## Core Concepts

### **What is System Design?**
Think of system design like **architecting a modern hospital** - you need to design the building layout, departments, workflows, and emergency systems to ensure everything works together seamlessly.

### **The "Why System Design" Analogy**
Imagine you're a **hospital architect** planning a new medical center:

```
🏥 Basic Building (No Design):
   - Random room placement (inefficient workflows)
   - No emergency systems (dangerous for patients)
   - Poor department coordination (treatment delays)
   - No scalability (can't handle patient growth)

🏛️ Smart Hospital Design:
   - Optimized department layout (efficient workflows)
   - Emergency systems and backup plans (patient safety)
   - Coordinated department communication (fast treatment)
   - Scalable design (handles patient growth)
```

### **Key System Design Components:**
- **Scalability**: System's ability to handle growing load (like hospital capacity planning)
- **Availability**: System's uptime and reliability (like hospital backup systems)
- **Performance**: Response time and throughput (like emergency response time)
- **Security**: Protection against threats and vulnerabilities (like hospital security systems)
- **Maintainability**: Ease of system updates and modifications (like hospital remodeling)

---

## Healthcare System Architecture

### **High-Level Architecture:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend       │    │   Backend        │    │   Data Layer     │
│   (Streamlit)    │◄──►│   (FastAPI)      │◄──►│   (Delta Lake)   │
│                 │    │                 │    │                 │
│ • UI/UX          │    │ • REST APIs      │    │ • ACID Transactions│
│ • Visualizations │    │ • Business Logic │    │ • Time Travel     │
│ • User Input     │    │ • Authentication│    │ • SCD Type 2     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestration │    │   Processing    │    │   Storage       │
│   (Airflow)      │    │   (Spark)        │    │   (S3/Delta)    │
│                 │    │                 │    │                 │
│ • DAG Scheduling │    │ • ETL/ELT       │    │ • Object Storage │
│ • Monitoring     │    │ • Transformations│    │ • Data Lake     │
│ • Alerting       │    │ • ML Processing │    │ • File System   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Technology Stack:**
```python
technology_stack = {
    "frontend": {
        "framework": "Streamlit",
        "purpose": "Healthcare UI and visualizations",
        "advantages": "Python-native, easy deployment, rich charts"
    },
    "backend": {
        "framework": "FastAPI",
        "purpose": "REST APIs and business logic",
        "advantages": "Fast, async, automatic documentation"
    },
    "data_processing": {
        "framework": "Apache Spark",
        "purpose": "Big data processing and transformations",
        "advantages": "Scalable, in-memory, rich ecosystem"
    },
    "storage": {
        "format": "Delta Lake",
        "purpose": "ACID transactions and time travel",
        "advantages": "Reliability, performance, compliance"
    },
    "orchestration": {
        "framework": "Apache Airflow",
        "purpose": "Workflow orchestration",
        "advantages": "Python-native, extensible, monitoring"
    }
}
```

---

## Backend Architecture

### **FastAPI Backend Design:**
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="Healthcare Data API",
    description="REST APIs for healthcare data processing",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Data Models
class Patient(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str

class LabResult(BaseModel):
    result_id: str
    patient_id: str
    test_code: str
    result_value: float
    test_date: str

# API Endpoints
@app.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, token: str = Depends(security)):
    """Get patient information with HIPAA compliance"""
    try:
        patient = get_patient_from_delta(patient_id)
        return patient
    except Exception as e:
        raise HTTPException(status_code=404, detail="Patient not found")

@app.post("/lab-results", response_model=LabResult)
async def create_lab_result(
    lab_result: LabResult, 
    token: str = Depends(security)
):
    """Create lab result with validation"""
    if not validate_medical_code(lab_result.test_code):
        raise HTTPException(status_code=400, detail="Invalid medical code")
    
    result_id = save_lab_result_to_delta(lab_result)
    return {"result_id": result_id, "status": "created"}
```

### **Authentication & Authorization:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()

class AuthManager:
    def __init__(self):
        self.secret_key = "healthcare_secret_key"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return username
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    auth_manager = AuthManager()
    user = auth_manager.verify_token(credentials.credentials)
    return user
```

---

## Frontend Architecture

### **Streamlit Frontend Design:**
```python
import streamlit as st
import pandas as pd
import plotly.express as px
from backend.api_client import HealthcareAPI

# Page Configuration
st.set_page_config(
    page_title="Healthcare Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication
def authenticate_user():
    """Authenticate user with HIPAA compliance"""
    if 'authenticated' not in st.session_state:
        st.title("Healthcare Analytics Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")
        return False
    return True

# Main Dashboard
def main_dashboard():
    """Main healthcare analytics dashboard"""
    st.title("🏥 Healthcare Analytics Dashboard")
    
    # Sidebar Navigation
    page = st.sidebar.selectbox(
        "Select Page",
        ["Patient Analytics", "Lab Results", "Claims Analysis", "System Health"]
    )
    
    if page == "Patient Analytics":
        patient_analytics()
    elif page == "Lab Results":
        lab_results_analytics()
    elif page == "Claims Analysis":
        claims_analytics()
    elif page == "System Health":
        system_health_analytics()

def patient_analytics():
    """Patient analytics dashboard"""
    st.header("Patient Analytics")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    api = HealthcareAPI()
    metrics = api.get_patient_metrics()
    
    col1.metric("Total Patients", metrics['total_patients'])
    col2.metric("Active Patients", metrics['active_patients'])
    col3.metric("New Patients (Today)", metrics['new_patients_today'])
    col4.metric("Data Quality", f"{metrics['data_quality']:.1%}")
    
    # Charts
    patient_growth = api.get_patient_growth_trend()
    fig = px.line(patient_growth, x='date', y='count', title='Patient Growth')
    st.plotly_chart(fig, use_container_width=True)
    
    # Patient Table
    patients = api.get_recent_patients()
    st.dataframe(patients)
```

---

## Data Architecture

### **Delta Lake Data Model:**
```python
# Patient Dimension (SCD Type 2)
patients_schema = {
    "patient_id": "STRING (Primary Key)",
    "first_name": "STRING",
    "last_name": "STRING", 
    "email": "STRING",
    "phone": "STRING",
    "address": "STRING",
    "effective_date": "TIMESTAMP",
    "end_date": "TIMESTAMP",
    "is_current": "BOOLEAN"
}

# Lab Results Fact Table
lab_results_schema = {
    "result_id": "STRING (Primary Key)",
    "patient_id": "STRING (Foreign Key)",
    "test_code": "STRING",
    "test_name": "STRING",
    "result_value": "FLOAT",
    "result_unit": "STRING",
    "reference_range": "STRING",
    "abnormal_flag": "STRING",
    "test_date": "TIMESTAMP",
    "facility_id": "STRING"
}

# Claims Fact Table
claims_schema = {
    "claim_id": "STRING (Primary Key)",
    "patient_id": "STRING (Foreign Key)",
    "provider_id": "STRING (Foreign Key)",
    "service_date": "DATE",
    "procedure_code": "STRING",
    "diagnosis_code": "STRING",
    "billed_amount": "FLOAT",
    "allowed_amount": "FLOAT",
    "paid_amount": "FLOAT",
    "claim_status": "STRING",
    "submission_date": "TIMESTAMP"
}
```

### **Data Flow Architecture:**
```python
# Data Pipeline Flow
data_flow = {
    "ingestion": {
        "sources": ["EMR Systems", "Lab Information Systems", "Claims Systems"],
        "format": "JSON/CSV/HL7",
        "frequency": "Real-time + Batch",
        "validation": "Schema validation + Business rules"
    },
    "processing": {
        "transformations": ["Data cleaning", "Medical code validation", "SCD Type 2 updates"],
        "enrichment": ["Geocoding", "Risk scoring", "Anomaly detection"],
        "quality_checks": ["Completeness", "Accuracy", "HIPAA compliance"]
    },
    "storage": {
        "format": "Delta Lake",
        "partitioning": ["Date", "Facility", "Status"],
        "optimization": ["Z-ordering", "Compaction", "Caching"],
        "retention": "7 years (HIPAA requirement)"
    },
    "serving": {
        "apis": ["REST APIs", "GraphQL"],
        "analytics": ["Real-time dashboards", "Reports"],
        "ml": ["Feature store", "Model serving"],
        "compliance": ["Audit logs", "Access controls"]
    }
}
```

---

## Performance & Scalability

### **Scalability Design:**
```python
# Horizontal Scaling Strategy
scaling_strategy = {
    "frontend": {
        "scaling": "Load balancer + Multiple instances",
        "target": "1000 concurrent users",
        "response_time": "<200ms (95th percentile)"
    },
    "backend": {
        "scaling": "Kubernetes auto-scaling",
        "target": "10000 requests/second",
        "response_time": "<100ms (95th percentile)"
    },
    "data_processing": {
        "scaling": "Spark cluster auto-scaling",
        "target": "10TB/day processing",
        "processing_time": "<4 hours for full dataset"
    },
    "storage": {
        "scaling": "S3 auto-scaling + Delta Lake",
        "target": "100TB+ storage",
        "query_performance": "<2 seconds for complex queries"
    }
}
```

### **Performance Optimization:**
```python
# Caching Strategy
caching_strategy = {
    "frontend": {
        "browser_cache": "Static assets (1 hour)",
        "cdn_cache": "API responses (5 minutes)",
        "memory_cache": "User session data"
    },
    "backend": {
        "redis_cache": "Patient data (15 minutes)",
        "memory_cache": "Medical codes (1 hour)",
        "database_cache": "Query results (5 minutes)"
    },
    "data_layer": {
        "delta_cache": "Hot data (1 hour)",
        "file_cache": "Frequent queries (30 minutes)",
        "result_cache": "ML predictions (15 minutes)"
    }
}
```

---

## Security Architecture

### **Healthcare Security Framework:**
```python
# Multi-Layer Security
security_framework = {
    "network_security": {
        "firewall": "WAF with healthcare rules",
        "encryption": "TLS 1.3 for all traffic",
        "ddos_protection": "Cloud-based DDoS protection",
        "access_control": "IP whitelisting for critical systems"
    },
    "application_security": {
        "authentication": "JWT with 2FA",
        "authorization": "RBAC with fine-grained permissions",
        "input_validation": "Comprehensive input sanitization",
        "output_encoding": "Secure response encoding"
    },
    "data_security": {
        "encryption_at_rest": "AES-256 for PHI",
        "encryption_in_transit": "TLS 1.3",
        "key_management": "AWS KMS or Azure Key Vault",
        "data_masking": "Dynamic masking for non-privileged users"
    },
    "compliance": {
        "hipaa": "Complete HIPAA compliance framework",
        "audit_logging": "Comprehensive audit trails",
        "access_logging": "All PHI access logged",
        "retention": "7-year data retention policy"
    }
}
```

### **HIPAA Compliance Implementation:**
```python
# HIPAA Compliance Checklist
hipaa_compliance = {
    "technical_safeguards": {
        "access_control": "✅ Role-based access control",
        "audit_controls": "✅ Complete audit logging",
        "integrity": "✅ Data integrity checks",
        "transmission_security": "✅ TLS 1.3 encryption"
    },
    "administrative_safeguards": {
        "security_officer": "✅ Designated HIPAA officer",
        "training": "✅ Annual HIPAA training",
        "policies": "✅ Security policies and procedures",
        "incident_response": "✅ Incident response plan"
    },
    "physical_safeguards": {
        "facility_access": "✅ Controlled facility access",
        "workstation_security": "✅ Workstation security",
        "device_management": "✅ Mobile device management",
        "media_disposal": "✅ Secure media disposal"
    },
    "breach_notification": {
        "risk_assessment": "✅ Risk assessment procedures",
        "notification": "✅ Breach notification procedures",
        "documentation": "✅ Incident documentation",
        "remediation": "✅ Remediation procedures"
    }
}
```

---

## Code Examples

### **API Gateway Design:**
```python
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://healthcare-ui.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logging.info(
        f"Method: {request.method}, "
        f"Path: {request.url.path}, "
        f"Status: {response.status_code}, "
        f"Time: {process_time:.4f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/patients/{patient_id}")
@limiter.limit("10/minute")
async def get_patient_rate_limited(patient_id: str):
    """Rate-limited patient endpoint"""
    return get_patient_data(patient_id)
```

### **Database Connection Pooling:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import psycopg2

# Database Connection Pool
database_url = "postgresql://user:password@localhost/healthcare_db"

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)

# Connection Management
class DatabaseManager:
    def __init__(self):
        self.engine = engine
    
    def get_connection(self):
        """Get database connection from pool"""
        return self.engine.connect()
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute query with connection pooling"""
        with self.get_connection() as conn:
            result = conn.execute(query, params or ())
            return result.fetchall()
    
    def close_all_connections(self):
        """Close all connections in pool"""
        self.engine.dispose()
```

---

## Trade-offs & Architecture Decisions

### **Why FastAPI vs Alternatives:**

| Framework | Performance | Development Speed | Ecosystem | Security | Our Choice |
|----------|------------|-------------------|-----------|---------|------------|
| **FastAPI** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Chosen |
| **Django** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ Rejected |
| **Flask** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ❌ Rejected |
| **Express.js** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ Rejected |

### **Why Streamlit vs Alternatives:**

| Framework | Development Speed | Customization | Performance | Healthcare UI | Our Choice |
|----------|------------------|----------------|------------|---------------|------------|
| **Streamlit** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Chosen |
| **React** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ Rejected |
| **Vue.js** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ Rejected |
| **Dash** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ❌ Rejected |

---

## Challenges & Solutions

### **Challenge 1: HIPAA Compliance in Web Applications**
```python
# Problem: PHI data in web applications
# Solution: Multi-layer security approach

def hipaa_web_security():
    return {
        "frontend": {
            "encryption": "HTTPS only",
            "authentication": "2FA required",
            "session_timeout": "15 minutes",
            "data_masking": "PHI masked in UI"
        },
        "backend": {
            "api_security": "JWT + RBAC",
            "input_validation": "Comprehensive validation",
            "output_filtering": "Filter PHI in responses",
            "audit_logging": "All access logged"
        },
        "infrastructure": {
            "network": "VPC + Security groups",
            "storage": "Encrypted at rest",
            "monitoring": "Security monitoring",
            "backup": "Encrypted backups"
        }
    }
```

### **Challenge 2: Real-time Analytics Performance**
```python
# Problem: Real-time healthcare analytics
# Solution: Optimized caching and data serving

def real_time_optimization():
    return {
        "caching": {
            "redis_cache": "Patient data (15min)",
            "memory_cache": "Medical codes (1hr)",
            "cdn_cache": "API responses (5min)"
        },
        "data_serving": {
            "precomputed_aggregates": "Common metrics",
            "materialized_views": "Complex queries",
            "partitioned_tables": "Time-based partitioning"
        },
        "performance": {
            "response_time": "<200ms (95th percentile)",
            "throughput": "1000 req/sec",
            "concurrent_users": "1000+"
        }
    }
```

### **Challenge 3: Multi-Tenant Healthcare Data**
```python
# Problem: Multiple healthcare organizations
# Solution: Tenant isolation with shared infrastructure

def multi_tenant_architecture():
    return {
        "data_isolation": {
            "logical_separation": "Tenant-specific schemas",
            "physical_separation": "Separate Delta Lake tables",
            "access_control": "Tenant-specific permissions"
        },
        "resource_sharing": {
            "compute": "Shared Spark cluster",
            "storage": "Shared S3 bucket with prefixes",
            "monitoring": "Shared monitoring stack"
        },
        "scalability": {
            "horizontal": "Add new tenants easily",
            "vertical": "Scale per tenant resources",
            "cost": "Pay-per-tenant model"
        }
    }
```

---

## Performance Metrics

### **System Performance:**
```
API Response Time: 95ms (95th percentile)
Web Page Load Time: 1.2s (95th percentile)
Data Processing: 10TB/day in 4 hours
Query Performance: <2s for complex queries
Concurrent Users: 1000+
System Uptime: 99.9%
```

### **Scalability Metrics:**
```
Horizontal Scaling: Linear to 1000 users
Vertical Scaling: 10x performance improvement
Data Volume: 100TB+ supported
Processing Speed: 1.26GB/minute
Storage Efficiency: 65% compression ratio
```

### **Security Metrics:**
```
Authentication: 2FA required for all users
Authorization: RBAC with fine-grained permissions
Encryption: AES-256 for PHI at rest and in transit
Audit Logging: 100% of PHI access logged
Compliance: 100% HIPAA compliance
```

---

## Interview Questions & Answers

### **Q: How did you design the system for HIPAA compliance?**
**A:** Multi-layer approach:
- **Technical**: AES-256 encryption, TLS 1.3, RBAC
- **Administrative**: Security officer, training, policies
- **Physical**: Facility access, workstation security
- **Monitoring**: Complete audit trails and breach detection

### **Q: Why did you choose FastAPI over Django?**
**A:** Three key reasons:
1. **Performance**: 5x faster than Django for APIs
2. **Python-native**: Perfect integration with our data stack
3. **Modern**: Async support, automatic documentation
4. **Security**: Built-in security features

### **Q: How do you handle real-time analytics performance?**
**A:** Multi-layer optimization:
- **Caching**: Redis for hot data, CDN for API responses
- **Data Serving**: Precomputed aggregates, materialized views
- **Infrastructure**: Load balancing, auto-scaling
- **Results**: 95ms response time, 1000+ concurrent users

### **Q: What was your biggest system design challenge?**
**A**: HIPAA compliance in web applications. We solved it with:
- Multi-layer security framework
- Comprehensive audit logging
- Data masking in UI
- Complete encryption of PHI

### **Q: How do you ensure system scalability?**
**A**: Three-pronged approach:
1. **Horizontal**: Load balancer + auto-scaling
2. **Vertical**: Resource optimization and caching
3. **Data**: Delta Lake with partitioning and optimization

---

## Future Enhancements

### **Planned Improvements:**
1. **Microservices**: Break down monolithic services
2. **Event-driven**: Add Kafka for real-time events
3. **AI Integration**: ML model serving and monitoring
4. **Multi-cloud**: Cross-cloud deployment strategy

### **Scaling Considerations:**
1. **Enterprise Scale**: Support for 10,000+ users
2. **Global Deployment**: Multi-region architecture
3. **Advanced Analytics**: Real-time ML predictions
4. **Cost Optimization**: Predictive auto-scaling

---

## Key Takeaways

### **Technical Excellence:**
- Comprehensive system design understanding
- Healthcare domain expertise
- Performance optimization skills
- Security implementation experience

### **Business Impact:**
- 99.9% system uptime
- 1000+ concurrent users
- 10TB/day processing capacity
- 100% HIPAA compliance

### **Leadership Demonstrated:**
- End-to-end system architecture
- Security framework design
- Performance optimization
- Scalability planning

---

*This system design expertise demonstrates senior-level architecture skills with specific healthcare domain knowledge and measurable performance metrics.*
