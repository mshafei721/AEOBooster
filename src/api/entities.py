"""
API endpoints for entity extraction and management.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import asyncio

from ..models.database import get_db
from ..models.project import Project
from ..services.entity_service import EntityService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entities", tags=["entities"])

# Pydantic models for request/response
class EntityExtractionRequest(BaseModel):
    """Request model for entity extraction."""
    min_confidence: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    force_reextract: Optional[bool] = Field(default=False)

class EntityExtractionResponse(BaseModel):
    """Response model for entity extraction initiation."""
    job_id: str
    status: str
    message: str

class EntityExtractionStatus(BaseModel):
    """Response model for extraction status."""
    status: str
    entities_found: Optional[int] = None
    pages_processed: Optional[int] = None
    successful_pages: Optional[int] = None
    failed_pages: Optional[int] = None
    error: Optional[str] = None

class EntityResponse(BaseModel):
    """Response model for individual entity."""
    id: str
    type: str
    value: str
    confidence_score: float
    frequency: int
    context: Optional[str] = None
    extraction_method: str
    created_at: str

class EntitiesListResponse(BaseModel):
    """Response model for entities list."""
    entities: List[EntityResponse]
    total: int
    limit: int
    offset: int
    stats: Dict[str, Any]

# Global job storage (in production, use Redis or database)
extraction_jobs: Dict[str, Dict] = {}

def get_entity_service():
    """Dependency to get entity service."""
    return EntityService()

@router.post("/projects/{project_id}/extract", response_model=EntityExtractionResponse)
async def extract_entities(
    project_id: str,
    request: EntityExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    entity_service: EntityService = Depends(get_entity_service)
):
    """
    Initiate entity extraction for a project.
    
    Args:
        project_id: Project identifier
        request: Extraction parameters
        background_tasks: FastAPI background tasks
        db: Database session
        entity_service: Entity service dependency
        
    Returns:
        Extraction job information
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if extraction is already in progress
        active_job = None
        for job_id, job_data in extraction_jobs.items():
            if (job_data.get("project_id") == project_id and 
                job_data.get("status") in ["pending", "running"]):
                active_job = job_id
                break
        
        if active_job and not request.force_reextract:
            return EntityExtractionResponse(
                job_id=active_job,
                status="already_running",
                message="Entity extraction already in progress for this project"
            )
        
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        extraction_jobs[job_id] = {
            "project_id": project_id,
            "status": "pending",
            "min_confidence": request.min_confidence,
            "entities_found": 0,
            "pages_processed": 0,
            "successful_pages": 0,
            "failed_pages": 0,
            "error": None
        }
        
        # Start extraction in background
        background_tasks.add_task(
            run_entity_extraction,
            job_id,
            project_id,
            request.min_confidence,
            entity_service
        )
        
        return EntityExtractionResponse(
            job_id=job_id,
            status="started",
            message="Entity extraction initiated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate entity extraction for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate entity extraction")

async def run_entity_extraction(
    job_id: str,
    project_id: str, 
    min_confidence: float,
    entity_service: EntityService
):
    """
    Run entity extraction in background.
    
    Args:
        job_id: Job identifier
        project_id: Project identifier
        min_confidence: Minimum confidence threshold
        entity_service: Entity service instance
    """
    try:
        # Update job status
        extraction_jobs[job_id]["status"] = "running"
        
        # Run extraction
        result = await entity_service.extract_and_store_entities(
            project_id, min_confidence
        )
        
        # Update job with results
        extraction_jobs[job_id].update({
            "status": "completed" if result["status"] == "completed" else "failed",
            "entities_found": result.get("entities_extracted", 0),
            "pages_processed": result.get("pages_processed", 0),
            "successful_pages": result.get("successful_pages", 0),
            "failed_pages": result.get("failed_pages", 0),
            "error": None if result["status"] == "completed" else result.get("message", "Unknown error")
        })
        
        logger.info(f"Entity extraction completed for project {project_id}: {result['entities_extracted']} entities")
        
    except Exception as e:
        # Update job with error
        extraction_jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })
        logger.error(f"Entity extraction failed for project {project_id}: {e}")

