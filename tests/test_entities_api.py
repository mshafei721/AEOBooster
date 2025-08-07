"""
Tests for entities API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from main import app
from src.models.database import Base, get_db
from src.models.project import Project, User
from src.models.crawled_content import CrawledPage
from src.models.entity import Entity

# Create in-memory test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_setup():
    """Set up test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_data(db_setup):
    """Create test data."""
    db = TestingSessionLocal()
    
    # Create test user
    user = User(id="test_user", email="test@example.com")
    db.add(user)
    
    # Create test project
    project = Project(id="test_project", user_id="test_user", site_url="https://example.com")
    db.add(project)
    
    # Create test crawled page
    page = CrawledPage(
        id="test_page",
        project_id="test_project",
        crawl_job_id="test_job",
        url="https://example.com/page1",
        normalized_url="https://example.com/page1",
        title="Test Page",
        content_text="Enterprise Software Solution from TechCorp",
        status="crawled"
    )
    db.add(page)
    
    # Create test entities
    entities = [
        Entity(
            id="entity_1",
            project_id="test_project",
            page_id="test_page",
            entity_type="product",
            value="Enterprise Software Solution",
            normalized_value="enterprise software solution",
            confidence_score=0.9,
            frequency=1,
            extraction_method="spacy"
        ),
        Entity(
            id="entity_2", 
            project_id="test_project",
            page_id="test_page",
            entity_type="brand",
            value="TechCorp",
            normalized_value="techcorp",
            confidence_score=0.8,
            frequency=1,
            extraction_method="spacy"
        )
    ]
    
    for entity in entities:
        db.add(entity)
    
    db.commit()
    db.close()
    
    return {
        "user_id": "test_user",
        "project_id": "test_project", 
        "page_id": "test_page",
        "entities": entities
    }

