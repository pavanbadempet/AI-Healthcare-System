import os
import subprocess
import sys

import sqlalchemy as sa


def _run_alembic(database_url, *args):
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": database_url,
            "TESTING": "",
            "SECRET_KEY": "test_secret_for_migration_tests",
            "SUPABASE_URL": "",
            "SUPABASE_KEY": "",
            "AXIOM_TOKEN": "",
        }
    )
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_fresh_sqlite_database_upgrades_to_alembic_head(tmp_path):
    database_path = tmp_path / "fresh.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    result = _run_alembic(database_url, "upgrade", "head")

    assert result.returncode == 0, result.stdout + result.stderr

    engine = sa.create_engine(database_url)
    inspector = sa.inspect(engine)
    with engine.connect() as connection:
        revision = connection.scalar(sa.text("SELECT version_num FROM alembic_version"))

    assert revision == "c1234567890a"
    assert "doctor_id" not in {column["name"] for column in inspector.get_columns("users")}
    assert {constraint["name"] for constraint in inspector.get_unique_constraints("monitoring_signals")} == {
        "uq_monitoring_signal_vital_type"
    }
    appointment_status = {
        constraint["name"]: constraint["sqltext"] for constraint in inspector.get_check_constraints("appointments")
    }
    assert "Rescheduled" in appointment_status["check_appt_status"]


def test_startup_migrations_adopt_unversioned_legacy_sqlite_database(tmp_path):
    database_path = tmp_path / "legacy.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    baseline = _run_alembic(database_url, "upgrade", "0001_baseline")
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr

    engine = sa.create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(sa.text("DELETE FROM alembic_version"))
        connection.execute(
            sa.text(
                """
                INSERT INTO users (id, username, hashed_password, role, email)
                VALUES (1, 'legacy-user', 'hash', 'patient', 'legacy@example.invalid')
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO chat_logs (id, user_id, role, content)
                VALUES (1, 1, 'user', 'legacy message')
                """
            )
        )
        connection.execute(sa.text("CREATE TABLE _alembic_tmp_users (id INTEGER)"))

    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": database_url,
            "TESTING": "",
            "SECRET_KEY": "test_secret_for_migration_tests",
            "SUPABASE_URL": "",
            "SUPABASE_KEY": "",
            "AXIOM_TOKEN": "",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from backend.main import run_migrations; run_migrations()",
        ],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    inspector = sa.inspect(engine)
    with engine.connect() as connection:
        revision = connection.scalar(sa.text("SELECT version_num FROM alembic_version"))
        user_count = connection.scalar(sa.text("SELECT COUNT(*) FROM users WHERE id = 1"))
        chat_count = connection.scalar(sa.text("SELECT COUNT(*) FROM chat_logs WHERE user_id = 1"))
        foreign_key_violations = connection.execute(
            sa.text("PRAGMA foreign_key_check")
        ).fetchall()

    assert revision == "c1234567890a"
    assert user_count == 1
    assert chat_count == 1
    assert foreign_key_violations == []
    assert {"is_deleted", "deleted_at"} <= {
        column["name"] for column in inspector.get_columns("users")
    }
    assert {
        "clinical_alerts",
        "federated_sync_audits",
        "model_feedbacks",
        "patient_insights",
        "smart_apps",
        "smart_launch_contexts",
    } <= set(inspector.get_table_names())
    assert "_alembic_tmp_users" not in inspector.get_table_names()


def test_deployed_legacy_revision_upgrades_to_head(tmp_path):
    database_path = tmp_path / "deployed-legacy.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    baseline = _run_alembic(database_url, "upgrade", "0001_baseline")
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr

    engine = sa.create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                UPDATE alembic_version
                SET version_num = '4bccc856108e'
                """
            )
        )

    result = _run_alembic(database_url, "upgrade", "head")
    assert result.returncode == 0, result.stdout + result.stderr

    inspector = sa.inspect(engine)
    with engine.connect() as connection:
        revision = connection.scalar(sa.text("SELECT version_num FROM alembic_version"))

    assert revision == "c1234567890a"
    assert {"is_deleted", "deleted_at"} <= {
        column["name"] for column in inspector.get_columns("users")
    }
