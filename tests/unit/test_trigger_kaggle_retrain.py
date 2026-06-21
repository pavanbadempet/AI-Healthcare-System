import json
from pathlib import Path

import pytest

from scripts.runners import trigger_kaggle_retrain


def _point_script_at_temp_repo(monkeypatch, tmp_path):
    script_path = tmp_path / "scripts" / "runners" / "trigger_kaggle_retrain.py"
    script_path.parent.mkdir(parents=True)
    monkeypatch.setattr(trigger_kaggle_retrain, "__file__", str(script_path))


def test_generated_notebook_references_kaggle_secrets_without_materializing_values(
    monkeypatch,
    tmp_path,
):
    _point_script_at_temp_repo(monkeypatch, tmp_path)
    sentinels = {
        "DATABASE_URL": "postgresql://sentinel-database",
        "ADMIN_JWT_TOKEN": "sentinel-admin-token",
        "HF_TOKEN": "sentinel-hf-token",
    }
    for name, value in sentinels.items():
        monkeypatch.setenv(name, value)

    build_dir = Path(trigger_kaggle_retrain.build_kaggle_kernel("security-test"))
    notebook_text = (build_dir / "healthcare_retrain_notebook.ipynb").read_text()
    notebook = json.loads(notebook_text)
    secret_setup_source = "".join(notebook["cells"][2]["source"])

    for secret_name, secret_value in sentinels.items():
        assert secret_value not in notebook_text
        assert f'get_secret("{secret_name}")' in secret_setup_source

    assert notebook["metadata"]["kernelspec"]["name"] == "python3"


def test_retrain_cleanup_runs_when_kaggle_push_fails(monkeypatch, tmp_path):
    build_dir = tmp_path / "kaggle_build"
    build_dir.mkdir()
    (build_dir / "healthcare_retrain_notebook.ipynb").write_text("temporary")

    monkeypatch.setattr(
        trigger_kaggle_retrain,
        "setup_kaggle_credentials",
        lambda: ("security-test", "kaggle-token"),
    )
    monkeypatch.setattr(
        trigger_kaggle_retrain,
        "build_kaggle_kernel",
        lambda username: str(build_dir),
    )

    def fail_push(build_path, username, key):
        raise RuntimeError("simulated upload failure")

    monkeypatch.setattr(trigger_kaggle_retrain, "push_to_kaggle", fail_push)

    with pytest.raises(RuntimeError, match="simulated upload failure"):
        trigger_kaggle_retrain.run_retrain()

    assert not build_dir.exists()
