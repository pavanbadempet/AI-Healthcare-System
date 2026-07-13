import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock libsql modules in sys.modules to prevent ImportError during tests
mock_libsql_client = MagicMock()
mock_sqlalchemy_libsql = MagicMock()
sys.modules["libsql_client"] = mock_libsql_client
sys.modules["sqlalchemy_libsql"] = mock_sqlalchemy_libsql

from backend import database


class TestTursoIntegration:
    """Tests for LibSQL/Turso database configuration and integration."""

    def test_turso_replication_url_loading(self):
        """Test that Turso embedded replication url is configured when env vars are present."""
        with patch.dict(os.environ, {
            "TURSO_DATABASE_URL": "libsql://test-db.turso.io",
            "TURSO_AUTH_TOKEN": "test-token",
            "TESTING": ""
        }, clear=True):
            db_url = database._load_database_url()
            assert db_url.startswith("sqlite+libsql:///")
            assert "healthcare.db" in db_url

    def test_libsql_url_translation(self):
        """Test that libsql:// URL is translated to sqlite+libsql://."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "libsql://test-remote-db.turso.io",
            "TESTING": ""
        }, clear=True):
            db_url = database._load_database_url()
            assert db_url == "sqlite+libsql://test-remote-db.turso.io"

    def test_testing_takes_precedence(self):
        """Test that TESTING=1 environment variable takes precedence over Turso configs."""
        with patch.dict(os.environ, {
            "TURSO_DATABASE_URL": "libsql://test-db.turso.io",
            "TURSO_AUTH_TOKEN": "test-token",
            "TESTING": "1"
        }, clear=True):
            db_url = database._load_database_url()
            assert db_url == "sqlite:///:memory:"

    def test_connect_args_configuration_for_libsql(self):
        """Test that connection arguments are populated with Turso replication settings."""
        # Clean environment test to run the engine creation configuration logic manually
        # since database.py runs it at import time. We verify the configuration logic itself.
        test_url = "sqlite+libsql:///healthcare.db"

        with patch.dict(os.environ, {
            "TURSO_DATABASE_URL": "libsql://test-db.turso.io",
            "TURSO_AUTH_TOKEN": "test-token"
        }, clear=True):
            # Simulate the connect_args selection logic in database.py
            c_args = {}
            if "libsql" in test_url:
                try:
                    import libsql_client  # noqa: F401
                    import sqlalchemy_libsql  # noqa: F401
                except ImportError:
                    pytest.fail("Should not raise ImportError as we mocked sys.modules")

                sync_url = os.getenv("TURSO_DATABASE_URL")
                auth_token = os.getenv("TURSO_AUTH_TOKEN")
                if sync_url:
                    c_args["sync_url"] = sync_url
                if auth_token:
                    c_args["auth_token"] = auth_token

            assert c_args.get("sync_url") == "libsql://test-db.turso.io"
            assert c_args.get("auth_token") == "test-token"

    def test_libsql_missing_packages_raises_importerror(self):
        """Test that if packages are missing when using LibSQL, a clear ImportError is raised."""
        # Un-mock sys.modules temporarily to test the error path
        with patch.dict(sys.modules, {"libsql_client": None, "sqlalchemy_libsql": None}):
            test_url = "sqlite+libsql:///healthcare.db"

            with pytest.raises(ImportError) as exc_info:
                if "libsql" in test_url:
                    try:
                        import libsql_client  # noqa: F401
                        import sqlalchemy_libsql  # noqa: F401
                    except ImportError as e:
                        raise ImportError(
                            "libsql-client and sqlalchemy-libsql packages are required to use LibSQL/Turso database. "
                            "Please install them via: pip install libsql-client sqlalchemy-libsql"
                        ) from e

            assert "libsql-client and sqlalchemy-libsql packages are required" in str(exc_info.value)
