"""
PDF Health Report Generator
============================
Generates downloadable PDF health reports for users.
Uses fpdf (already in requirements).
"""
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HealthReportPDF(FPDF):
    """Custom PDF class with healthcare branding."""
    
    def header(self):
        """Add header to each page."""
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(59, 130, 246)  # Blue
        self.cell(0, 10, 'AI Healthcare System', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'Personal Health Report', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)
        # Line separator
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
    
    def footer(self):
        """Add footer to each page."""
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'This report is AI-generated and should not replace professional medical advice.', align='C', new_x='LMARGIN', new_y='NEXT')
        self.cell(0, 5, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")} | Page {self.page_no()}', align='C')


def generate_health_report(
    user_name: str,
    user_profile: Dict[str, Any],
    health_records: List[Dict[str, Any]]
) -> bytes:
    """
    Generate a PDF health report.
    
    Args:
        user_name: User's full name
        user_profile: Dict with height, weight, dob, blood_type, etc.
        health_records: List of health records with type, prediction, timestamp
        
    Returns:
        bytes: PDF file content
    """
    pdf = HealthReportPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    
    # --- User Info Section ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, f'Health Report for {user_name}', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(60, 60, 60)
    
    # Profile info
    height = user_profile.get('height', 'N/A')
    weight = user_profile.get('weight', 'N/A')
    dob = user_profile.get('dob', 'N/A')
    blood_type = user_profile.get('blood_type', 'N/A')
    
    # Calculate BMI if possible
    bmi_str = "N/A"
    if height and weight and height != 'N/A' and weight != 'N/A':
        try:
            h_m = float(height) / 100
            bmi = round(float(weight) / (h_m ** 2), 1)
            bmi_str = str(bmi)
        except:
            pass
    
    pdf.cell(0, 7, f'Date of Birth: {dob}', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 7, f'Height: {height} cm | Weight: {weight} kg | BMI: {bmi_str}', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 7, f'Blood Type: {blood_type}', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)
    
    # --- Health Records Section ---
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, 'Health Assessment History', new_x='LMARGIN', new_y='NEXT')
    
    if not health_records:
        pdf.set_font('Helvetica', 'I', 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 7, 'No health assessments recorded yet.', new_x='LMARGIN', new_y='NEXT')
    else:
        # Table header
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(50, 8, 'Date', border=1, fill=True)
        pdf.cell(50, 8, 'Assessment Type', border=1, fill=True)
        pdf.cell(80, 8, 'Result', border=1, fill=True, new_x='LMARGIN', new_y='NEXT')
        
        # Table data
        pdf.set_font('Helvetica', '', 10)
        for record in health_records[:20]:  # Limit to 20 records
            date_str = record.get('timestamp', 'N/A')
            if hasattr(date_str, 'strftime'):
                date_str = date_str.strftime('%Y-%m-%d')
            
            record_type = record.get('record_type', 'Unknown')
            prediction = record.get('prediction', 'N/A')
            
            # Color code based on risk
            if 'risk' in prediction.lower() or 'positive' in prediction.lower() or 'yes' in prediction.lower():
                pdf.set_text_color(220, 38, 38)  # Red
            else:
                pdf.set_text_color(22, 163, 74)  # Green
            
            pdf.cell(50, 7, str(date_str)[:10], border=1)
            pdf.cell(50, 7, str(record_type), border=1)
            pdf.cell(80, 7, str(prediction)[:40], border=1, new_x='LMARGIN', new_y='NEXT')
            pdf.set_text_color(60, 60, 60)
    
    pdf.ln(10)
    
    # --- Recommendations Section ---
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, 'General Health Recommendations', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    recommendations = [
        "• Schedule regular check-ups with your healthcare provider",
        "• Maintain a balanced diet rich in fruits and vegetables",
        "• Exercise for at least 30 minutes daily",
        "• Get 7-8 hours of quality sleep each night",
        "• Stay hydrated - drink 8 glasses of water daily",
        "• Monitor your vitals regularly and track changes"
    ]
    for rec in recommendations:
        pdf.cell(0, 6, rec, new_x='LMARGIN', new_y='NEXT')
    
    # Return as bytes
    return bytes(pdf.output())
