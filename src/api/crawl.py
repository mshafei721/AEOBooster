"""
API endpoints for website crawling functionality.
"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field

from ..models.database import get_db, SessionLocal
from ..models.project import Project
from ..models.crawled_content import CrawlJob, CrawledPage
from ..services.crawler_service import CrawlerService

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models
class CrawlRequest(BaseModel):
    """Request model for starting a crawl."""
    max_pages: int = Field(default=50, ge=1, le=500, description="Maximum pages to crawl")
    delay_seconds: float = Field(default=1.0, ge=0.1, le=10.0, description="Delay between requests")
    timeout_seconds: int = Field(default=30, ge=10, le=120, description="Request timeout")
    respect_robots: bool = Field(default=True, description="Whether to respect robots.txt")

class CrawlResponse(BaseModel):
    """Response model for crawl initiation."""
    job_id: str
    status: str
    message: str
    project_id: str

class CrawlStatusResponse(BaseModel):
    """Response model for crawl status."""
    job_id: str
    project_id: str
    status: str
    base_url: str
    pages_crawled: int
    pages_failed: int
    total_pages_found: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    current_progress: Optional[str]

class CrawledPageResponse(BaseModel):
    """Response model for individual crawled page."""
    id: str
    url: str
    title: Optional[str]
    page_type: Optional[str]
    confidence_score: Optional[float]
    status: str
    crawled_at: Optional[datetime]
    word_count: Optional[int]
    reading_time_minutes: Optional[float]

class ProjectContentResponse(BaseModel):
    """Response model for project's crawled content."""
    project_id: str
    total_pages: int
    pages_by_type: Dict[str, int]
    recent_crawl_job: Optional[str]
    pages: list[CrawledPageResponse]

# Global dictionary to track active crawl jobs for progress updates
active_crawl_jobs: Dict[str, Dict] = {}

