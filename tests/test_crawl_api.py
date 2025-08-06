"""
Integration tests for crawl API endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, UTC

from main import app
from src.models.database import SessionLocal, Base, engine
from src.models.project import User, Project
from src.models.crawled_content import CrawlJob, CrawledPage

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    """Create a test database session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create test user
        test_user = User(
            id="test-user-id",
            email="test@example.com"
        )
        db.add(test_user)
        
        # Create test project
        test_project = Project(
            id="test-project-id",
            user_id="test-user-id",
            site_url="https://example.com",
            business_category="Technology"
        )
        db.add(test_project)
        
        db.commit()
        yield db
    finally:
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=engine)

class TestCrawlAPI:
    """Test suite for crawl API endpoints."""
    
    def test_start_crawl_success(self, test_db):
        """Test successful crawl initiation."""
        project_id = "test-project-id"
        
        # Mock the background task
        with patch('src.api.crawl.run_crawl_job', new_callable=AsyncMock) as mock_crawl:
            response = client.post(
                f"/api/projects/{project_id}/crawl",
                json={
                    "max_pages": 10,
                    "delay_seconds": 1.0,
                    "timeout_seconds": 30,
                    "respect_robots": True
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "started"
        assert data["project_id"] == project_id
        assert "job_id" in data
        
        # Verify crawl job was created in database
        db = SessionLocal()
        try:
            crawl_job = db.query(CrawlJob).filter(CrawlJob.id == data["job_id"]).first()
            assert crawl_job is not None
            assert crawl_job.project_id == project_id
            assert crawl_job.status == "pending"
            assert crawl_job.max_pages == 10
        finally:
            db.close()
    
    def test_start_crawl_project_not_found(self, test_db):
        """Test crawl initiation with non-existent project."""
        response = client.post(
            "/api/projects/non-existent-project/crawl",
            json={"max_pages": 10}
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_start_crawl_already_running(self, test_db):
        """Test crawl initiation when another crawl is already running."""
        project_id = "test-project-id"
        
        # Create existing running crawl job
        db = SessionLocal()
        try:
            existing_job = CrawlJob(
                project_id=project_id,
                status="running",
                base_url="https://example.com"
            )
            db.add(existing_job)
            db.commit()
        finally:
            db.close()
        
        response = client.post(
            f"/api/projects/{project_id}/crawl",
            json={"max_pages": 10}
        )
        
        assert response.status_code == 409
        assert "already running" in response.json()["detail"]
    
    def test_get_crawl_status_success(self, test_db):
        """Test getting crawl status."""
        project_id = "test-project-id"
        
        # Create crawl job
        db = SessionLocal()
        try:
            crawl_job = CrawlJob(
                id="test-job-id",
                project_id=project_id,
                status="completed",
                base_url="https://example.com",
                pages_crawled=5,
                pages_failed=1,
                total_pages_found=6,
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC)
            )
            db.add(crawl_job)
            db.commit()
        finally:
            db.close()
        
        response = client.get(f"/api/projects/{project_id}/crawl/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == "test-job-id"
        assert data["project_id"] == project_id
        assert data["status"] == "completed"
        assert data["pages_crawled"] == 5
        assert data["pages_failed"] == 1
        assert data["total_pages_found"] == 6
    
    def test_get_crawl_status_no_jobs(self, test_db):
        """Test getting crawl status when no jobs exist."""
        project_id = "test-project-id"
        
        response = client.get(f"/api/projects/{project_id}/crawl/status")
        
        assert response.status_code == 404
        assert "No crawl jobs found" in response.json()["detail"]
    
    def test_get_project_content_success(self, test_db):
        """Test getting project's crawled content."""
        project_id = "test-project-id"
        
        # Create crawl job and pages
        db = SessionLocal()
        try:
            crawl_job = CrawlJob(
                id="test-job-id",
                project_id=project_id,
                status="completed",
                base_url="https://example.com"
            )
            db.add(crawl_job)
            
            # Create crawled pages
            pages = [
                CrawledPage(
                    id="page-1",
                    crawl_job_id="test-job-id",
                    project_id=project_id,
                    url="https://example.com",
                    normalized_url="https://example.com",
                    title="Homepage",
                    page_type="homepage",
                    confidence_score=0.9,
                    status="crawled",
                    content_metrics={"word_count": 250, "reading_time_minutes": 1.25},
                    crawled_at=datetime.now(UTC)
                ),
                CrawledPage(
                    id="page-2",
                    crawl_job_id="test-job-id",
                    project_id=project_id,
                    url="https://example.com/about",
                    normalized_url="https://example.com/about",
                    title="About Us",
                    page_type="about",
                    confidence_score=0.8,
                    status="crawled",
                    content_metrics={"word_count": 400, "reading_time_minutes": 2.0},
                    crawled_at=datetime.now(UTC)
                )
            ]
            
            for page in pages:
                db.add(page)
            
            db.commit()
        finally:
            db.close()
        
        response = client.get(f"/api/projects/{project_id}/content")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["project_id"] == project_id
        assert data["total_pages"] == 2
        assert len(data["pages"]) == 2
        assert data["recent_crawl_job"] == "test-job-id"
        
        # Check page type counts
        assert data["pages_by_type"]["homepage"] == 1
        assert data["pages_by_type"]["about"] == 1
        
        # Check individual pages
        page1 = data["pages"][0]  # Should be ordered by crawled_at desc
        assert page1["url"] in ["https://example.com", "https://example.com/about"]
        assert page1["status"] == "crawled"
        assert "word_count" in page1
        assert "reading_time_minutes" in page1
    
    def test_get_project_content_filtered_by_type(self, test_db):
        """Test getting project content filtered by page type."""
        project_id = "test-project-id"
        
        # Create crawled pages of different types
        db = SessionLocal()
        try:
            crawl_job = CrawlJob(
                id="test-job-id",
                project_id=project_id,
                status="completed",
                base_url="https://example.com"
            )
            db.add(crawl_job)
            
            pages = [
                CrawledPage(
                    crawl_job_id="test-job-id",
                    project_id=project_id,
                    url="https://example.com/product1",
                    normalized_url="https://example.com/product1",
                    title="Product 1",
                    page_type="product",
                    status="crawled",
                    crawled_at=datetime.now(UTC)
                ),
                CrawledPage(
                    crawl_job_id="test-job-id",
                    project_id=project_id,
                    url="https://example.com/about",
                    normalized_url="https://example.com/about",
                    title="About",
                    page_type="about",
                    status="crawled",
                    crawled_at=datetime.now(UTC)
                )
            ]
            
            for page in pages:
                db.add(page)
            
            db.commit()
        finally:
            db.close()
        
        # Filter by product type
        response = client.get(f"/api/projects/{project_id}/content?page_type=product")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_pages"] == 1
        assert len(data["pages"]) == 1
        assert data["pages"][0]["page_type"] == "product"
    
    def test_get_project_content_pagination(self, test_db):
        """Test pagination in project content endpoint."""
        project_id = "test-project-id"
        
        # Create multiple crawled pages
        db = SessionLocal()
        try:
            crawl_job = CrawlJob(
                id="test-job-id",
                project_id=project_id,
                status="completed",
                base_url="https://example.com"
            )
            db.add(crawl_job)
            
            # Create 5 pages
            for i in range(5):
                page = CrawledPage(
                    crawl_job_id="test-job-id",
                    project_id=project_id,
                    url=f"https://example.com/page{i}",
                    normalized_url=f"https://example.com/page{i}",
                    title=f"Page {i}",
                    page_type="unknown",
                    status="crawled",
                    crawled_at=datetime.now(UTC)
                )
                db.add(page)
            
            db.commit()
        finally:
            db.close()
        
        # Get first 2 pages
        response = client.get(f"/api/projects/{project_id}/content?limit=2&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_pages"] == 5
        assert len(data["pages"]) == 2
        
        # Get next 2 pages
        response = client.get(f"/api/projects/{project_id}/content?limit=2&offset=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_pages"] == 5
        assert len(data["pages"]) == 2
    
    def test_crawl_request_validation(self, test_db):
        """Test request validation for crawl endpoints."""
        project_id = "test-project-id"
        
        # Test invalid max_pages (too high)
        response = client.post(
            f"/api/projects/{project_id}/crawl",
            json={"max_pages": 1000}  # Above limit
        )
        assert response.status_code == 422  # Validation error
        
        # Test invalid delay_seconds (too low)
        response = client.post(
            f"/api/projects/{project_id}/crawl",
            json={"delay_seconds": 0.01}  # Below minimum
        )
        assert response.status_code == 422
        
        # Test invalid timeout_seconds (too high)
        response = client.post(
            f"/api/projects/{project_id}/crawl",
            json={"timeout_seconds": 300}  # Above limit
        )
        assert response.status_code == 422

class TestCrawlBackgroundTask:
    """Test the background crawl task."""
    
    @pytest.mark.asyncio
    async def test_run_crawl_job_success(self):
        """Test successful background crawl job execution."""
        # Create test database
        Base.metadata.create_all(bind=engine)
        
        try:
            db = SessionLocal()
            
            # Create test data
            test_user = User(id="test-user", email="test@example.com")
            db.add(test_user)
            
            test_project = Project(
                id="test-project",
                user_id="test-user",
                site_url="https://example.com"
            )
            db.add(test_project)
            
            test_job = CrawlJob(
                id="test-job",
                project_id="test-project",
                status="pending",
                base_url="https://example.com"
            )
            db.add(test_job)
            
            db.commit()
            db.close()
            
            # Mock crawler results
            mock_results = {
                'pages_crawled': 2,
                'pages_failed': 0,
                'total_pages_found': 2,
                'crawled_pages': [
                    {
                        'url': 'https://example.com',
                        'title': 'Home',
                        'page_type': 'homepage',
                        'confidence_score': 0.9,
                        'content': {
                            'content': 'Home content',
                            'headings': [],
                            'images': [],
                            'links': [],
                            'structured_data': {},
                            'open_graph': {},
                            'twitter_card': {},
                            'content_metrics': {'word_count': 10}
                        },
                        'status': 'crawled',
                        'crawled_at': 1234567890.0
                    }
                ],
                'failed_pages': []
            }
            
            # Mock CrawlerService
            with patch('src.api.crawl.CrawlerService') as mock_crawler_class:
                mock_crawler = Mock()
                mock_crawler.crawl_website = AsyncMock(return_value=mock_results)
                mock_crawler.normalize_url = Mock(return_value="https://example.com")
                mock_crawler_class.return_value = mock_crawler
                
                # Import and run the background task
                from src.api.crawl import run_crawl_job
                
                await run_crawl_job(
                    job_id="test-job",
                    base_url="https://example.com",
                    crawl_config={
                        'max_pages': 10,
                        'delay_seconds': 1.0,
                        'timeout_seconds': 30,
                        'respect_robots': True
                    }
                )
            
            # Verify job completion
            db = SessionLocal()
            try:
                completed_job = db.query(CrawlJob).filter(CrawlJob.id == "test-job").first()
                assert completed_job.status == "completed"
                assert completed_job.pages_crawled == 2
                assert completed_job.pages_failed == 0
                
                # Verify page was saved
                saved_pages = db.query(CrawledPage).filter(CrawledPage.crawl_job_id == "test-job").all()
                assert len(saved_pages) == 1
                assert saved_pages[0].title == "Home"
                assert saved_pages[0].page_type == "homepage"
            finally:
                db.close()
        
        finally:
            Base.metadata.drop_all(bind=engine)
    
    @pytest.mark.asyncio
    async def test_run_crawl_job_failure(self):
        """Test background crawl job failure handling."""
        Base.metadata.create_all(bind=engine)
        
        try:
            db = SessionLocal()
            
            # Create test data
            test_user = User(id="test-user", email="test@example.com")
            db.add(test_user)
            
            test_project = Project(
                id="test-project",
                user_id="test-user",
                site_url="https://example.com"
            )
            db.add(test_project)
            
            test_job = CrawlJob(
                id="test-job",
                project_id="test-project",
                status="pending",
                base_url="https://example.com"
            )
            db.add(test_job)
            
            db.commit()
            db.close()
            
            # Mock CrawlerService to raise exception
            with patch('src.api.crawl.CrawlerService') as mock_crawler_class:
                mock_crawler = Mock()
                mock_crawler.crawl_website = AsyncMock(side_effect=Exception("Crawl failed"))
                mock_crawler_class.return_value = mock_crawler
                
                from src.api.crawl import run_crawl_job
                
                await run_crawl_job(
                    job_id="test-job",
                    base_url="https://example.com",
                    crawl_config={'max_pages': 10, 'delay_seconds': 1.0, 'timeout_seconds': 30, 'respect_robots': True}
                )
            
            # Verify job failure
            db = SessionLocal()
            try:
                failed_job = db.query(CrawlJob).filter(CrawlJob.id == "test-job").first()
                assert failed_job.status == "failed"
                assert "Crawl failed" in failed_job.error_message
            finally:
                db.close()
        
        finally:
            Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    pytest.main([__file__])