import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app import schemas
from app.crud import crud_school, crud_class, crud
from app.db.database import get_db
from app.api import deps

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/by_code/{unique_code}", response_model=schemas.School)
def get_school_by_unique_code(
    unique_code: str,
    db: Session = Depends(get_db),
):
    """
    Get school by unique code (public endpoint - no authentication required).
    """
    logger.debug(f"Looking for school with unique_code: '{unique_code}'")
    school = crud_school.get_school_by_unique_code(db, unique_code=unique_code)
    logger.debug(f"School found from crud: {school is not None}")
    if school:
        logger.debug(f"School details: id={school.id}, name='{school.name}', unique_code='{school.unique_code}'")
    if not school:
        logger.warning(f"School not found with unique_code '{unique_code}', raising 404")
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.get("/{school_id}/classes/", response_model=List[schemas.Class])
def read_school_classes(
    school_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(deps.get_current_active_user),
):
    """
    Get all classes for a specific school.
    Only accessible by users associated with that school or superusers.
    """
    school = crud.school.get(db, id=school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    if not (current_user.role == schemas.UserRole.SUPER_ADMIN) and current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    classes = crud.class_.get_multi_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return classes

@router.post("/{school_id}/classes/", response_model=schemas.Class, status_code=status.HTTP_201_CREATED)
def create_class_for_school(
    school_id: int,
    class_data: schemas.ClassCreate,
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user),
):
    """
    Create a new class for a specific school.
    Only accessible by admin or superusers of the school.
    """
    school = crud.school.get(db, id=school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with id {school_id} not found")

    if not (current_user.role == schemas.UserRole.SUPER_ADMIN) and \
       not (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to create a class in this school")

    if class_data.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"School ID in path ({school_id}) does not match school ID in request body ({class_data.school_id})."
        )
    
    existing_class = crud.class_.get_by_name_and_school_id(db, class_name=class_data.class_name, school_id=school_id)
    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class '{class_data.class_name}' already exists in this school (ID: {school_id})"
        )
    
    try:
        new_class = crud.class_.create(db=db, obj_in=class_data)
        return new_class
    except Exception as e:
        logger.error(f"Error creating class '{class_data.class_name}' for school {school_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create class")

@router.get("/{school_id}", response_model=schemas.School)
def read_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user),
):
    """
    Get a specific school by ID.
    """
    school = crud_school.get_school_by_id(db, school_id=school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.get("/{school_id}/students/", response_model=List[schemas.Student])
def read_school_students(
    school_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(deps.get_current_active_user),
):
    """
    Retrieve students for a specific school.
    Only accessible by users associated with that school or superusers.
    """
    school = crud.school.get(db, id=school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    if not (current_user.role == schemas.UserRole.SUPER_ADMIN) and current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    students = crud.student.get_multi_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return students

@router.get("/{school_id}/teachers/", response_model=List[schemas.Teacher])
def read_school_teachers(
    school_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(deps.get_current_active_user),
):
    """
    Retrieve teachers for a specific school.
    Only accessible by users associated with that school or superusers.
    """
    school = crud.school.get(db, id=school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")

    if not (current_user.role == schemas.UserRole.SUPER_ADMIN) and current_user.school_id != school_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    teachers = crud.teacher.get_multi_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return teachers

@router.post("/{school_id}/students/", response_model=schemas.Student)
def create_school_student(
    school_id: int,
    student_in: schemas.StudentCreate,
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user)
):
    """Create a new student for a specific school."""
    # Yetkilendirme
    is_superuser = current_user.role == schemas.UserRole.SUPER_ADMIN
    is_school_admin_of_target_school = (current_user.role == schemas.UserRole.SCHOOL_ADMIN and 
                                        current_user.school_id == school_id)

    if not (is_superuser or is_school_admin_of_target_school):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to add student to this school."
        )

    if student_in.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"School ID in path ({school_id}) does not match school ID in request body ({student_in.school_id})."
        )
    
    try:
        created_student = crud.student.create(db=db, obj_in=student_in)
        return created_student
    except Exception as e:
        logger.error(f"Error creating student '{student_in.full_name}' for school {school_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create student.")

@router.put("/{school_id}/students/{student_id}", response_model=schemas.Student)
def update_school_student(
    school_id: int,
    student_id: int,
    student: schemas.StudentUpdate,
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user)
):
    """Update a student"""
    db_student = crud.student.get(db, id=student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    if db_student.school_id != school_id:
        raise HTTPException(status_code=400, detail="Student does not belong to this school")
    return crud.student.update(db, db_obj=db_student, obj_in=student)

@router.delete("/{school_id}/students/{student_id}", response_model=schemas.Student)
def delete_school_student(
    school_id: int,
    student_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user)
):
    """Delete a student"""
    db_student = crud.student.get(db, id=student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    if db_student.school_id != school_id:
        raise HTTPException(status_code=400, detail="Student does not belong to this school")
    return crud.student.remove(db, id=student_id) 