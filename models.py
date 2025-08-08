from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    disabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="user")  # user, admin
