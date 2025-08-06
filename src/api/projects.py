from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
import re
from urllib.parse import urlparse

from ..models.database import get_db
from ..models.project import Project, User
from ..constants.business_categories import BUSINESS_CATEGORIES, is_valid_business_category

router = APIRouter()

class ProjectCreate(BaseModel):
    site_url: str
    business_category: Optional[str] = None
    
    @field_validator('business_category')
    @classmethod
    def validate_business_category(cls, v):
        if v and not is_valid_business_category(v):
            raise ValueError(f'Invalid business category. Must be one of: {", ".join(BUSINESS_CATEGORIES)}')
        return v
    
    @field_validator('site_url')
    @classmethod
    def validate_url(cls, v):
        # Reject clearly invalid inputs early
        if not v or not v.strip():
            raise ValueError('URL is required')
        
        v = v.strip()
        
        # Reject URLs that are clearly invalid
        invalid_patterns = [
            r'^https?://$',  # Just protocol
            r'^[a-zA-Z]+$',  # Single word without dots
            r'.*\.{2,}.*',   # Multiple consecutive dots
            r'^ftp://',      # FTP protocol not supported
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, v):
                raise ValueError('Please enter a valid website URL')
        
        # Add protocol if missing
        if not v.startswith(('http://', 'https://')):
            v = f'https://{v}'
        
        # Parse and validate URL
        try:
            parsed = urlparse(v)
            if not parsed.netloc or not parsed.scheme:
                raise ValueError('Invalid URL format')
            
            # Domain must contain at least one dot (except localhost)
            domain = parsed.netloc.split(':')[0].lower()
            if domain != 'localhost' and '.' not in domain:
                raise ValueError('Invalid domain format')
            
            # Basic domain validation - must have valid characters
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$'
            if not re.match(domain_pattern, domain):
                raise ValueError('Invalid domain format')
            
            # Domain parts should not be empty
            domain_parts = domain.split('.')
            if any(not part for part in domain_parts):
                raise ValueError('Invalid domain format')
                
            return v
        except ValueError:
            raise
        except Exception:
            raise ValueError('Please enter a valid website URL')

class ProjectResponse(BaseModel):
    project_id: str
    status: str

# Mock user for development - In production, this would come from auth token
def get_current_user(db: Session = Depends(get_db)) -> User:
    # For demo purposes, create/get a default user
    user = db.query(User).filter(User.email == "demo@example.com").first()
    if not user:
        user = User(email="demo@example.com", auth_token="demo_token")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project with the provided website URL.
    
    - **site_url**: The website URL to analyze (protocol will be added if missing)
    - **business_category**: Optional business category for better analysis
    """
    try:
        # Create new project
        new_project = Project(
            user_id=current_user.id,
            site_url=project_data.site_url,
            business_category=project_data.business_category
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        return ProjectResponse(
            project_id=new_project.id,
            status="created"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details by ID"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {
        "project_id": project.id,
        "site_url": project.site_url,
        "business_category": project.business_category,
        "created_at": project.created_at,
        "status": "created"
    }