# AI Healthcare System

**AI-powered healthcare platform combining Machine Learning for multi-disease prediction (Diabetes, Heart, Liver, Kidney, Lungs) with Generative AI for intelligent medical assistance and lab report analysis.**

---

## 📑 Quick Navigation

| [📥 Download](#quick-start) | [✨ Features](#feature-highlights) | [🏗️ Architecture](#architecture) | [📚 Documentation](docs/) | [🐛 Issues](../../issues) | [💬 Discussions](../../discussions) |
|:---:|:---:|:---:|:---:|:---:|:---:|

### 📖 Detailed Docs
- **[Installation Guide](docs/INSTALLATION.md)** - Setup for development & production
- **[Usage Guide](docs/USAGE.md)** - API endpoints & features
- **[FAQ](docs/FAQ.md)** - Common questions & answers
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Debug common issues
- **[Contributing](docs/CONTRIBUTING.md)** - How to contribute
- **[Changelog](docs/CHANGELOG.md)** - Version history

---

<div align="center">

<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System" width="100%"/>

<br/>

<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI Tests" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=22c55e" alt="License" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square" alt="Stars" /></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js_15-000000?style=for-the-badge&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge&logo=chainlink" alt="LangGraph" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql" alt="PostgreSQL" />
</p>

</div>

---

## Feature Highlights

| 5 ML Diagnostic Models | 3-Tier AI Inference | RAG Medical Chat |
|---|---|---|
| Diabetes, Heart, Liver, Kidney, Lungs — trained on real clinical datasets with SHAP explainability | **Ollama > Gemini > Cloud** automatic fallback. Local inference for sensitive workflows | Gemini embeddings + vector store + LangGraph agent with patient history |

| Enterprise Security | 5 Deployment Options | 8 CI/CD Pipelines |
|---|---|---|
| JWT + bcrypt auth, RBAC (patient/doctor/admin), audit logging, rate limiting, PII redaction | Docker Compose, Enterprise Stack, Render, Kubernetes, Terraform AWS | Pytest + coverage, CodeQL, Docker builds, HuggingFace, Dependabot |

---

## 🚀 Quick Start

```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Backend
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend && npm install && npm run dev -- -p 3000
```

Visit: http://localhost:3000

**Full setup:** [Installation Guide](docs/INSTALLATION.md)

---

## 🏗️ Architecture

- **Frontend**: Next.js 15 with TypeScript & Tailwind CSS
- **Backend**: FastAPI with async/await, middleware stack
- **AI Engine**: 3-tier inference (Ollama → Gemini → OpenAI/Anthropic)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ML Models**: 5 scikit-learn/XGBoost classifiers with SHAP

[Full Architecture](https://github.com/pavanbadempet/AI-Healthcare-System#-architecture) | [API Reference](docs/USAGE.md#api-endpoints)

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [Installation](docs/INSTALLATION.md) | Local setup, Docker, production deployment |
| [Usage Guide](docs/USAGE.md) | API endpoints, dashboards, authentication |
| [FAQ](docs/FAQ.md) | Common questions & troubleshooting |
| [Contributing](docs/CONTRIBUTING.md) | Development setup, code style, testing |
| [Changelog](docs/CHANGELOG.md) | Version history & roadmap |

---

## ⚕️ Medical Disclaimer

⚠️ **This tool is for educational and screening purposes only.** It is NOT a medical diagnosis. Always consult qualified healthcare professionals. See [docs/FAQ.md](docs/FAQ.md) for details.

---

## 📊 Project Stats

- **5** ML diagnostic models
- **8** CI/CD pipelines
- **5** deployment options
- **7** middleware layers
- **95%+ test coverage**
- **HIPAA-friendly** design

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

**🌟 If this project helps you, please consider giving it a star!**

Made with ❤️ by [Pavan Badempet](https://github.com/pavanbadempet)