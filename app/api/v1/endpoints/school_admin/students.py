from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.api.deps import get_db, get_current_active_user

router = APIRouter(
    # prefix="/schools/{school_id}/students", # Bu prefix api_v1.py'de yönetilecek
    tags=["School Administration - Students"],
    responses={404: {"description": "Not found"}},
)

# /schools/{school_id}/students/ path'i api_v1.py'de bu router'a verildiği için
# buradaki @router.post("/") direkt /schools/{school_id}/students/ anlamına gelecek.
@router.post("/", response_model=schemas.Student, status_code=status.HTTP_201_CREATED)
async def create_student_for_school(
    school_id: int, # Path parametresi (api_v1.py'deki prefix'ten gelecek)
    student_in: schemas.StudentCreate, # StudentCreate artık school_id içerecek (veya opsiyonel)
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Yeni bir öğrenci oluşturur (belirli bir okul için).
    - Yetki: Sadece o okulun SCHOOL_ADMIN'i veya SUPER_ADMIN oluşturabilir.
    - Öğrenci numarası okul içinde benzersiz olmalıdır.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create student in this school")

    db_school = crud.school.get(db, id=school_id)
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")

    if student_in.class_id:
        db_class = crud.class_.get_by_id_and_school_id(db, class_id=student_in.class_id, school_id=school_id)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Class with ID {student_in.class_id} not found in school {school_id}")

    if student_in.student_number: # StudentCreate'de student_number olmalı
        existing_student = crud.student.get_by_student_number_and_school_id(db, student_number=student_in.student_number, school_id=school_id)
        if existing_student:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Student with number {student_in.student_number} already exists in school {school_id}")

    # StudentCreate şemasının school_id içerdiğini veya burada atandığını varsayıyoruz.
    # Eğer StudentCreate'de school_id yoksa:
    # student_data = student_in.dict()
    # student_data['school_id'] = school_id
    # obj_to_create = schemas.StudentCreate(**student_data)
    # return crud.student.create(db=db, obj_in=obj_to_create)
    # Eğer StudentCreate school_id içeriyorsa ve path'teki school_id ile aynı olmalıysa:
    if student_in.school_id != school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School ID in path and body must match.")

    return crud.student.create(db=db, obj_in=student_in)

@router.get("/{student_id}", response_model=schemas.Student)
async def read_student(
    school_id: int, # Path parametresi (api_v1.py'deki prefix'ten gelecek)
    student_id: int, # Path parametresi
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki belirli bir öğrenciyi getirir.
    - Path: /schools/{school_id}/students/{student_id}
    - Yetki: SUPER_ADMIN, o okulun SCHOOL_ADMIN'i, o öğrencinin atandığı TEACHER, veya o öğrencinin PARENT'ı.
    """
    student = crud.student.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this school")

    can_access = False
    if current_user.role == schemas.UserRole.SUPER_ADMIN:
        can_access = True
    elif current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id:
        can_access = True
    elif current_user.role == schemas.UserRole.TEACHER and current_user.school_id == school_id:
        # TODO: Öğretmenin bu öğrencinin sınıfına atanıp atanmadığını veya dersine girip girmediğini kontrol et
        # (Örnek: if crud.teacher.is_teacher_of_student(db, teacher_id=current_user.id, student_id=student_id): can_access = True)
        # Şimdilik öğretmenin öğrencinin sınıfının öğretmeni olduğunu varsayalım (eğer sınıfı varsa)
        if student.class_id and student.class_obj and student.class_obj.teacher_id == current_user.id:
            can_access = True
    elif current_user.role == schemas.UserRole.PARENT:
        # TODO: crud.parent_student_relation.is_parent_of_student(db, parent_user_id=current_user.id, student_id=student_id)
        # Şimdilik, velinin bu öğrencinin velisi olup olmadığını crud.student üzerinden kontrol edelim (varsayımsal)
        # Bu kontrol crud.parent_student_relation'a taşınmalı
        is_parent = crud.parent_student_relation.is_parent_linked_to_student(
            db, parent_user_id=current_user.id, student_id=student_id
        )
        if is_parent:
            can_access = True
            
    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this student")

    return student

@router.get("/", response_model=List[schemas.Student])
async def read_students_for_school(
    school_id: int, # Path parametresi (api_v1.py'deki prefix'ten gelecek)
    skip: int = 0,
    limit: int = 100,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki tüm öğrencileri listeler. Sınıfa göre filtrelenebilir.
    - Path: /schools/{school_id}/students/
    - Yetki: SUPER_ADMIN, o okulun SCHOOL_ADMIN'i, veya o okulda görevli bir TEACHER.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.school_id == school_id and 
             (current_user.role == schemas.UserRole.SCHOOL_ADMIN or current_user.role == schemas.UserRole.TEACHER))):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list students for this school")

    db_school = crud.school.get(db, id=school_id) # Okul var mı kontrolü
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")
    
    if class_id:
        db_class = crud.class_.get_by_id_and_school_id(db, class_id=class_id, school_id=school_id)
        if not db_class:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with ID {class_id} not found in school {school_id}")

    students = crud.student.get_multi_by_school_and_optional_class(
        db, school_id=school_id, class_id=class_id, skip=skip, limit=limit
    )
    return students

@router.put("/{student_id}", response_model=schemas.Student)
async def update_student(
    school_id: int, # Path parametresi
    student_id: int, # Path parametresi
    student_update_in: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki bir öğrencinin bilgilerini günceller.
    - Path: /schools/{school_id}/students/{student_id}
    - Yetki: Sadece o okulun SCHOOL_ADMIN'i veya SUPER_ADMIN güncelleyebilir.
    - `student_number` güncelleniyorsa, okul içinde benzersizliği kontrol edilir.
    - `class_id` güncelleniyorsa, sınıfın aynı okulda olduğu kontrol edilir.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update student in this school")

    db_student = crud.student.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this school")

    if student_update_in.class_id is not None and student_update_in.class_id != db_student.class_id:
        db_new_class = crud.class_.get_by_id_and_school_id(db, class_id=student_update_in.class_id, school_id=school_id)
        if not db_new_class:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"New class with ID {student_update_in.class_id} not found in school {school_id}")

    if student_update_in.student_number and student_update_in.student_number != db_student.student_number:
        existing_student = crud.student.get_by_student_number_and_school_id(
            db, student_number=student_update_in.student_number, school_id=school_id
        )
        if existing_student and existing_student.id != student_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Student with number {student_update_in.student_number} already exists in school {school_id}")
            
    # StudentUpdate şemasında school_id olmamalı veya değiştirilmemeli.
    # CRUDStudent.update metodu db_obj ve obj_in alacak şekilde güncellenmeli.
    return crud.student.update(db=db, db_obj=db_student, obj_in=student_update_in)

@router.delete("/{student_id}", response_model=schemas.Student)
async def delete_student(
    school_id: int, # Path parametresi
    student_id: int, # Path parametresi
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okuldaki bir öğrenciyi siler.
    - Path: /schools/{school_id}/students/{student_id}
    - Yetki: Sadece o okulun SCHOOL_ADMIN'i veya SUPER_ADMIN silebilir.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete student in this school")

    # Önce öğrencinin varlığını kontrol et ve objeyi al
    db_student = crud.student.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this school for deletion")

    # CRUDStudent.remove metodu id alacak şekilde güncellenmeli.
    # remove_in_school gibi bir metod yerine, get ile alıp remove(id=...) kullanılabilir.
    deleted_student = crud.student.remove(db=db, id=student_id) # remove db_obj değil id alır genellikle
    if not deleted_student: # Bu kontrol genelde remove metodunun dönüşüne bağlı.
        # Eğer remove metodu silinen objeyi dönmüyorsa (örn. sadece id dönerse) bu kısım değişir.
        # Ya da get_by_id_and_school_id ile kontrol edildiği için bu if gereksiz olabilir.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student could not be deleted or was already deleted.")
    return deleted_student # remove metodu silinen objeyi dönerse bu OK.

# --- Öğrenci-Veli İlişkileri --- #

@router.post("/{student_id}/parents/{parent_user_id}", response_model=schemas.Student, tags=["School Administration - Students", "Student-Parent Relations"])
async def add_parent_to_student(
    school_id: int, # Path parametresi (ana prefix'ten)
    student_id: int, # Path parametresi
    parent_user_id: int, # Path parametresi
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Bir öğrenciye bir veli atar (belirli bir okulda).
    - Path: /schools/{school_id}/students/{student_id}/parents/{parent_user_id} (POST)
    - Yetki: SCHOOL_ADMIN veya SUPER_ADMIN.
    - Veli kullanıcısının rolü 'parent' olmalı.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this operation")

    # Öğrencinin okulda var olduğunu kontrol et
    db_student = crud.student.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with ID {student_id} not found in school {school_id}")

    parent_user = crud.user.get(db, id=parent_user_id)
    if not parent_user or parent_user.role != schemas.UserRole.PARENT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {parent_user_id} not found or is not a parent.")
    
    # Veli zaten bu öğrenciye atanmış mı kontrolü (ParentStudentRelation.add_parent_to_student içinde yapılabilir)

    # crud.parent_student_relation.create_relation çağrılabilir
    # Bu metod, student objesini dönmeli veya biz student objesini tekrar çekmeliyiz.
    # Şimdilik add_parent_to_student metodunun güncellenmiş student objesini döndüğünü varsayalım.
    updated_student = crud.parent_student_relation.add_parent_to_student(
        db, student_id=student_id, parent_user_id=parent_user_id, school_id=school_id
    )
    if not updated_student: # add_parent_to_student başarısız olursa (örn: zaten atanmışsa veya hata oluşursa)
        # crud.parent_student_relation.add_parent_to_student daha spesifik hata vermeli
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to add parent to student. Parent might already be assigned or other error.")
    return updated_student

@router.delete("/{student_id}/parents/{parent_user_id}", response_model=schemas.Student, tags=["School Administration - Students", "Student-Parent Relations"])
async def remove_parent_from_student(
    school_id: int, # Path parametresi (ana prefix'ten)
    student_id: int, # Path parametresi
    parent_user_id: int, # Path parametresi
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Bir öğrencinin veli atamasını kaldırır.
    - Path: /schools/{school_id}/students/{student_id}/parents/{parent_user_id} (DELETE)
    - Yetki: SCHOOL_ADMIN veya SUPER_ADMIN.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this operation")

    # Öğrencinin okulda var olduğunu kontrol et
    db_student = crud.student.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with ID {student_id} not found in school {school_id}")

    # Veli var mı kontrolü (opsiyonel, çünkü ilişkiyi silerken velinin varlığı şart değil)
    # parent_user = crud.user.get(db, id=parent_user_id)
    # if not parent_user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parent user with ID {parent_user_id} not found.")

    updated_student = crud.parent_student_relation.remove_parent_from_student(
        db, student_id=student_id, parent_user_id=parent_user_id, school_id=school_id
    )
    if not updated_student: # remove_parent_from_student başarısız olursa (örn: ilişki yoksa)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent-student relation not found or school mismatch.")
    return updated_student

@router.get("/{student_id}/parents", response_model=List[schemas.User], tags=["School Administration - Students", "Student-Parent Relations"])
async def get_parents_of_student(
    school_id: int, # Path parametresi (ana prefix'ten)
    student_id: int, # Path parametresi
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Bir öğrencinin tüm velilerini listeler.
    - Path: /schools/{school_id}/students/{student_id}/parents
    - Yetki: SUPER_ADMIN, o okulun SCHOOL_ADMIN'i, o öğrencinin atandığı TEACHER, veya o öğrencinin PARENT'ı.
    """
    student = crud.student.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this school")

    # Yetkilendirme (read_student ile benzer)
    can_access = False
    if current_user.role == schemas.UserRole.SUPER_ADMIN:
        can_access = True
    elif current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id:
        can_access = True
    elif current_user.role == schemas.UserRole.TEACHER and current_user.school_id == school_id:
        # TODO: Öğretmenin bu öğrencinin sınıfına/dersine erişimi var mı?
        if student.class_id and student.class_obj and student.class_obj.teacher_id == current_user.id:
            can_access = True 
    elif current_user.role == schemas.UserRole.PARENT:
        is_parent = crud.parent_student_relation.is_parent_linked_to_student(
            db, parent_user_id=current_user.id, student_id=student_id
        )
        if is_parent:
            can_access = True
            
    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this student's parents")

    parents = crud.parent_student_relation.get_parents_of_student(db, student_id=student_id)
    return parents

# Bu endpoint /users/me/children altına taşındı.
# @router.get("/by_parent/me", response_model=List[schemas.Student], tags=["Students (Parent View)"])
# async def get_my_children_as_parent(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_active_user) # Bu get_current_parent_user olmalı?
# ):
#     """
#     Giriş yapmış veli kullanıcısının çocuklarını listeler.
#     - Path: /students/by_parent/me (Bu path /school-admin altında olmayacak şekilde ayarlanmalı)
#     - Yetki: Sadece rolü PARENT olan kullanıcılar.
#     """
#     if current_user.role != schemas.UserRole.PARENT:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can access this endpoint.")
#     
#     # crud.student.get_students_by_parent_id gibi bir metod gerekecek.
#     # Bu metod, ParentStudentRelation tablosunu joinleyerek student'ları çekmeli.
#     students = crud.student.get_students_by_parent_user_id(db, parent_user_id=current_user.id)
#     return students 