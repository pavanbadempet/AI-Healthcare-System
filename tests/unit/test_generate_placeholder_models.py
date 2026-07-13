import sys
from types import SimpleNamespace

from scripts import generate_placeholder_models


def test_hf_placeholder_download_preserves_existing_models_python_package(
    tmp_path,
    monkeypatch,
):
    models_package = tmp_path / "models"
    models_package.mkdir()
    package_init = models_package / "__init__.py"
    package_init.write_text("# package marker\n", encoding="utf-8")
    download_kwargs = {}

    class FakeHfApi:
        def __init__(self, token):
            self.token = token

        def list_repo_files(self, repo_id, repo_type):
            return ["models/diabetes_model.pkl"]

        def hf_hub_download(
            self,
            repo_id,
            repo_type,
            filename,
            local_dir,
            **kwargs,
        ):
            download_kwargs.update(kwargs)
            destination = tmp_path / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"downloaded-model")
            return str(destination)

    monkeypatch.setattr(generate_placeholder_models, "BACKEND_DIR", str(tmp_path))
    monkeypatch.setenv("HF_TOKEN", "test-token")
    monkeypatch.setenv("HF_DATASET_ID", "test/models")
    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(HfApi=FakeHfApi),
    )

    generate_placeholder_models.generate_placeholders()

    assert package_init.read_text(encoding="utf-8") == "# package marker\n"
    assert (tmp_path / "diabetes_model.pkl").read_bytes() == b"downloaded-model"
    assert "local_dir_use_symlinks" not in download_kwargs
