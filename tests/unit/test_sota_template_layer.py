"""
Unit tests for SOTA High-Performance Template Engine (backend/sota_template_layer.py).
"""

from backend.sota_template_layer import SOTATemplateEngine


def test_compiled_template_rendering_and_xss_escaping():
    engine = SOTATemplateEngine()
    engine.register_template(
        "patient_summary_card",
        "<div><h1>Patient: {{ patient_name }}</h1><p>Status: {{ status }}</p></div>",
    )

    context = {
        "patient_name": "<script>alert('XSS')</script>John Doe",
        "status": "STABLE",
    }

    rendered = engine.render_template("patient_summary_card", context)

    assert "John Doe" in rendered
    assert "<script>" not in rendered  # XSS sanitized
    assert "&lt;script&gt;" in rendered

    chunks = engine.stream_rendered_chunks("patient_summary_card", context)
    assert len(chunks) > 0
    assert "".join(chunks) == rendered
