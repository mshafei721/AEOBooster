from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    auth_token = Column(String, nullable=True)  # For Clerk/Supabase integration
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationship to projects
    projects = relationship("Project", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    site_url = Column(String, nullable=False)
    business_category = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationship to user
    user = relationship("User", back_populates="projects")