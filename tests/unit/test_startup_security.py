from unittest.mock import MagicMock, patch

from backend import main


def test_default_admin_seed_skips_without_explicit_credentials(monkeypatch):
    monkeypatch.delenv("DEFAULT_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

    with patch("backend.main.database.SessionLocal") as session_factory:
        main.create_default_admin()

    session_factory.assert_not_called()


def test_default_admin_seed_uses_explicit_credentials(monkeypatch):
    monkeypatch.setenv("DEFAULT_ADMIN_USERNAME", "ops-admin")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "StrongAdminPassword123!")
    monkeypatch.setenv("DEFAULT_ADMIN_EMAIL", "ops-admin@example.com")

    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None

    with patch("backend.main.database.SessionLocal", return_value=session):
        main.create_default_admin()

    session.add.assert_called_once()
    created_user = session.add.call_args.args[0]
    assert created_user.username == "ops-admin"
    assert created_user.email == "ops-admin@example.com"
    assert created_user.hashed_password != "StrongAdminPassword123!"
    session.commit.assert_called_once()
    session.close.assert_called_once()


def test_default_admin_seed_hides_error_details(monkeypatch, caplog):
    monkeypatch.setenv("DEFAULT_ADMIN_USERNAME", "ops-admin")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "StrongAdminPassword123!")

    session = MagicMock()
    sensitive_error = "seed failed password=StrongAdminPassword123! db_password=secret-db"
    session.query.side_effect = Exception(sensitive_error)
    caplog.set_level("ERROR", logger="backend.main")

    with patch("backend.main.database.SessionLocal", return_value=session):
        main.create_default_admin()

    assert sensitive_error not in caplog.text
    assert "StrongAdminPassword123!" not in caplog.text
    assert "secret-db" not in caplog.text
    session.close.assert_called_once()


def test_run_migrations_hides_column_error_details(caplog):
    sensitive_error = "alter table failed db_password=secret-db patient_name=Sensitive User"
    caplog.set_level("WARNING", logger="backend.main")

    with patch("alembic.command.upgrade", side_effect=Exception(sensitive_error)), \
         patch("os.getenv", return_value=None):
        main.run_migrations()

    assert sensitive_error not in caplog.text
    assert "secret-db" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_postgres_startup_does_not_restore_sqlite_backup(monkeypatch):
    monkeypatch.setattr(
        main.database,
        "SQLALCHEMY_DATABASE_URL",
        "postgresql://user:password@example.invalid/database",
    )

    with patch("backend.supabase_backup.restore_database") as restore_database:
        restored = main.restore_sqlite_backup()

    assert restored is False
    restore_database.assert_not_called()


def test_sqlite_startup_restores_configured_backup(monkeypatch):
    monkeypatch.setattr(
        main.database,
        "SQLALCHEMY_DATABASE_URL",
        "sqlite:///./healthcare.db",
    )

    with patch("backend.supabase_backup.restore_database", return_value=True) as restore_database:
        restored = main.restore_sqlite_backup()

    assert restored is True
    restore_database.assert_called_once_with()


def test_postgres_shutdown_does_not_backup_sqlite_database(monkeypatch):
    monkeypatch.setattr(
        main.database,
        "SQLALCHEMY_DATABASE_URL",
        "postgresql://user:password@example.invalid/database",
    )

    with patch("backend.supabase_backup.backup_database") as backup_database:
        backed_up = main.backup_sqlite_database()

    assert backed_up is False
    backup_database.assert_not_called()
