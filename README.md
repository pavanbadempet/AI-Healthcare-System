
# 🏥 AIO Healthcare System
### *Intelligent Disease Prediction & AI-Powered Medical Assistance*

![CI Status](https://img.shields.io/github/actions/workflow/status/pavanbadempet/AIO-Healthcare-System/ci.yml?branch=main)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 📖 Overview

The **AIO Healthcare System** is a production-grade, microservices-ready platform designed to democratize access to preliminary medical insights. By combining **Gradient Boosting Machines (XGBoost)** for high-accuracy disease prediction with **Generative AI (Gemini Pro & RAG)** for personalized medical consultation, we bridge the gap between raw data and actionable health advice.

Unlike traditional health apps, this system implements **Retrieval Augmented Generation (RAG)** to "remember" user health records, ensuring that the AI chat assistant provides context-aware, verifiable answers—minimizing hallucinations and maximizing trust.

---

## 🏗️ Architecture

    Chat --> VectorDB
    Chat --> SQL
    Chat --> Gemini
    Vision --> Gemini
```

---

## ✨ Key Features

### 🩺 **Multi-Disease Prediction Engine**
- **Diabetes, Heart, & Liver Disease**: High-accuracy XGBoost classifiers trained on verified medical datasets.
- **Real-Time Inference**: Sub-millisecond prediction latency via optimized FastAPI endpoints.
- **Explainable AI (XAI)**: (Experimental) SHAP-based reasoning for *why* a prediction was made.

### 🤖 **Context-Aware AI Assistant**
- **RAG Architecture**: Creating a "memory" for the AI. It recalls your past checkups and lab reports during conversation.
- **Anti-Hallucination**: Strictly grounded in "Available Reports" and medical context.
- **Persistent History**: Chat sessions are saved and indexed for long-term health tracking.

### � **Automated Lab Analysis**
- **Vision API**: Upload detailed lab reports (PDF/Images). The system extracts values, flags anomalies, and adds them to your digital health profile.

### 🔐 **Enterprise-Grade Security**
- **JWT Authentication**: Stateless, secure session management.
- **Password Policies**: Enforced complexity (Regex validation).
- **Tenant Isolation**: User data is strictly siloed in both SQL and Vector Databases.

---

## ⚡ Quick Start

### Option 1: Docker (Recommended)
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

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Streamlit, Lottie | Rapid UI development, Interactive Data Viz |
| **Backend** | FastAPI, Pydantic | High-performance Async API, Validation |
| **ML Engine** | XGBoost, Scikit-Learn | State-of-the-art Tabular Classification |
| **GenAI** | Google Gemini Pro, LangChain | LLM Orchestration, RAG, Vision Analysis |
| **Database** | SQLAlchemy (SQLite), FAISS | Relational & Vector Data Persistence |
| **DevOps** | Docker, GitHub Actions | Containerization & CI/CD Pipelines |
| **MLOps** | MLflow | Experiment Tracking & Model Registry |

---

## 🧪 Engineering Standards

We adhere to strict engineering principles to ensure reliability.

- **100% Line Coverage**: All critical backend modules (`prediction`, `auth`, `vision`, `report`) are fully unit-tested.
- **Type Safety**: Strictly typed Python codebase using Pydantic V2 migration paths.
- **CI/CD**: Automated testing on every push via GitHub Actions.

To verify the system yourself:
```bash
# Run the full test suite
pytest tests/ --cov=backend
```

---

## 🤝 Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for style guides and setup instructions.

---

### License
MIT License. See [LICENSE](LICENSE) for details.
