"""
Comprehensive tests for backend/pdf_service.py
Tests the PDF report generation functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import datetime

from backend.pdf_service import PDFReport, generate_medical_report


class TestPDFReport:
    """Tests for the PDFReport class."""
    
    def test_pdf_report_header(self):
        """Test that PDFReport header is rendered correctly."""
        pdf = PDFReport()
        pdf.add_page()  # This triggers header()
        # Just ensure no exception is raised
        output = pdf.output(dest='S')
        assert len(output) > 0
    
    def test_pdf_report_footer(self):
        """Test that PDFReport footer is rendered correctly."""
        pdf = PDFReport()
        pdf.add_page()
        # Footer is rendered on output
        output = pdf.output(dest='S')
        assert len(output) > 0


class TestGenerateMedicalReport:
    """Tests for the generate_medical_report function."""
    
    def test_generate_report_basic(self):
        """Test basic report generation with minimal data."""
        result = generate_medical_report(
            user_name="Test Patient",
            report_type="Diabetes",
            prediction="Low Risk",
            data={"glucose": 100}
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_report_high_risk(self):
        """Test report with High Risk prediction (red color)."""
        result = generate_medical_report(
            user_name="Test Patient",
            report_type="Heart Disease",
            prediction="High Risk",
            data={"bp": 140, "cholesterol": 250}
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_report_with_advice(self):
        """Test report generation with advice list."""
        result = generate_medical_report(
            user_name="Test Patient",
            report_type="Liver",
            prediction="Healthy",
            data={"bilirubin": 1.0},
            advice=["Eat healthy", "Exercise regularly", "Stay hydrated"]
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_report_empty_data(self):
        """Test report with empty data dictionary."""
        result = generate_medical_report(
            user_name="Patient",
            report_type="General",
            prediction="Normal",
            data={}
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_report_complex_data(self):
        """Test report with many data fields."""
        result = generate_medical_report(
            user_name="John Doe",
            report_type="Full Checkup",
            prediction="Needs Attention",
            data={
                "glucose": 120,
                "hba1c": 6.5,
                "cholesterol": 220,
                "blood_pressure": 130,
                "heart_rate": 72,
                "bmi": 28.5
            },
            advice=["Reduce sugar intake", "Monitor regularly"]
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_report_special_characters(self):
        """Test report with special characters in data."""
        result = generate_medical_report(
            user_name="José García",
            report_type="Test",
            prediction="OK",
            data={"test_value": "100mg/dL"}
        )
        assert isinstance(result, bytes)
    
    def test_generate_report_empty_advice(self):
        """Test report with explicitly empty advice list."""
        result = generate_medical_report(
            user_name="Patient",
            report_type="Test",
            prediction="Normal",
            data={"value": 1},
            advice=[]
        )
        assert isinstance(result, bytes)
