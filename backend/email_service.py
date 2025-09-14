"""
Email Service (Simulated)
=========================
Handles sending transactional emails.
Currently configured for SIMULATION mode to ensure stability.
Logs emails to server console instead of risking SMTP crashes.
"""
import logging
import os

logger = logging.getLogger(__name__)

def send_booking_confirmation(to_email: str, patient_name: str, doctor_name: str, date_time: str, link: str):
    """
    Simulates sending a booking confirmation email.
    In production, this would use SMTP or SendGrid.
    """
    try:
        # Construct Email Body
        subject = f"Appointment Confirmed: {doctor_name}"
        body = f"""
        Dear {patient_name},
        
        Your appointment with {doctor_name} has been confirmed.
        
        📅 Date & Time: {date_time}
        🔗 Video Link: {link}
        
        Please join 5 minutes early.
        
        Regards,
        AI Healthcare System
        """
        
        # Log instead of Send (Safety First)
        logger.info(f"📧 [EMAIL SENT TO {to_email}] Subject: {subject}")
        logger.info(f"📧 Body: {body.strip()}")
        
        # If we had SMTP credentials, we would use them here:
        # if os.getenv("SMTP_SERVER"):
        #     send_smtp_email(...)
            
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