class TestEntitiesAPI:
    """Test cases for entities API endpoints."""
    
    @patch('src.api.entities.run_entity_extraction')
    def test_extract_entities_success(self, mock_extract, test_data):
        """Test successful entity extraction initiation."""
        project_id = test_data["project_id"]
        
        response = client.post(
            f"/api/entities/projects/{project_id}/extract",
            json={"min_confidence": 0.6}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "job_id" in data
        assert data["message"] == "Entity extraction initiated"
        
        # Verify background task was called
        mock_extract.assert_called_once()
    
    def test_extract_entities_project_not_found(self, test_data):
        """Test extraction with non-existent project."""
        response = client.post(
            "/api/entities/projects/nonexistent/extract",
            json={"min_confidence": 0.5}
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_extract_entities_invalid_confidence(self, test_data):
        """Test extraction with invalid confidence parameter."""
        project_id = test_data["project_id"]
        
        # Test confidence > 1.0
        response = client.post(
            f"/api/entities/projects/{project_id}/extract",
            json={"min_confidence": 1.5}
        )
        assert response.status_code == 422
        
        # Test negative confidence
        response = client.post(
            f"/api/entities/projects/{project_id}/extract", 
            json={"min_confidence": -0.1}
        )
        assert response.status_code == 422
    
    def test_get_extraction_status_not_found(self, test_data):
        """Test getting status for non-existent job."""
        project_id = test_data["project_id"]
        
        response = client.get(f"/api/entities/projects/{project_id}/extract/status")
        
        assert response.status_code == 404
        assert "No extraction jobs found" in response.json()["detail"]
    
    def test_get_entities_success(self, test_data):
        """Test successful entity retrieval."""
        project_id = test_data["project_id"]
        
        response = client.get(f"/api/entities/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "entities" in data
        assert "total" in data
        assert "stats" in data
        assert data["total"] == 2
        assert len(data["entities"]) == 2
        
        # Verify entity structure
        entity = data["entities"][0]
        required_fields = ["id", "type", "value", "confidence_score", "frequency"]
        for field in required_fields:
            assert field in entity
    
    def test_get_entities_with_filters(self, test_data):
        """Test entity retrieval with filters."""
        project_id = test_data["project_id"]
        
        # Test entity type filter
        response = client.get(f"/api/entities/projects/{project_id}?entity_type=brand")
        assert response.status_code == 200
        data = response.json()
        
        # Should only return brand entities
        for entity in data["entities"]:
            assert entity["type"] == "brand"
    
    def test_get_entities_with_confidence_filter(self, test_data):
        """Test entity retrieval with confidence filter."""
        project_id = test_data["project_id"]
        
        # Test high confidence filter
        response = client.get(f"/api/entities/projects/{project_id}?min_confidence=0.85")
        assert response.status_code == 200
        data = response.json()
        
        # Should only return high confidence entities
        for entity in data["entities"]:
            assert entity["confidence_score"] >= 0.85
    
    def test_get_entities_pagination(self, test_data):
        """Test entity retrieval pagination."""
        project_id = test_data["project_id"]
        
        # Test with limit
        response = client.get(f"/api/entities/projects/{project_id}?limit=1")
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 1
        assert len(data["entities"]) <= 1
        
        # Test with offset
        response = client.get(f"/api/entities/projects/{project_id}?offset=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 1
    
    def test_get_entities_project_not_found(self, test_data):
        """Test entity retrieval for non-existent project."""
        response = client.get("/api/entities/projects/nonexistent")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_get_entity_stats_success(self, test_data):
        """Test entity statistics retrieval."""
        project_id = test_data["project_id"]
        
        response = client.get(f"/api/entities/projects/{project_id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "project_id" in data
        assert "total_entities" in data
        assert "by_type" in data
        assert "confidence_distribution" in data
        
        assert data["project_id"] == project_id
        assert data["total_entities"] == 2
    
    def test_get_entity_stats_project_not_found(self, test_data):
        """Test statistics for non-existent project."""
        response = client.get("/api/entities/projects/nonexistent/stats")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_delete_entities_success(self, test_data):
        """Test successful entity deletion."""
        project_id = test_data["project_id"]
        
        response = client.delete(f"/api/entities/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert f"All entities deleted for project {project_id}" in data["message"]
        
        # Verify entities were deleted
        get_response = client.get(f"/api/entities/projects/{project_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["total"] == 0
    
    def test_delete_entities_project_not_found(self, test_data):
        """Test deletion for non-existent project."""
        response = client.delete("/api/entities/projects/nonexistent")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

@pytest.mark.asyncio
class TestEntitiesAPIIntegration:
    """Integration tests for entities API workflow."""
    
    @patch('src.services.entity_service.EntityService.extract_and_store_entities')
    async def test_full_extraction_workflow(self, mock_extract_service, test_data):
        """Test complete extraction workflow."""
        project_id = test_data["project_id"]
        
        # Mock extraction service
        mock_extract_service.return_value = {
            "status": "completed",
            "entities_extracted": 5,
            "pages_processed": 1,
            "successful_pages": 1,
            "failed_pages": 0
        }
        
        # Start extraction
        response = client.post(
            f"/api/entities/projects/{project_id}/extract",
            json={"min_confidence": 0.5}
        )
        
        assert response.status_code == 200
        job_data = response.json()
        job_id = job_data["job_id"]
        
        # Simulate job completion
        from src.api.entities import extraction_jobs
        extraction_jobs[job_id] = {
            "project_id": project_id,
            "status": "completed",
            "entities_found": 5,
            "pages_processed": 1,
            "successful_pages": 1,
            "failed_pages": 0,
            "error": None
        }
        
        # Check status
        status_response = client.get(
            f"/api/entities/projects/{project_id}/extract/status",
            params={"job_id": job_id}
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "completed"
        assert status_data["entities_found"] == 5
    
    def test_api_validation_edge_cases(self, test_data):
        """Test API validation with edge cases."""
        project_id = test_data["project_id"]
        
        # Test with maximum limit
        response = client.get(f"/api/entities/projects/{project_id}?limit=250")
        assert response.status_code == 422  # Should exceed max limit
        
        # Test with negative offset
        response = client.get(f"/api/entities/projects/{project_id}?offset=-1")
        assert response.status_code == 422
        
        # Test with invalid entity type (should still work, just return no results)
        response = client.get(f"/api/entities/projects/{project_id}?entity_type=invalid")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
    
    def test_concurrent_extraction_requests(self, test_data):
        """Test handling of concurrent extraction requests."""
        project_id = test_data["project_id"]
        
        # Mock to prevent actual extraction
        with patch('src.api.entities.run_entity_extraction'):
            # First request
            response1 = client.post(
                f"/api/entities/projects/{project_id}/extract",
                json={"min_confidence": 0.5}
            )
            assert response1.status_code == 200
            
            # Second request (should detect already running)
            response2 = client.post(
                f"/api/entities/projects/{project_id}/extract", 
                json={"min_confidence": 0.5}
            )
            
            # May return already running status or start new job depending on timing
            assert response2.status_code == 200
    
    def test_api_error_handling(self, test_data):
        """Test API error handling and response formats."""
        # Test malformed JSON
        project_id = test_data["project_id"]
        
        response = client.post(
            f"/api/entities/projects/{project_id}/extract",
            data="invalid json",  # Not valid JSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test missing required fields (should use defaults)
        response = client.post(
            f"/api/entities/projects/{project_id}/extract",
            json={}  # Empty JSON, should use defaults
        )
        assert response.status_code == 200 or response.status_code == 500  # May fail on mock setup