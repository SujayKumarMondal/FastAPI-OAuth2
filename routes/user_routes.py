from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from jose import jwt

import auth, config, email_utils
from database import get_db
from models import UserTable
from schemas import User, PasswordResetRequest, PasswordResetConfirm

router = APIRouter(tags=["User"])


@router.get("/users/me", response_model=User)
def read_users_me(current_user: UserTable = Depends(auth.get_current_active_user)):
    return current_user


@router.post("/password-reset-request")
def password_reset_request(data: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = auth.get_user_by_email(data.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    reset_token = auth.create_access_token({"sub": data.email}, expires_delta=None)
    reset_link = f"http://localhost:7001/password-reset-confirm?token={reset_token}"

    background_tasks.add_task(
        email_utils.send_email,
        to_email=data.email,
        subject="Password Reset",
        body=f"<p>Click <a href='{reset_link}'>here</a> to reset your password.</p>"
    )

    return {"message": "Password reset email sent"}


@router.post("/password-reset-confirm")
def password_reset_confirm(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid reset token")
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = auth.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = auth.get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password reset successful"}
