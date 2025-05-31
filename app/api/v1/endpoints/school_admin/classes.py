from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.api.deps import get_db, get_current_active_user

router = APIRouter(
    # prefix="/schools/{school_id}/classes", # api_v1.py'de yönetilecek
    tags=["School Administration - Classes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Class, status_code=status.HTTP_201_CREATED)
async def create_class(
    school_id: int, # Path'ten
    class_in: schemas.ClassCreate, # ClassCreate school_id içermeli
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Yeni bir sınıf oluşturur (belirli bir okul için).
    - Yetki: Sadece o okulun SCHOOL_ADMIN'i veya SUPER_ADMIN oluşturabilir.
    - Sınıf adı okul içinde benzersiz olmalıdır.
    - Atanan öğretmen (teacher_id) aynı okulda olmalıdır.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create class in this school")

    db_school = crud.school.get(db, id=school_id)
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")

    # ClassCreate'in school_id içerdiğini ve path'teki ile eşleştiğini kontrol et
    if class_in.school_id != school_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School ID in path and body must match.")

    existing_class = crud.class_.get_by_name_and_school_id(db, class_name=class_in.class_name, school_id=school_id)
    if existing_class:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail=f"Class with name '{class_in.class_name}' already exists in school {school_id}")
    
    if class_in.teacher_id:
        db_teacher = crud.teacher.get_by_id_and_school_id(db, teacher_id=class_in.teacher_id, school_id=school_id)
        if not db_teacher:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Teacher with ID {class_in.teacher_id} not found or not in school {school_id}")
            
    return crud.class_.create(db=db, obj_in=class_in)

@router.get("/{class_id}", response_model=schemas.Class)
async def read_class(
    school_id: int, # Path'ten
    class_id: int, # Path'ten
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki belirli bir sınıfı getirir.
    """
    db_class = crud.class_.get_by_id_and_school_id(db, class_id=class_id, school_id=school_id)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found in this school")

    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.school_id == school_id and 
             (current_user.role == schemas.UserRole.SCHOOL_ADMIN or current_user.role == schemas.UserRole.TEACHER))):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this class")
    return db_class

@router.get("/", response_model=List[schemas.Class])
async def read_classes(
    school_id: int, # Path'ten
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki tüm sınıfları listeler.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.school_id == school_id and 
             (current_user.role == schemas.UserRole.SCHOOL_ADMIN or current_user.role == schemas.UserRole.TEACHER))):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list classes for this school")

    db_school = crud.school.get(db, id=school_id) # Okul var mı kontrolü
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")

    classes = crud.class_.get_multi_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return classes

@router.put("/{class_id}", response_model=schemas.Class)
async def update_class(
    school_id: int, # Path'ten
    class_id: int, # Path'ten
    class_update_in: schemas.ClassUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki bir sınıfın bilgilerini günceller.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update class in this school")

    db_class = crud.class_.get_by_id_and_school_id(db, class_id=class_id, school_id=school_id)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found in this school")

    if class_update_in.class_name and class_update_in.class_name != db_class.class_name:
        existing_class = crud.class_.get_by_name_and_school_id(db, class_name=class_update_in.class_name, school_id=school_id)
        if existing_class and existing_class.id != class_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Class with name '{class_update_in.class_name}' already exists in school {school_id}")

    if class_update_in.teacher_id is not None and class_update_in.teacher_id != db_class.teacher_id:
        # None atanıyorsa (öğretmen kaldırılıyorsa) öğretmen kontrolüne gerek yok.
        if class_update_in.teacher_id is not None:
            db_new_teacher = crud.teacher.get_by_id_and_school_id(db, teacher_id=class_update_in.teacher_id, school_id=school_id)
            if not db_new_teacher:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                    detail=f"New teacher with ID {class_update_in.teacher_id} not found or not in school {school_id}")

    return crud.class_.update(db=db, db_obj=db_class, obj_in=class_update_in)

@router.delete("/{class_id}", response_model=schemas.Class)
async def delete_class(
    school_id: int, # Path'ten
    class_id: int, # Path'ten
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki bir sınıfı siler.
    TODO: Sınıf silinmeden önce içindeki öğrenciler (class_id=None) ve öğretmen ataması ne olmalı?
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete class in this school")

    db_class = crud.class_.get_by_id_and_school_id(db, class_id=class_id, school_id=school_id)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found in this school for deletion")
    
    # TODO: Öğrencilerin class_id'lerini null yap veya öğrencileri başka bir sınıfa taşı?
    # students_in_class = crud.student.get_multi_by_class_id(db, class_id=class_id, school_id=school_id)
    # for student in students_in_class:
    #     crud.student.update(db, db_obj=student, obj_in=schemas.StudentUpdate(class_id=None))

    deleted_class = crud.class_.remove(db=db, id=class_id)
    return deleted_class 