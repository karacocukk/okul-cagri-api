from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.api.deps import get_db, get_current_active_user

router = APIRouter(
    # prefix="/schools/{school_id}/teachers", # api_v1.py'de yönetilecek
    tags=["School Administration - Teachers"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Teacher, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    school_id: int, # Path'ten (api_v1.py'deki router include)
    teacher_in: schemas.TeacherCreate, # TeacherCreate school_id içermeli
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Yeni bir öğretmen oluşturur (belirli bir okul için).
    - Yetki: Sadece o okulun SCHOOL_ADMIN'i veya SUPER_ADMIN oluşturabilir.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create teacher in this school")

    db_school = crud.school.get(db, id=school_id)
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")

    if teacher_in.user_id: # Eğer TeacherCreate user_id alıyorsa
        # User'ın varlığını ve rolünü kontrol et (opsiyonel, Teacher modeli User'a bağlıysa)
        user_to_be_teacher = crud.user.get(db, id=teacher_in.user_id)
        if not user_to_be_teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {teacher_in.user_id} not found.")
        # İsteğe bağlı: User'ın rolünü teacher olarak güncellemek veya kontrol etmek
        # if user_to_be_teacher.role != schemas.UserRole.TEACHER:
        #     # Belki burada user'ın rolünü güncellemek gerekebilir veya hata verilebilir.
        #     pass 
    
    # TeacherCreate'in school_id içerdiğini ve path'teki ile eşleştiğini kontrol et
    if teacher_in.school_id != school_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School ID in path and body must match.")

    # TODO: email benzersizlik kontrolü: crud.teacher.get_by_email_and_school_id
    # if teacher_in.email:
    #     existing_teacher_by_email = crud.teacher.get_by_email_and_school_id(db, email=teacher_in.email, school_id=school_id)
    #     if existing_teacher_by_email:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
    #                             detail=f"Teacher with email {teacher_in.email} already exists in this school.")

    return crud.teacher.create(db=db, obj_in=teacher_in)

@router.get("/{teacher_id}", response_model=schemas.Teacher)
async def read_teacher(
    school_id: int, # Path'ten
    teacher_id: int, # Path'ten
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki belirli bir öğretmeni getirir.
    """
    teacher = crud.teacher.get_by_id_and_school_id(db, teacher_id=teacher_id, school_id=school_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found in this school")

    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or current_user.school_id == school_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this teacher")
    
    return teacher

@router.get("/", response_model=List[schemas.Teacher])
async def read_teachers(
    school_id: int, # Path'ten
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki tüm öğretmenleri listeler.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.school_id == school_id and 
             (current_user.role == schemas.UserRole.SCHOOL_ADMIN or current_user.role == schemas.UserRole.TEACHER))):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list teachers for this school")

    db_school = crud.school.get(db, id=school_id) # Okul var mı kontrolü
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")

    teachers = crud.teacher.get_multi_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return teachers

@router.put("/{teacher_id}", response_model=schemas.Teacher)
async def update_teacher(
    school_id: int, # Path'ten
    teacher_id: int, # Path'ten
    teacher_update_in: schemas.TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki bir öğretmenin bilgilerini günceller.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update teacher in this school")

    db_teacher = crud.teacher.get_by_id_and_school_id(db, teacher_id=teacher_id, school_id=school_id)
    if not db_teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found in this school")

    # TODO: Email benzersizlik kontrolü güncellenirken
    # if teacher_update_in.email and teacher_update_in.email != db_teacher.user.email: # Teacher modelinde user ilişkisi varsayıldı
    #     existing_teacher_by_email = crud.teacher.get_by_email_and_school_id(db, email=teacher_update_in.email, school_id=school_id)
    #     if existing_teacher_by_email and existing_teacher_by_email.id != teacher_id:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
    #                             detail=f"Teacher with email {teacher_update_in.email} already exists in this school.")
            
    return crud.teacher.update(db=db, db_obj=db_teacher, obj_in=teacher_update_in)

@router.delete("/{teacher_id}", response_model=schemas.Teacher)
async def delete_teacher(
    school_id: int, # Path'ten
    teacher_id: int, # Path'ten
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki bir öğretmeni siler.
    TODO: Öğretmen silinmeden önce atanmış olduğu sınıflar varsa ne yapılmalı?
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete teacher in this school")

    db_teacher = crud.teacher.get_by_id_and_school_id(db, teacher_id=teacher_id, school_id=school_id)
    if not db_teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found in this school for deletion")
    
    # TODO: Sınıflardan öğretmen atamasını kaldır (class.teacher_id = None)
    # classes_taught = crud.class_.get_by_teacher_id(db, teacher_id=teacher_id, school_id=school_id)
    # for class_obj in classes_taught:
    #     crud.class_.update(db, db_obj=class_obj, obj_in=schemas.ClassUpdate(teacher_id=None))

    deleted_teacher = crud.teacher.remove(db=db, id=teacher_id)
    return deleted_teacher 