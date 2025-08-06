import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from main import app
from src.models.database import get_db, Base
from src.models.project import User, Project
from src.constants.business_categories import BUSINESS_CATEGORIES

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and clean up after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestProjectsAPI:
    
    def test_create_project_valid_url(self):
        """Test creating a project with a valid URL"""
        response = client.post(
            "/api/projects",
            json={"site_url": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "created"
    
    def test_create_project_url_without_protocol(self):
        """Test creating a project with URL missing protocol"""
        response = client.post(
            "/api/projects",
            json={"site_url": "example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "created"
    
    def test_create_project_with_business_category(self):
        """Test creating a project with business category"""
        response = client.post(
            "/api/projects",
            json={
                "site_url": "https://example.com",
                "business_category": "e-commerce"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "created"
    
    def test_create_project_with_invalid_business_category(self):
        """Test creating a project with invalid business category"""
        response = client.post(
            "/api/projects",
            json={
                "site_url": "https://example.com",
                "business_category": "invalid-category"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_project_without_business_category(self):
        """Test creating a project without business category (optional field)"""
        response = client.post(
            "/api/projects",
            json={"site_url": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "created"
    
    def test_all_business_categories_valid(self):
        """Test that all predefined business categories are accepted"""
        for category in BUSINESS_CATEGORIES:
            response = client.post(
                "/api/projects",
                json={
                    "site_url": f"https://example-{category}.com",
                    "business_category": category
                }
            )
            assert response.status_code == 200, f"Failed for category: {category}"
    
    def test_create_project_invalid_url(self):
        """Test creating a project with invalid URL"""
        invalid_urls = [
            "not-a-url",
            "http://",
            "https://",
            "ftp://example.com",
            "example",
            "http://invalid..domain.com"
        ]
        
        for invalid_url in invalid_urls:
            response = client.post(
                "/api/projects",
                json={"site_url": invalid_url}
            )
            assert response.status_code == 422  # Validation error
    
    def test_create_project_missing_url(self):
        """Test creating a project without URL"""
        response = client.post(
            "/api/projects",
            json={"business_category": "E-commerce"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_project_existing(self):
        """Test getting an existing project"""
        # First create a project
        create_response = client.post(
            "/api/projects",
            json={"site_url": "https://example.com"}
        )
        project_id = create_response.json()["project_id"]
        
        # Then get it
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["project_id"] == project_id
        assert data["site_url"] == "https://example.com"
        assert data["status"] == "created"
        assert "created_at" in data
    
    def test_get_project_not_found(self):
        """Test getting a non-existent project"""
        response = client.get("/api/projects/non-existent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"
    
    def test_url_validation_edge_cases(self):
        """Test URL validation with various edge cases"""
        valid_urls = [
            "https://example.com",
            "http://example.com", 
            "https://www.example.com",
            "https://subdomain.example.com",
            "https://example.co.uk",
            "https://example.com/path",
            "https://example.com:8080",
            "example.com",
            "www.example.com",
            "subdomain.example.co.uk"
        ]
        
        for valid_url in valid_urls:
            response = client.post(
                "/api/projects",
                json={"site_url": valid_url}
            )
            assert response.status_code == 200, f"Valid URL failed: {valid_url}"
    
    def test_api_response_structure(self):
        """Test that API responses have correct structure"""
        response = client.post(
            "/api/projects",
            json={"site_url": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "project_id" in data
        assert "status" in data
        assert isinstance(data["project_id"], str)
        assert data["status"] == "created"
        
        # Project ID should be a valid UUID format
        import uuid
        try:
            uuid.UUID(data["project_id"])
        except ValueError:
            pytest.fail("project_id is not a valid UUID")

# Integration test for the full flow
def test_full_project_creation_flow():
    """Test the complete flow of creating and retrieving a project"""
    # Create project
    create_data = {
        "site_url": "example.com",
        "business_category": "saas"
    }
    
    create_response = client.post("/api/projects", json=create_data)
    assert create_response.status_code == 200
    
    project_data = create_response.json()
    project_id = project_data["project_id"]
    
    # Retrieve project
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    
    retrieved_data = get_response.json()
    assert retrieved_data["project_id"] == project_id
    assert retrieved_data["site_url"] == "https://example.com"  # Should have protocol added
    assert retrieved_data["business_category"] == "saas"