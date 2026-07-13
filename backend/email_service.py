"""
Email Service
=============
Handles sending transactional emails via SMTP.
Falls back to logging (simulation) if SMTP_SERVER is not configured.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

def _send_email_via_smtp(to_email: str, subject: str, html_body: str, plain_body: str) -> bool:
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not smtp_server or not smtp_user:
        logger.info(f"SIMULATED EMAIL to {to_email}: {subject}")
        return True
        
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
        return False

def send_booking_confirmation(to_email: str, patient_name: str, doctor_name: str, date_time: str, link: str):
    subject = f"Appointment Confirmed: {doctor_name}"
    plain_body = f"""Dear {patient_name},
Your appointment with {doctor_name} has been confirmed.
Date & Time: {date_time}
Video Link: {link}
Please join 5 minutes early.
"""
    html_body = f"""
    <html>
      <body>
        <p>Dear {patient_name},</p>
        <p>Your appointment with <strong>{doctor_name}</strong> has been confirmed.</p>
        <p>📅 Date & Time: {date_time}</p>
        <p>🔗 <a href="{link}">Video Link</a></p>
        <p>Please join 5 minutes early.</p>
        <p>Regards,<br/>AI Healthcare System</p>
      </body>
    </html>
    """
    return _send_email_via_smtp(to_email, subject, html_body, plain_body)

def send_password_reset(to_email: str, username: str, reset_link: str) -> bool:
    subject = "Reset Your Password - AI Healthcare System"
    plain_body = f"""Dear {username},
You requested to reset your password for the AI Healthcare System.
Please click the link below to reset your password (valid for 15 minutes):
{reset_link}
If you did not request this, please ignore this email.
"""
    html_body = f"""
    <html>
      <body>
        <p>Dear {username},</p>
        <p>You requested to reset your password for the AI Healthcare System.</p>
        <p>🔗 <a href="{reset_link}">Click here to reset your password</a> (valid for 15 minutes)</p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Regards,<br/>AI Healthcare System</p>
      </body>
    </html>
    """
    return _send_email_via_smtp(to_email, subject, html_body, plain_body)
