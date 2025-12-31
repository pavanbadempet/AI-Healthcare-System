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
    If SMTP_SERVER is set, it sends a REAL email.
    Otherwise, logs it.
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
        
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if smtp_server and smtp_user:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, to_email, text)
            server.quit()
            logger.info(f"✅ Real Email sent to {to_email}")
        else:
            # Fallback to simulation
            logger.info(f"📧 [SIMULATION] To: {to_email} | Subject: {subject}")
            
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
