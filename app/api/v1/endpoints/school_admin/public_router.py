from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging # Loglama için eklendi

# crud, schemas, get_db gibi gerekli importları app seviyesinden yapalım
from app import crud, models, schemas # models eklendi, lazım olabilir diye
from app.dependencies import get_db

logger = logging.getLogger(__name__)
router = APIRouter(
    tags=["public"],
    responses={404: {"description": "Not found"}},
)

# schools.py\'den buraya taşınan endpoint
@router.get("/schools/{school_id}/classes/", response_model=List[schemas.Class])
def public_read_school_classes_no_auth( # Fonksiyon adını değiştirelim çakışmasın diye
    school_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all classes for a specific school. This endpoint is public and requires no authentication.
    """
    db_school = crud.get_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found for public class listing")
    
    classes = crud.get_classes(db=db, school_id=school_id, skip=skip, limit=limit)
    return classes

# Buraya başka public endpointler de eklenebilir (örn: okul kodu doğrulama)
# Örneğin, get_school_by_unique_code endpoint'ini de buraya taşıyabiliriz.

@router.get("/schools/by_code/{unique_code}", response_model=schemas.School)
def public_get_school_by_unique_code_no_auth(
    unique_code: str,
    db: Session = Depends(get_db)
):
    """Fetch a school by its unique_code. Public access."""
    logger.debug(f"Attempting to find school with unique_code: {unique_code}") # print yerine logger.debug
    db_school = crud.get_school_by_unique_code(db, unique_code=unique_code)
    if db_school is None:
        logger.warning(f"School with unique_code '{unique_code}' NOT FOUND in DB.") # print yerine logger.warning
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with unique code '{unique_code}' not found for public access.")
    logger.debug(f"School FOUND: {db_school.name if db_school else 'N/A'}") # print yerine logger.debug
    return db_school 