# 🎨 AI Healthcare System — React 19 Clinical Portal & Telemedicine UI

> A modern, high-performance, and responsive clinical portal and telemedicine web application built with **React 19**, **Vite 8**, and **Tailwind CSS v4**.

---

## 🚀 Overview

The frontend serves as the primary user interface for clinicians, administrators, and patients. It provides real-time dashboards, an interactive multi-agent scheduling chat, clinical decision support widgets, and electronic health record (EHR) interoperability views.

Built as a client-side Single Page Application (SPA), it communicates with the FastAPI backend using secure REST endpoints and WebSockets for real-time telemetry streaming.

---

## ⚡ Tech Stack

* **Core Framework**: React 19 (Client-side SPA)
* **Build Tooling**: Vite 8 & TypeScript 6
* **Styling**: Tailwind CSS v4 (Vanilla CSS variables integration)
* **Routing**: React Router DOM v7 (Lazy-loaded routes)
* **State Management**: Zustand (Lightweight, decoupled store pattern)
* **Data Fetching**: TanStack Query v5 (React Query)
* **Visualizations & Charts**: Recharts (High-contrast monochromatic styling)
* **Unit Testing**: Vitest (JSDOM environment with coverage)
* **E2E Testing**: Playwright (Headless Chromium browser testing)

---

## 📁 Source Directory Structure

```
frontend/
├── src/
│   ├── __tests__/             # Vitest Unit & Component Tests
│   ├── components/            # Reusable UI Components
│   │   ├── layout/            # Navigation, Sidebar, Top bar, Theme Toggle
│   │   ├── operations/        # Specialized clinical widgets (ECG, Vitals, SOAP)
│   │   └── ui/                # Base design system elements (Buttons, Dialogs)
│   ├── lib/                   # Core Client Libraries & Utilities
│   │   ├── api.ts             # API Client Gateway & endpoints
│   │   ├── apiCore.ts         # Base fetch clients with auth handling
│   │   └── store.ts           # Global Zustand store (User profile, active states)
│   ├── pages/                 # Lazy-loaded Page views
│   │   ├── Dashboard.tsx      # Main Clinician Operations hub
│   │   ├── Chat.tsx           # Multi-Agent RAG Assistant chat interface
│   │   ├── Telemedicine.tsx   # Telemedicine scheduling portal
│   │   └── Patients.tsx       # Patient roster registry
│   ├── App.tsx                # Routing definitions & global providers
│   ├── main.tsx               # Client entry mount point
│   └── index.css              # Tailwind CSS v4 design tokens configuration
├── tests/                     # Playwright E2E Browser Spec tests
│   ├── functional.spec.ts     # Core flows (Signup -> Dashboard -> Telemedicine)
│   └── visual.spec.ts         # Visual regression & high-contrast theme tests
├── playwright.config.ts       # Playwright E2E configuration
├── vitest.config.ts           # Vitest unit test configuration
└── package.json               # Package manifests & run scripts
```

---

## ⚙️ Configuration & Environment

The client automatically detects the API backend location. If deploying to custom endpoints, create a `.env` file inside the `frontend/` directory:

```env
# Target API base URL (Backend)
VITE_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## 🛠️ Local Development

Ensure you have **Node.js 20.x** or higher installed.

### 1. Install Dependencies
```bash
npm install
```

### 2. Run local development server
```bash
npm run dev
```
The application will serve locally at [http://127.0.0.1:3000](http://127.0.0.1:3000).

### 3. Compile Production Bundle
Builds the static assets with full TypeScript validation and optimization:
```bash
npm run build
```

---

## 🧪 Verification & Testing Suite

### 1. Run Unit & Component Tests
Executed via **Vitest** in a `jsdom` environment. Employs v8 coverage tools.
```bash
# Run tests once
npm run test

# Run tests in watch mode
npm run test:watch
```

### 2. Run End-to-End (E2E) Browser Tests
Playwright automates real browser sessions to verify user registration, login transitions, and interactive chat workflows.

Before running E2E tests, ensure the backend API server is running on port `8000`:
```bash
# Run headless browser tests
npm run test:e2e

# Run tests in UI mode (interactive)
npx playwright test --ui
```

### 3. Run Linter
Validates code styling rules:
```bash
npm run lint
```

---

## ⚕️ Regulatory & Medical Guidelines

In compliance with medical software standards:
1. **Medical Disclaimer**: Every user-facing view that generates machine learning predictions, AI diagnostic advice, or clinical narratives must display a prominent medical disclaimer. It must recommend consulting a qualified clinician for actual medical diagnosis, treatment, or emergencies.
2. **PII Isolation**: Never include real patient names, Dates of Birth (DOBs), or actual health records in unit tests, E2E fixtures, console logs, or mock states. All data must be synthetically generated.
