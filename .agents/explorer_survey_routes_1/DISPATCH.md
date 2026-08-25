## 2026-08-21T05:14:30Z

### Survey Task: FastAPI Routers, Endpoints & API Contract Mapping
**Working Directory**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_routes_1
**Original Request**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\ORIGINAL_REQUEST.md

**Objective**:
Map all API endpoints, routes, schemas, and contracts in the existing Python backend (`backend/main.py`, `backend/routes/`, `backend/schemas/`, etc.).

**Instructions**:
1. Read `ORIGINAL_REQUEST.md`.
2. Inspect `backend/main.py` and systematically enumerate all ~40 registered routers, their prefix paths, tags, dependencies (auth, db), and middleware.
3. For each router file in `backend/routes/` or related modules:
   - List every route (HTTP method, exact path including prefix).
   - Document request parameters (path, query, header, body schemas).
   - Document response status codes, response JSON models/shapes, error response formats.
   - Document WebSocket endpoints (paths, protocols, event formats for streaming chat and telemetry).
   - Document authentication & authorization mechanisms (JWT tokens, OAuth2 schemes, roles/permissions).
4. Check frontend usage (`frontend/src/` API calls / client hooks / services) to identify any frontend-critical endpoints, headers, or query parameters.
5. Write your comprehensive survey report to `c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_routes_1\routes_survey.md` and a self-contained summary in `handoff.md`.
