"""
Utility functions for database operations including audit logging and email tracking.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import AuditLog, EmailLog, PasswordResetToken, TokenBlacklist
from typing import Optional


def log_audit(
    db: Session,
    user_id: int,
    action: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """
    Log user actions to the audit log.
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: Type of action (login, logout, register, password_reset, etc.)
        details: Additional details about the action
        ip_address: IP address of the request
        user_agent: User agent string from the request
    
    Returns:
        AuditLog object
    """
    audit = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def log_email(
    db: Session,
    to_email: str,
    subject: str,
    body: str,
    status: str = "sent",
    error_message: Optional[str] = None,
    user_id: Optional[int] = None
) -> EmailLog:
    """
    Log email sending attempts.
    
    Args:
        db: Database session
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        status: Status of email (sent, failed, pending)
        error_message: Error message if failed
        user_id: ID of the user (if applicable)
    
    Returns:
        EmailLog object
    """
    email_log = EmailLog(
        to_email=to_email,
        subject=subject,
        body=body,
        status=status,
        error_message=error_message,
        user_id=user_id
    )
    db.add(email_log)
    db.commit()
    db.refresh(email_log)
    return email_log


def store_password_reset_token(
    db: Session,
    user_id: int,
    token: str,
    expires_in_minutes: int = 60
) -> PasswordResetToken:
    """
    Store password reset token in database.
    
    Args:
        db: Database session
        user_id: ID of the user
        token: Reset token
        expires_in_minutes: Token expiration time in minutes
    
    Returns:
        PasswordResetToken object
    """
    expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def mark_reset_token_used(
    db: Session,
    token_id: int
) -> PasswordResetToken:
    """
    Mark a reset token as used.
    
    Args:
        db: Database session
        token_id: ID of the reset token
    
    Returns:
        Updated PasswordResetToken object
    """
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.id == token_id).first()
    if reset_token:
        reset_token.used = True
        reset_token.used_at = datetime.utcnow()
        db.commit()
        db.refresh(reset_token)
    return reset_token


def add_token_to_blacklist(
    db: Session,
    user_id: int,
    token: str,
    expires_at: datetime
) -> TokenBlacklist:
    """
    Add a token to the blacklist (for logout functionality).
    
    Args:
        db: Database session
        user_id: ID of the user
        token: The token to blacklist
        expires_at: When the token expires
    
    Returns:
        TokenBlacklist object
    """
    blacklisted_token = TokenBlacklist(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(blacklisted_token)
    db.commit()
    db.refresh(blacklisted_token)
    return blacklisted_token


def is_token_blacklisted(db: Session, token: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        db: Database session
        token: Token to check
    
    Returns:
        True if token is blacklisted, False otherwise
    """
    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    return blacklisted is not None


def get_user_audit_logs(
    db: Session,
    user_id: int,
    limit: int = 50
) -> list:
    """
    Get audit logs for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
        limit: Maximum number of logs to return
    
    Returns:
        List of AuditLog objects
    """
    return db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()


def get_user_email_logs(
    db: Session,
    user_id: int,
    limit: int = 50
) -> list:
    """
    Get email logs for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
        limit: Maximum number of logs to return
    
    Returns:
        List of EmailLog objects
    """
    return db.query(EmailLog).filter(
        EmailLog.user_id == user_id
    ).order_by(EmailLog.sent_at.desc()).limit(limit).all()
