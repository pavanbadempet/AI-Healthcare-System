<p align="center">
  <img src="frontend/static/logo.png" alt="AI Healthcare Logo" width="120"/>
</p>

<h1 align="center">AI Smart Patient Portal</h1>
<p align="center">
  <strong>Bridging Lab Results to Patient Understanding with AI</strong>
</p>

<p align="center">
  <a href="https://ai-healthcare-system.streamlit.app/">
    <img src="https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Live Demo"/>
  </a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?style=for-the-badge" alt="License"/>
</p>

---

## 🎯 Overview

A B2B2C healthcare platform that powers **Diagnostic Centers** to provide **Smart Patient Portals**. It combines detailed **Disease Screening** (Diabetes, Heart, etc.) with a **Personalized AI Companion** that explains lab reports to patients in plain English.

**🔗 Live Demo**: [ai-healthcare-system.streamlit.app](https://ai-healthcare-system.streamlit.app/)

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Streamlit Cloud)"]
        UI[Web Interface]
        Auth[Authentication]
        Views[Disease Prediction Views]
    end
    
    subgraph Backend["Backend API (Render)"]
        API[FastAPI Server]
        ML[ML Prediction Engine]
        RAG[RAG Pipeline]
        Vision[Vision Service]
    end
    
    subgraph AI["AI Services"]
        Gemini[Gemini Pro]
        FAISS[FAISS Vector Store]
    end
    
    subgraph Storage["Data Layer"]
        SQLite[(SQLite DB)]
        Models[(ML Models)]
    end
    
    UI --> API
    API --> ML --> Models
    API --> RAG --> FAISS
    RAG --> Gemini
    Vision --> Gemini
    API --> SQLite
```

---

## ✨ Key Features

### 🏥 For Diagnostic Centers (B2B)
- **White-label Patient Portal**: Offer a premium digital experience to your patients.
- **Automated Screening**: 5+ Disease Prediction Models (XGBoost/RandomForest).
- **Clinic Admin Console**: Manage patient records and system health.

### 👤 For Patients (Consumer)
- **AI Health Companion**: "Explain my lab report" chat interface.
- **My Health Passport**: Secure access to historical health data.
- **Virtual Consultations**: Book video calls with specialists.

### 🔬 Multi-Disease Screening
| Screening Screen | Model | Key Metrics |
|---------|-------|-------------|
| **Diabetes** | XGBoost | Glucose, BMI, Insulin, Age |
| **Heart Disease** | XGBoost | Cholesterol, BP, ECG Results |
| **Liver Disease** | XGBoost | Bilirubin, Albumin, Proteins |
| **Kidney Disease** | Random Forest | Creatinine, Hemoglobin, RBC |
| **Lung Cancer** | Gradient Boosting | Smoking, Chest Pain, Fatigue |

### 🤖 AI-Powered Medical Assistant
- **RAG Architecture**: Retrieval-Augmented Generation using FAISS vector storage
- **Context-Aware Responses**: Grounded in user health records and medical context
- **Conversation Memory**: Persists chat history for continuity

### 📄 Smart Lab Report Analyzer
- **Vision AI**: Extracts data from PDF/Image lab reports using Gemini Vision
- **Automated Insights**: Generates AI explanations for abnormal values

### 🔐 Security & Privacy
- **JWT Authentication**: Secure session management
- **Tenant Isolation**: User data fully separated
- **Rate Limiting**: API abuse prevention

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)
Spin up the entire stack with one command:

```bash
# Clone the repository
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Launch all services
docker-compose up --build
```

| Service | URL |
|---------|-----|
| **App (Frontend)** | http://localhost:8501 |
| **API Docs** | http://localhost:8000/docs |
| **MLflow UI** | http://localhost:5000 |

### Option 2: Local Development

**Prerequisites**: Python 3.10+, pip

```bash
# Install dependencies
pip install -r requirements.txt

# Start Backend (Terminal 1)
uvicorn backend.main:app --reload --port 8000

# Start Frontend (Terminal 2)
streamlit run frontend/main.py
```

### Option 3: Quick Scripts (Windows)
```powershell
# Run everything
.\scripts\runners\run_app.bat

# Run E2E tests
.\scripts\runners\run_e2e_tests.ps1
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Responsive UI & Data Visualization |
| **Backend** | FastAPI, Pydantic | REST API & Request Validation |
| **ML/AI** | XGBoost, Scikit-Learn | Disease Classification Models |
| **GenAI** | Gemini Pro, LangChain | Chat Assistant & RAG Pipeline |
| **Vector DB** | FAISS | Semantic Search & Memory |
| **Database** | SQLite | User Data & Chat History |
| **DevOps** | Docker, GitHub Actions | Containerization & CI/CD |
| **Hosting** | Streamlit Cloud, Render | Production Deployment |

---

## 🧪 Testing

```bash
# Run all tests with coverage
pytest tests/ --cov=backend --cov-report=term-missing

# Run specific test suites
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/e2e/            # End-to-end tests (requires running app)
```

### CI/CD Pipeline
GitHub Actions automatically runs on every push:
- ✅ Unit & Integration Tests
- ✅ Code Coverage Reporting
- ✅ Placeholder Model Generation for CI

---

## 📁 Project Structure

```
├── backend/                # FastAPI backend
│   ├── main.py             # API entrypoint
│   ├── prediction.py       # ML prediction logic
│   ├── agent.py            # AI chat agent
│   ├── rag.py              # RAG pipeline
│   ├── vision_service.py   # Lab report analyzer
│   └── *.pkl               # Trained ML models
├── frontend/               # Streamlit frontend
│   ├── main.py             # App entrypoint
│   ├── views/              # Page components
│   └── components/         # Reusable UI components
├── mlops/                  # MLOps pipeline
│   ├── data_ingestion.py   # Data loading
│   ├── data_processing.py  # Feature engineering
│   └── model_training.py   # Training scripts
├── tests/                  # Test suites
│   ├── unit/               # Unit tests
│   ├── integration/        # API integration tests
│   └── e2e/                # End-to-end tests
├── scripts/                # Utility scripts
├── docker-compose.yml      # Multi-container setup
└── render.yaml             # Render deployment config
```

---

## 🌐 Deployment

### Frontend (Streamlit Cloud)
1. Fork/Push to GitHub
2. Connect repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Set `BACKEND_URL` environment variable

### Backend (Render)
1. Connect repository to [Render](https://render.com)
2. Uses `render.yaml` for auto-configuration
3. Set required environment variables:
   - `GOOGLE_API_KEY` - Gemini API key
   - `SECRET_KEY` - JWT signing key

---

## 🤝 Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
