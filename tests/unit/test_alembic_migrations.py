from scripts.runners.run_alembic_migrations import AlembicMigrationRunner, run_database_migrations


def test_alembic_migration_runner():
    runner = AlembicMigrationRunner("sqlite:///:memory:")
    res = runner.run_migrations_upgrade_head()
    assert res["status"] == "success"
    assert res["zero_downtime"] is True
    assert res["current_revision"] == "v2026_07_22_initial_schema"


def test_run_database_migrations_helper():
    info = run_database_migrations()
    assert info["status"] == "success"
    assert info["zero_downtime"] is True
