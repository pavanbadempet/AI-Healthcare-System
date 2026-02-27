# AGENTS.md - Frontend

> Scoped rules for `frontend/`. Read root `AGENTS.md` first.

## Stack

- **Streamlit** (Python) — not React/Vue/Angular.
- Views live in `frontend/views/` with the naming convention `{feature}_view.py`.
- Shared components live in `frontend/components/`.
- API client utilities live in `frontend/utils/`.
- Static assets (CSS, images) live in `frontend/static/`.
- Entry point is `frontend/main.py`.

## Rules

- **Session State**: Use `st.session_state` for cross-rerun persistence. Initialize defaults at the top of each view.
- **API Calls**: Always use the shared API client in `utils/`. Never call `requests.get/post` directly in view files.
- **Backend URL**: Read from `os.getenv("BACKEND_URL", "http://127.0.0.1:8000")`. Never hardcode.
- **Auth Token**: Store in `st.session_state["token"]` after login. Pass via `Authorization: Bearer` header.
- **Error Display**: Use `st.error()` for user-facing errors, `st.warning()` for non-critical. Never show raw tracebacks.
- **Layout**: Use `st.columns()` for side-by-side layouts. Use `st.expander()` for collapsible sections.
- **Medical Disclaimers**: Every prediction view must include a visible disclaimer that AI predictions are not medical advice.

## View Files

| View | Purpose |
| --- | --- |
| `dashboard_view.py` | Main dashboard after login |
| `chat_view.py` | AI medical chatbot |
| `diabetes_view.py` | Diabetes risk prediction |
| `heart_view.py` | Heart disease prediction |
| `liver_view.py` | Liver disease prediction |
| `kidney_view.py` | Kidney disease prediction |
| `lungs_view.py` | Lung disease prediction |
| `profile_view.py` | User profile management |
| `admin_view.py` | Admin panel |
| `telemedicine_view.py` | Doctor consultation booking |
| `pricing_view.py` | Subscription plans |
