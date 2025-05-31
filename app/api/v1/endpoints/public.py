from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app import crud, schemas
from app.db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/schools/", response_model=List[schemas.School])
def read_public_schools(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all schools. Public endpoint, no authentication required.
    """
    schools = crud.school.get_multi(db, skip=skip, limit=limit)
    return schools

@router.get("/schools/{school_id}", response_model=schemas.School)
def read_public_school(
    school_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific school by ID. Public endpoint, no authentication required.
    """
    school = crud.school.get(db, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.get("/schools/by_code/{unique_code}", response_model=schemas.School)
def get_school_by_unique_code(
    unique_code: str,
    db: Session = Depends(get_db),
):
    """
    Get school by unique code (public endpoint - no authentication required).
    """
    logger.debug(f"Looking for school with unique_code: '{unique_code}'")
    school = crud.school.get_by_unique_code(db, unique_code=unique_code)
    if not school:
        logger.warning(f"School not found with unique_code '{unique_code}', raising 404")
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.get("/schools/{school_id}/classes/", response_model=List[schemas.Class])
def read_public_school_classes(
    school_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all classes for a specific school. Public endpoint, no authentication required.
    """
    school = crud.school.get(db, id=school_id) # Okulun varlığını kontrol et
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    
    classes = crud.class_.get_multi_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return classes 