@router.post("/projects/{project_id}/crawl", response_model=CrawlResponse)
async def start_crawl(
    project_id: str,
    crawl_request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start crawling a project's website.
    
    Args:
        project_id: ID of the project to crawl
        crawl_request: Crawling configuration
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        CrawlResponse with job information
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if there's already a running crawl for this project
    existing_job = db.query(CrawlJob).filter(
        CrawlJob.project_id == project_id,
        CrawlJob.status.in_(["pending", "running"])
    ).first()
    
    if existing_job:
        raise HTTPException(
            status_code=409, 
            detail=f"A crawl job is already running for this project: {existing_job.id}"
        )
    
    try:
        # Create crawl job record
        crawl_job = CrawlJob(
            project_id=project_id,
            status="pending",
            base_url=project.site_url,
            max_pages=crawl_request.max_pages,
            delay_seconds=crawl_request.delay_seconds,
            timeout_seconds=crawl_request.timeout_seconds,
            respect_robots="true" if crawl_request.respect_robots else "false"
        )
        
        db.add(crawl_job)
        db.commit()
        db.refresh(crawl_job)
        
        # Initialize progress tracking
        active_crawl_jobs[crawl_job.id] = {
            'status': 'pending',
            'current_url': '',
            'pages_crawled': 0,
            'pages_found': 0,
            'error': None
        }
        
        # Start crawling in background
        background_tasks.add_task(
            run_crawl_job, 
            crawl_job.id, 
            project.site_url,
            crawl_request.dict()
        )
        
        logger.info(f"Started crawl job {crawl_job.id} for project {project_id}")
        
        return CrawlResponse(
            job_id=crawl_job.id,
            status="started",
            message="Crawl job started successfully",
            project_id=project_id
        )
        
    except Exception as e:
        logger.error(f"Error starting crawl for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start crawl: {str(e)}")

@router.get("/projects/{project_id}/crawl/status", response_model=CrawlStatusResponse)
async def get_crawl_status(project_id: str, db: Session = Depends(get_db)):
    """
    Get the status of the most recent crawl job for a project.
    
    Args:
        project_id: ID of the project
        db: Database session
        
    Returns:
        CrawlStatusResponse with current status
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get most recent crawl job
    crawl_job = db.query(CrawlJob).filter(
        CrawlJob.project_id == project_id
    ).order_by(CrawlJob.created_at.desc()).first()
    
    if not crawl_job:
        raise HTTPException(status_code=404, detail="No crawl jobs found for this project")
    
    # Get current progress if job is active
    current_progress = None
    if crawl_job.id in active_crawl_jobs:
        progress = active_crawl_jobs[crawl_job.id]
        if progress['current_url']:
            current_progress = f"Currently crawling: {progress['current_url']}"
    
    return CrawlStatusResponse(
        job_id=crawl_job.id,
        project_id=project_id,
        status=crawl_job.status,
        base_url=crawl_job.base_url,
        pages_crawled=crawl_job.pages_crawled,
        pages_failed=crawl_job.pages_failed,
        total_pages_found=crawl_job.total_pages_found,
        started_at=crawl_job.started_at,
        completed_at=crawl_job.completed_at,
        error_message=crawl_job.error_message,
        current_progress=current_progress
    )

@router.get("/projects/{project_id}/content", response_model=ProjectContentResponse)
async def get_project_content(project_id: str, 
                            page_type: Optional[str] = None,
                            limit: int = 50,
                            offset: int = 0,
                            db: Session = Depends(get_db)):
    """
    Get crawled content for a project.
    
    Args:
        project_id: ID of the project
        page_type: Filter by page type (optional)
        limit: Maximum number of pages to return
        offset: Number of pages to skip
        db: Database session
        
    Returns:
        ProjectContentResponse with crawled content
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Build query for crawled pages
    query = db.query(CrawledPage).filter(
        CrawledPage.project_id == project_id,
        CrawledPage.status == "crawled"
    )
    
    if page_type:
        query = query.filter(CrawledPage.page_type == page_type)
    
    # Get total count
    total_pages = query.count()
    
    # Get pages with pagination
    pages = query.order_by(CrawledPage.crawled_at.desc()).offset(offset).limit(limit).all()
    
    # Calculate pages by type
    pages_by_type = {}
    type_counts = db.query(
        CrawledPage.page_type, 
        db.func.count(CrawledPage.id)
    ).filter(
        CrawledPage.project_id == project_id,
        CrawledPage.status == "crawled"
    ).group_by(CrawledPage.page_type).all()
    
    for page_type, count in type_counts:
        pages_by_type[page_type or 'unknown'] = count
    
    # Get most recent crawl job
    recent_crawl = db.query(CrawlJob).filter(
        CrawlJob.project_id == project_id
    ).order_by(CrawlJob.created_at.desc()).first()
    
    # Convert pages to response format
    page_responses = []
    for page in pages:
        # Extract metrics from content_metrics JSON
        word_count = None
        reading_time = None
        if page.content_metrics:
            word_count = page.content_metrics.get('word_count')
            reading_time = page.content_metrics.get('reading_time_minutes')
        
        page_responses.append(CrawledPageResponse(
            id=page.id,
            url=page.url,
            title=page.title,
            page_type=page.page_type,
            confidence_score=page.confidence_score,
            status=page.status,
            crawled_at=page.crawled_at,
            word_count=word_count,
            reading_time_minutes=reading_time
        ))
    
    return ProjectContentResponse(
        project_id=project_id,
        total_pages=total_pages,
        pages_by_type=pages_by_type,
        recent_crawl_job=recent_crawl.id if recent_crawl else None,
        pages=page_responses
    )

async def run_crawl_job(job_id: str, base_url: str, crawl_config: Dict):
    """
    Background task to run the actual crawling.
    
    Args:
        job_id: ID of the crawl job
        base_url: Base URL to crawl
        crawl_config: Crawling configuration
    """
    db = SessionLocal()
    
    try:
        # Get crawl job
        crawl_job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not crawl_job:
            logger.error(f"Crawl job {job_id} not found")
            return
        
        # Update job status to running
        crawl_job.status = "running"
        crawl_job.started_at = datetime.now(UTC)
        db.commit()
        
        # Progress callback function
        async def progress_callback(progress: Dict):
            # Update in-memory progress
            if job_id in active_crawl_jobs:
                active_crawl_jobs[job_id].update(progress)
            
            # Update database periodically
            crawl_job.pages_crawled = progress.get('pages_crawled', 0)
            crawl_job.total_pages_found = progress.get('pages_found', 0)
            db.commit()
        
        # Initialize crawler
        crawler = CrawlerService(
            max_pages=crawl_config['max_pages'],
            delay_seconds=crawl_config['delay_seconds'],
            timeout_seconds=crawl_config['timeout_seconds'],
            respect_robots=crawl_config['respect_robots']
        )
        
        # Start crawling
        results = await crawler.crawl_website(
            project_id=crawl_job.project_id,
            base_url=base_url,
            progress_callback=progress_callback
        )
        
        # Save crawled pages to database
        for page_data in results['crawled_pages']:
            crawled_page = CrawledPage(
                crawl_job_id=job_id,
                project_id=crawl_job.project_id,
                url=page_data['url'],
                normalized_url=crawler.normalize_url(page_data['url']),
                title=page_data.get('title', ''),
                page_type=page_data.get('page_type'),
                confidence_score=page_data.get('confidence_score'),
                status="crawled",
                crawled_at=datetime.fromtimestamp(page_data['crawled_at'], UTC),
                content_text=page_data['content'].get('content', ''),
                headings=page_data['content'].get('headings', []),
                images=page_data['content'].get('images', []),
                links=page_data['content'].get('links', []),
                structured_data=page_data['content'].get('structured_data', {}),
                open_graph=page_data['content'].get('open_graph', {}),
                twitter_card=page_data['content'].get('twitter_card', {}),
                content_metrics=page_data['content'].get('content_metrics', {}),
                extraction_method=page_data.get('extraction_method', 'playwright')
            )
            db.add(crawled_page)
        
        # Save failed pages
        for failed_page in results['failed_pages']:
            crawled_page = CrawledPage(
                crawl_job_id=job_id,
                project_id=crawl_job.project_id,
                url=failed_page['url'],
                normalized_url=crawler.normalize_url(failed_page['url']),
                status="failed",
                error_message=failed_page.get('error', 'Unknown error'),
                crawled_at=datetime.fromtimestamp(failed_page['failed_at'], UTC)
            )
            db.add(crawled_page)
        
        # Update crawl job with final results
        crawl_job.status = "completed"
        crawl_job.completed_at = datetime.now(UTC)
        crawl_job.pages_crawled = results['pages_crawled']
        crawl_job.pages_failed = results['pages_failed']
        crawl_job.total_pages_found = results['total_pages_found']
        
        db.commit()
        
        logger.info(f"Crawl job {job_id} completed successfully. "
                   f"Pages crawled: {results['pages_crawled']}, "
                   f"Failed: {results['pages_failed']}")
        
    except Exception as e:
        logger.error(f"Crawl job {job_id} failed: {e}")
        
        # Update job status to failed
        crawl_job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if crawl_job:
            crawl_job.status = "failed"
            crawl_job.completed_at = datetime.now(UTC)
            crawl_job.error_message = str(e)
            db.commit()
    
    finally:
        # Clean up progress tracking
        if job_id in active_crawl_jobs:
            del active_crawl_jobs[job_id]
        
        db.close()

