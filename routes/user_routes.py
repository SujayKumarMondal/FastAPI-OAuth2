from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta

import auth, config, email_utils, db_utils
from database import get_db
from models import UserTable, PasswordResetToken
from schemas import User, PasswordResetRequest, PasswordResetConfirm

router = APIRouter(tags=["User"])

def require_role(role_name: str):
    def role_checker(current_user: UserTable = Depends(auth.get_current_active_user)):
        if current_user.role.name != role_name:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

@router.get("/users/me", response_model=User)
def read_users_me(
    current_user: UserTable = Depends(auth.get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    # Log profile access
    db_utils.log_audit(
        db=db,
        user_id=current_user.id,
        action="profile_accessed",
        details="User accessed their profile",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    return current_user


@router.get("/admin-only")
def admin_panel(
    current_user: UserTable = Depends(require_role("admin")),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Admin-only endpoint"""
    # Log admin access
    db_utils.log_audit(
        db=db,
        user_id=current_user.id,
        action="admin_panel_accessed",
        details="User accessed admin panel",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    return {"message": f"Welcome Admin {current_user.username}"}

@router.post("/password-reset-request")
def password_reset_request(
    data: PasswordResetRequest,
    request: Request = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    user = auth.get_user_by_email(data.email, db)
    if not user:
        # Log failed password reset request
        db_utils.log_audit(
            db=db,
            user_id=0,
            action="password_reset_request_failed",
            details=f"Password reset requested for non-existent email: {data.email}",
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        raise HTTPException(status_code=404, detail="Email not found")

    # Create reset token
    reset_token = auth.create_access_token({"sub": data.email}, expires_delta=timedelta(minutes=60))
    
    # Store reset token in database
    db_utils.store_password_reset_token(
        db=db,
        user_id=user.id,
        token=reset_token,
        expires_in_minutes=60
    )
    
    reset_link = f"http://localhost:7003/password-reset-confirm?token={reset_token}"

    # Log password reset request
    db_utils.log_audit(
        db=db,
        user_id=user.id,
        action="password_reset_requested",
        details="Password reset email sent",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )

    # Send reset email in background
    if background_tasks:
        background_tasks.add_task(
            email_utils.send_email,
            to_email=data.email,
            subject="Password Reset",
            body=f"<p>Click <a href='{reset_link}'>here</a> to reset your password.</p>",
            db=db,
            user_id=user.id
        )

    return {"message": "Password reset email sent"}


@router.post("/password-reset-confirm")
def password_reset_confirm(
    data: PasswordResetConfirm,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Confirm password reset"""
    # Verify token from database
    try:
        payload = jwt.decode(data.token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid reset token")
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Check database for valid token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = auth.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password
    user.hashed_password = auth.get_password_hash(data.new_password)
    db.commit()

    # Mark token as used
    db_utils.mark_reset_token_used(db, reset_token.id)

    # Log password change
    db_utils.log_audit(
        db=db,
        user_id=user.id,
        action="password_changed",
        details="Password reset completed",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )

    return {"message": "Password reset successful"}

@router.get("/audit-logs")
def get_audit_logs(
    current_user: UserTable = Depends(auth.get_current_active_user),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user's audit logs"""
    logs = db_utils.get_user_audit_logs(db, current_user.id, limit)
    return {
        "user_id": current_user.id,
        "total_logs": len(logs),
        "logs": [{
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        } for log in logs]
    }

@router.get("/email-logs")
def get_email_logs(
    current_user: UserTable = Depends(auth.get_current_active_user),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user's email logs"""
    logs = db_utils.get_user_email_logs(db, current_user.id, limit)
    return {
        "user_id": current_user.id,
        "total_emails": len(logs),
        "emails": [{
            "id": log.id,
            "to_email": log.to_email,
            "subject": log.subject,
            "status": log.status,
            "sent_at": log.sent_at
        } for log in logs]
    }
