
# AI Healthcare System
### Disease Prediction & Medical Assistance Platform

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## Overview

This project provides a platform for preliminary medical insights. It uses **XGBoost** for disease prediction and **Gemini Pro (via RAG)** for interpreting health records.

The system uses **Retrieval Augmented Generation (RAG)** to ground responses in user data, reducing the likelihood of hallucination.

---

## 🏗️ Architecture

    Chat --> VectorDB
    Chat --> SQL
    Chat --> Gemini
    Vision --> Gemini
```

---

## Key Features

### Prediction Engine
- **Models**: XGBoost classifiers for Diabetes, Heart, and Liver disease.
- **Performance**: Optimized for low-latency inference.

### Assistant
- **RAG Architecture**: Uses vector storage to recall past interactions and reports.
- **Grounding**: Limits responses to available medical context.

### Lab Analysis
- **Vision**: Extracts data from PDF/Image lab reports using Gemini Vision.

### Security
- **Auth**: JWT-based session management.
- **Isolation**: Tenant-level data separation.

---

## Quick Start

### Option 1: Docker
Get the entire system (Frontend + Backend + MLflow) running in one command.

```bash
# 1. Clone & Setup
git clone <repository_url>
cd <repository_folder>
cp .env.example .env  # Add your GOOGLE_API_KEY in .env

# 2. Launch
docker-compose up --build
```
- **App**: [http://localhost:8501](http://localhost:8501)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MLflow**: [http://localhost:5000](http://localhost:5000)

### Option 2: Local Development
Run services individually for debugging.

1. **Backend**:
   ```bash
   pip install -r requirements.txt
   uvicorn backend.main:app --reload --port 8000
   ```
2. **Frontend**:
   ```bash
   streamlit run frontend/main.py
   ```

### Option 3: Quick Scripts (Windows)
Use the provided runner scripts for convenience:
- **Run Everything**: `.\scripts\runners\run_app.bat`
- **Run E2E Tests**: `.\scripts\runners\run_e2e_tests.ps1`


---

## Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | UI & Data Viz |
| **Backend** | FastAPI, Pydantic | API & Validation |
| **ML** | XGBoost, Scikit-Learn | Classification Models |
| **LLM** | Gemini Pro, LangChain | Orchestration & RAG |
| **Database** | SQLite, FAISS | Relational & Vector Storage |
| **Ops** | Docker, GitHub Actions | Containers & CI |

---

## Testing

To run the test suite:
```bash
pytest tests/ --cov=backend
```

---

## Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for style guides and setup instructions.

---

### License
MIT License. See [LICENSE](LICENSE) for details.
