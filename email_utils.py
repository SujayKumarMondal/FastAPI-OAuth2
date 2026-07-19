import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_USER, EMAIL_PORT, EMAIL_HOST, EMAIL_PASS
from sqlalchemy.orm import Session
from typing import Optional

def send_email(
    to_email: str,
    subject: str,
    body: str,
    db: Optional[Session] = None,
    user_id: Optional[int] = None
):
    """
    Send email and log it to the database.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML)
        db: Database session (for logging)
        user_id: ID of the user (if applicable)
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        
        # Log successful email
        if db:
            from models import EmailLog
            email_log = EmailLog(
                to_email=to_email,
                subject=subject,
                body=body,
                status="sent",
                user_id=user_id
            )
            db.add(email_log)
            db.commit()
        
        return True
    
    except Exception as e:
        # Log failed email
        if db:
            from models import EmailLog
            email_log = EmailLog(
                to_email=to_email,
                subject=subject,
                body=body,
                status="failed",
                error_message=str(e),
                user_id=user_id
            )
            db.add(email_log)
            db.commit()
        
        print(f"Error sending email to {to_email}: {str(e)}")
        return False
