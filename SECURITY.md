# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < main  | :x:                |

## Reporting a Vulnerability

We take security seriously in this healthcare AI system, especially given the sensitivity of medical data.

### How to Report

1. **DO NOT** open a public issue for security vulnerabilities.
2. Email **[pavanbadempet@gmail.com](mailto:pavanbadempet@gmail.com)** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Resolution Timeline**: Depends on severity
  - 🔴 Critical (data exposure, auth bypass): 24-48 hours
  - 🟠 High (privilege escalation): 1 week
  - 🟡 Medium (information leak): 2 weeks
  - 🟢 Low (best practice violation): Next release

### Security Measures in Place

- All AI inference routed through `backend/core_ai.py` — no direct provider API calls
- PII (patient names, DOBs, health data) never logged or exposed in error messages
- Medical disclaimers enforced on all AI-generated health advice
- SQL injection prevention via SQLAlchemy ORM
- JWT-based authentication with configurable expiry
- CORS and trusted host middleware
- Automated dependency scanning via Dependabot
- CodeQL static analysis on every push

### Scope

The following are **in scope**:
- Authentication and authorization bypass
- Patient data exposure or leakage
- AI model manipulation or prompt injection
- SQL injection or database access issues
- Cross-site scripting (XSS) in frontend
- Insecure API endpoints

The following are **out of scope**:
- Denial of service attacks on free-tier deployments
- Social engineering
- Issues in third-party dependencies (report upstream)

## Responsible Disclosure

We follow responsible disclosure practices. We will:
- Credit reporters (unless anonymity is requested)
- Not pursue legal action against good-faith reporters
- Work with you to understand and resolve the issue
