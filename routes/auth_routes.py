from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
import auth, config, email_utils, db_utils
from database import get_db
from models import UserTable, RoleTable, PasswordResetToken
from schemas import UserCreate, Token
from jose import jwt

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=dict)
def register_user(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user and send verification email"""
    existing_user = db.query(UserTable).filter(
        (UserTable.username == user_data.username) | (UserTable.email == user_data.email)
    ).first()
    if existing_user:
        # Log registration attempt for existing user
        db_utils.log_audit(
            db=db,
            user_id=existing_user.id,
            action="register_attempt_existing_user",
            details=f"Registration attempt with existing email/username",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        access_token = auth.create_access_token({"sub": existing_user.email}, timedelta(minutes=15))
        refresh_token = auth.create_refresh_token({"sub": existing_user.email}, timedelta(days=7))
        verification_token = auth.create_access_token({"sub": user_data.email}, timedelta(minutes=60))
        return {
            "message": "User already registered. Returning tokens.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "verification_token": verification_token,
        }

    # Get or create default "user" role
    default_role = db.query(RoleTable).filter(RoleTable.name == "user").first()
    if not default_role:
        default_role = RoleTable(name="user")
        db.add(default_role)
        db.commit()
        db.refresh(default_role)

    # Create new user
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = UserTable(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_verified=False,
        role_id=default_role.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log registration
    db_utils.log_audit(
        db=db,
        user_id=new_user.id,
        action="user_registered",
        details=f"User registration completed",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # Create verification token
    verification_token = auth.create_access_token({"sub": user_data.email}, timedelta(minutes=60))
    verification_link = f"http://localhost:7003/verify-email?token={verification_token}"

    # Send verification email in background
    background_tasks.add_task(
        email_utils.send_email,
        to_email=user_data.email,
        subject="Verify your email",
        body=f"<p>Click <a href='{verification_link}'>here</a> to verify your email.</p>",
        db=db,
        user_id=new_user.id
    )

    # Issue tokens for newly registered user
    access_token = auth.create_access_token({"sub": user_data.email}, timedelta(minutes=15))
    refresh_token = auth.create_refresh_token({"sub": user_data.email}, timedelta(days=7))

    return {
        "message": "User registered successfully. Please verify your email.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "verification_token": verification_token,
        "verification_link": verification_link
    }

@router.get("/verify-email")
def verify_email(token: str, request: Request, db: Session = Depends(get_db)):
    """Verify email address"""
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

    # Verify email
    user.is_verified = True
    db.commit()

    # Log email verification
    db_utils.log_audit(
        db=db,
        user_id=user.id,
        action="email_verified",
        details=f"Email verified: {email}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {"message": "Email verified successfully"}

@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Authenticate user and issue tokens"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Log failed login attempt
        db_utils.log_audit(
            db=db,
            user_id=0,  # Unknown user
            action="login_failed",
            details=f"Failed login attempt for username: {form_data.username}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Log successful login
    db_utils.log_audit(
        db=db,
        user_id=user.id,
        action="user_login",
        details=f"User login successful",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )

    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth.create_refresh_token(
        {"sub": user.username},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    token: str,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
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

    # Log token refresh
    db_utils.log_audit(
        db=db,
        user_id=user.id,
        action="token_refreshed",
        details=f"Access token refreshed",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout(
    current_user: UserTable = Depends(auth.get_current_active_user),
    token: str = Depends(auth.oauth2_scheme),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Logout user by blacklisting token"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        exp = datetime.fromtimestamp(payload.get("exp"))
        
        # Add token to blacklist
        db_utils.add_token_to_blacklist(
            db=db,
            user_id=current_user.id,
            token=token,
            expires_at=exp
        )
        
        # Log logout
        db_utils.log_audit(
            db=db,
            user_id=current_user.id,
            action="user_logout",
            details=f"User logout",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return {"message": "Logged out successfully"}
    except:
        raise HTTPException(status_code=400, detail="Error logging out")
