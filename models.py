from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    user = "user"

class RoleTable(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("UserTable", back_populates="role")

class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    disabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"), default=1)  # default to "user" role
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    role = relationship("RoleTable", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    tokens = relationship("TokenBlacklist", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user")

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(100), index=True, nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default="sent")  # sent, failed, pending
    error_message = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)

    user = relationship("UserTable", back_populates="reset_tokens")

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserTable", back_populates="tokens")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), index=True, nullable=False)  # login, logout, register, password_reset, etc.
    details = Column(Text, nullable=True)  # Additional details in JSON format
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("UserTable", back_populates="audit_logs")