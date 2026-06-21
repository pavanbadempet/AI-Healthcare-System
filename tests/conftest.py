import warnings

warnings.filterwarnings("ignore", message=".*google.generativeai.*", category=FutureWarning)

import os

if hasattr(os, "add_dll_directory"):
    orig_add_dll_directory = os.add_dll_directory
    def patched_add_dll_directory(path):
        if not path:
            return None
        try:
            return orig_add_dll_directory(path)
        except Exception:
            return None
    os.add_dll_directory = patched_add_dll_directory

try:
    from unittest.mock import Mock

    import sklearn.utils._tags
    orig_get_tags = sklearn.utils._tags.get_tags
    def patched_get_tags(estimator):
        if isinstance(estimator, Mock) or not hasattr(estimator, "__sklearn_tags__"):
            mock_tags = Mock()
            mock_tags.estimator_type = "classifier"
            return mock_tags
        try:
            return orig_get_tags(estimator)
        except Exception:
            mock_tags = Mock()
            mock_tags.estimator_type = "classifier"
            return mock_tags
    sklearn.utils._tags.get_tags = patched_get_tags
except ImportError:
    pass

os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

# --- In-Memory DB for Testing ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from backend.prediction import initialize_models

initialize_models()


def _is_e2e_item(item: pytest.Item) -> bool:
    path = str(getattr(item, "path", getattr(item, "fspath", ""))).replace("\\", "/")
    return "/tests/e2e/" in path or path.startswith("tests/e2e/")


def pytest_collection_modifyitems(config, items):
    """
    Keep Playwright sync tests at the end of mixed pytest runs.

    Under Python 3.14 with pytest-playwright 0.7.x, the sync Playwright
    fixture can leave an event loop visible to pytest-asyncio in the same
    process. Running E2E tests last preserves E2E coverage without breaking
    async unit tests collected later.
    """
    e2e_items = []
    other_items = []

    for item in items:
        if _is_e2e_item(item) or item.get_closest_marker("e2e"):
            item.add_marker(pytest.mark.e2e)
            e2e_items.append(item)
        else:
            other_items.append(item)

    items[:] = other_items + e2e_items


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)



@pytest.fixture(scope="function")
def client(db_session):
    """Override dependency and return TestClient."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    # Initialize models (will use mocks if TESTING=1)
    initialize_models()

    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c
    app.dependency_overrides.clear()
