"""
Comprehensive tests for backend/explainability.py
Tests SHAP value generation for model explanations.
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np

from backend.explainability import get_shap_values, generate_static_force_plot


class TestGetShapValues:
    """Tests for the get_shap_values function."""
    
    def test_shap_values_simple_model(self):
        """Test SHAP with a simple model (no estimators_)."""
        # Mock model
        mock_model = MagicMock()
        mock_model.estimators_ = None  # Will fail hasattr check
        del mock_model.estimators_  # Remove attribute completely
        
        # Mock SHAP explainer and force_plot
        mock_explainer = MagicMock()
        mock_explainer.expected_value = 0.5
        mock_explainer.shap_values.return_value = np.array([[0.1, 0.2, 0.3]])
        
        mock_force_plot = MagicMock()
        mock_force_plot.html.return_value = "<div>SHAP Plot</div>"
        
        with patch("backend.explainability.shap.TreeExplainer", return_value=mock_explainer), \
             patch("backend.explainability.shap.force_plot", return_value=mock_force_plot):
            
            input_vector = np.array([[1, 2, 3]])
            feature_names = ["f1", "f2", "f3"]
            
            result = get_shap_values(mock_model, input_vector, feature_names)
            
            assert result is not None
            assert "html" in result
    
    def test_shap_values_voting_classifier(self):
        """Test SHAP with VotingClassifier (has estimators_)."""
        # Mock VotingClassifier
        mock_model = MagicMock()
        mock_estimator = MagicMock()
        mock_model.estimators_ = [mock_estimator]
        
        # Mock SHAP
        mock_explainer = MagicMock()
        mock_explainer.expected_value = [0.3, 0.7]  # List for binary class
        mock_explainer.shap_values.return_value = [
            np.array([[0.1, 0.2]]),  # Class 0
            np.array([[0.3, 0.4]])   # Class 1
        ]
        
        mock_force_plot = MagicMock()
        mock_force_plot.html.return_value = "<div>Plot</div>"
        
        with patch("backend.explainability.shap.TreeExplainer", return_value=mock_explainer), \
             patch("backend.explainability.shap.force_plot", return_value=mock_force_plot):
            
            input_vector = np.array([[1, 2]])
            feature_names = ["f1", "f2"]
            
            result = get_shap_values(mock_model, input_vector, feature_names)
            
            assert result is not None
            assert "html" in result
    
    def test_shap_values_multiclass_structure(self):
        """Test SHAP with multiclass output structure."""
        mock_model = MagicMock()
        del mock_model.estimators_
        
        mock_explainer = MagicMock()
        mock_explainer.expected_value = 0.5
        # Multiclass structure: shape (1, num_classes)
        mock_explainer.shap_values.return_value = np.array([[[0.1, 0.2, 0.3]]])
        
        mock_force_plot = MagicMock()
        mock_force_plot.html.return_value = "<div>Plot</div>"
        
        with patch("backend.explainability.shap.TreeExplainer", return_value=mock_explainer), \
             patch("backend.explainability.shap.force_plot", return_value=mock_force_plot):
            
            result = get_shap_values(mock_model, np.array([[1, 2, 3]]), ["f1", "f2", "f3"])
            
            assert result is not None
    
    def test_shap_values_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        mock_model = MagicMock()
        del mock_model.estimators_
        
        with patch("backend.explainability.shap.TreeExplainer", side_effect=Exception("SHAP Error")):
            result = get_shap_values(mock_model, np.array([[1, 2]]), ["f1", "f2"])
            assert result is None
    
    def test_shap_values_scalar_expected_value(self):
        """Test with scalar expected_value."""
        mock_model = MagicMock()
        del mock_model.estimators_
        
        mock_explainer = MagicMock()
        mock_explainer.expected_value = 0.5  # Scalar
        mock_explainer.shap_values.return_value = np.array([[0.1, 0.2]])
        
        mock_force_plot = MagicMock()
        mock_force_plot.html.return_value = "<div>Plot</div>"
        
        with patch("backend.explainability.shap.TreeExplainer", return_value=mock_explainer), \
             patch("backend.explainability.shap.force_plot", return_value=mock_force_plot) as mock_fp:
            
            result = get_shap_values(mock_model, np.array([[1, 2]]), ["f1", "f2"])
            
            # Verify scalar expected_value was used directly
            call_args = mock_fp.call_args
            assert call_args[0][0] == 0.5  # First positional arg
    
    def test_shap_values_array_expected_value(self):
        """Test with array expected_value."""
        mock_model = MagicMock()
        del mock_model.estimators_
        
        mock_explainer = MagicMock()
        mock_explainer.expected_value = np.array([0.3, 0.7])  # Array
        mock_explainer.shap_values.return_value = np.array([[0.1, 0.2]])
        
        mock_force_plot = MagicMock()
        mock_force_plot.html.return_value = "<div>Plot</div>"
        
        with patch("backend.explainability.shap.TreeExplainer", return_value=mock_explainer), \
             patch("backend.explainability.shap.force_plot", return_value=mock_force_plot) as mock_fp, \
             patch("backend.explainability.np.isscalar", return_value=False):
            
            result = get_shap_values(mock_model, np.array([[1, 2]]), ["f1", "f2"])
            
            assert result is not None


class TestGenerateStaticForcePlot:
    """Tests for the generate_static_force_plot function."""
    
    def test_static_force_plot_placeholder(self):
        """Test that static force plot function exists (currently placeholder)."""
        result = generate_static_force_plot(MagicMock(), np.array([[1, 2]]), ["f1", "f2"])
        # Current implementation returns None (pass)
        assert result is None
