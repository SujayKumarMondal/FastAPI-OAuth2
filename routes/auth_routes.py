from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

import auth, config, email_utils
from database import get_db
from models import UserTable
from schemas import UserCreate, Token
from jose import jwt

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=dict)
def register_user(user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing_user = db.query(UserTable).filter(
        (UserTable.username == user_data.username) | (UserTable.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    hashed_password = auth.get_password_hash(user_data.password)
    new_user = UserTable(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate verification token
    verification_token = auth.create_access_token({"sub": user_data.email}, timedelta(minutes=60))
    verification_link = f"http://localhost:7001/verify-email?token={verification_token}"

    # Send verification email in background
    background_tasks.add_task(
        email_utils.send_email,
        to_email=user_data.email,
        subject="Verify your email",
        body=f"<p>Click <a href='{verification_link}'>here</a> to verify your email.</p>"
    )

    # Return in Swagger (for testing)
    return {
        "message": "User registered successfully. Please verify your email.",
        "verification_token": verification_token,
        "verification_link": verification_link
    }

    


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid verification token")
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = auth.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth.create_refresh_token({"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = auth.get_user(username=username, db=db)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = auth.create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = auth.create_refresh_token({"sub": username})

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