@router.get("/projects/{project_id}/extract/status", response_model=EntityExtractionStatus)
async def get_extraction_status(
    project_id: str,
    job_id: Optional[str] = Query(None, description="Specific job ID to check"),
    db: Session = Depends(get_db)
):
    """
    Get entity extraction status for a project.
    
    Args:
        project_id: Project identifier
        job_id: Optional specific job ID
        db: Database session
        
    Returns:
        Extraction status information
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Find relevant job
        target_job = None
        if job_id:
            target_job = extraction_jobs.get(job_id)
            if not target_job or target_job.get("project_id") != project_id:
                raise HTTPException(status_code=404, detail="Job not found")
        else:
            # Find latest job for project
            for jid, job_data in extraction_jobs.items():
                if job_data.get("project_id") == project_id:
                    if target_job is None or job_data.get("created_at", 0) > target_job.get("created_at", 0):
                        target_job = job_data
        
        if not target_job:
            raise HTTPException(status_code=404, detail="No extraction jobs found for project")
        
        return EntityExtractionStatus(
            status=target_job["status"],
            entities_found=target_job.get("entities_found"),
            pages_processed=target_job.get("pages_processed"),
            successful_pages=target_job.get("successful_pages"),
            failed_pages=target_job.get("failed_pages"),
            error=target_job.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get extraction status for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get extraction status")

@router.get("/projects/{project_id}", response_model=EntitiesListResponse)
async def get_entities(
    project_id: str,
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    min_confidence: Optional[float] = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    entity_service: EntityService = Depends(get_entity_service)
):
    """
    Get extracted entities for a project.
    
    Args:
        project_id: Project identifier
        entity_type: Optional entity type filter
        min_confidence: Minimum confidence filter
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        entity_service: Entity service dependency
        
    Returns:
        List of entities with metadata
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get entities from service
        result = entity_service.get_entities_for_project(
            project_id=project_id,
            entity_type=entity_type,
            min_confidence=min_confidence,
            limit=limit,
            offset=offset,
            db=db
        )
        
        # Convert to response format
        entities = [EntityResponse(**entity) for entity in result["entities"]]
        
        return EntitiesListResponse(
            entities=entities,
            total=result["total"],
            limit=result["limit"], 
            offset=result["offset"],
            stats=result["stats"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entities for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get entities")

@router.get("/projects/{project_id}/stats")
async def get_entity_stats(
    project_id: str,
    db: Session = Depends(get_db),
    entity_service: EntityService = Depends(get_entity_service)
):
    """
    Get entity statistics for a project.
    
    Args:
        project_id: Project identifier
        db: Database session
        entity_service: Entity service dependency
        
    Returns:
        Entity statistics
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get basic stats
        result = entity_service.get_entities_for_project(
            project_id=project_id,
            limit=1,  # We only need stats
            db=db
        )
        
        return {
            "project_id": project_id,
            "total_entities": result["total"],
            "by_type": result["stats"],
            "confidence_distribution": {
                "high_confidence": entity_service.get_entities_for_project(
                    project_id, min_confidence=0.8, limit=1, db=db
                )["total"],
                "medium_confidence": entity_service.get_entities_for_project(
                    project_id, min_confidence=0.5, limit=1, db=db
                )["total"],
                "low_confidence": entity_service.get_entities_for_project(
                    project_id, min_confidence=0.0, limit=1, db=db
                )["total"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity stats for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get entity statistics")

@router.delete("/projects/{project_id}")
async def delete_entities(
    project_id: str,
    db: Session = Depends(get_db),
    entity_service: EntityService = Depends(get_entity_service)
):
    """
    Delete all entities for a project.
    
    Args:
        project_id: Project identifier
        db: Database session
        entity_service: Entity service dependency
        
    Returns:
        Deletion confirmation
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete entities
        entity_service.delete_entities_for_project(project_id, db)
        
        return {"message": f"All entities deleted for project {project_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete entities for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete entities")