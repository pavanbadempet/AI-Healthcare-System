from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "huggingface.yml"


def test_huggingface_sync_removes_onnx_artifacts_before_push():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'find . -name "*.onnx" -type f -delete' in workflow
    assert '-name "*.onnx"' in workflow
