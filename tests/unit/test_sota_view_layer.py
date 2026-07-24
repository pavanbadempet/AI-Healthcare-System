"""
Unit tests for SOTA Server-Driven View Layer Engine (backend/sota_view_layer.py).
"""

from backend.sota_view_layer import SOTAViewLayerEngine


def test_sdui_view_tree_rendering_and_diffing():
    engine = SOTAViewLayerEngine()

    vitals_1 = {"heart_rate": 75}
    tree_1 = engine.render_clinical_dashboard_view("P_1001", vitals_1)

    assert tree_1.type == "PageContainer"
    assert len(tree_1.children) == 2
    assert tree_1.children[0].props["value"] == 75

    vitals_2 = {"heart_rate": 110}
    tree_2 = engine.render_clinical_dashboard_view("P_1001", vitals_2)
    assert tree_2.children[0].props["status"] == "WARNING"

    # Test view diffing
    patches = engine.diff_view_trees(tree_1, tree_2)
    assert isinstance(patches, list)
