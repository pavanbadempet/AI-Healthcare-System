# AGENTS.md - Tests

> Scoped rules for `tests/`. Read root `AGENTS.md` first.

## Stack

- Backend tests use **pytest** with `pytest-asyncio` for async tests.
- Config in `pytest.ini` at project root.
- Test database uses SQLite in-memory or temp file - never touch `healthcare.db`.
- Frontend Jest and Playwright tests are under `frontend/`; read `frontend/AGENTS.md` for those.

## Rules

- **Mock AI calls**: All tests must mock `core_ai.generate()`, `core_ai.chat()`, and embedding functions. Tests must never make real API calls.
- **Mock external services**: Mock Tavily, Razorpay, and any external HTTP calls.
- **Database isolation**: Use a fresh test database per test session. Use fixtures from `conftest.py`.
- **No hardcoded predictions**: Don't assert exact ML prediction values - models may be retrained. Assert structure and types instead.
- **Auth helpers**: Use the `test_client` and `auth_headers` fixtures for authenticated endpoint tests.
- **Naming**: Test files follow `test_{module}.py`. Test functions follow `test_{behavior}_[when_condition]`.

## Running

```bash
# Full suite
python -m pytest tests/ -n auto -v

# Specific module
python -m pytest tests/test_auth.py -n auto -v

# With coverage
python -m pytest tests/ -n auto --cov=backend --cov-report=term-missing
```
